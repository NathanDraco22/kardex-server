import asyncio


from pymongo.errors import OperationFailure


from kardex.repos.v1.receipts import CreateReceipt, ReceiptInDb
from kardex.repos.v1.receipts import ReceiptsRepository, ReceiptsDataSource
from kardex.repos.v1.clients import ClientsRepository, ClientsDataSource, ClientInDb
from kardex.repos.v1.branches import BranchesRepository, BranchesDataSource
from kardex.tools import (
    BranchNotFound,
    ClientNotFound,
    DocumentAlreadyExists,
    InvalidOperation,
    ReceiptNotFound,
    ReceiptAlreadyDeleted,
)

from .process_receipt import process_receipt
from .reverse_receipt import reverse_receipt


class ReceiptRegister:
    def __init__(self) -> None:
        """Inicializa los repositorios necesarios."""
        self.receipts_repo = ReceiptsRepository(ReceiptsDataSource())
        self.branches_repo = BranchesRepository(BranchesDataSource())
        self.clients_repo = ClientsRepository(
            ClientsDataSource()
        )  # Necesario para validación

    async def _validate_document(self, doc: CreateReceipt):
        """
        Método privado para validar la existencia de la sucursal y el cliente.
        """
        branch = await self.branches_repo.get_branch_by_id(doc.branchId)
        if branch is None:
            raise BranchNotFound("BRANCH_NOT_FOUND", branch_id=doc.branchId)

        client = await self.clients_repo.get_client_by_id(doc.clientId)
        if client is None:
            raise ClientNotFound("CLIENT_NOT_FOUND", client_id=doc.clientId)
        # Aquí podrías añadir validaciones extra, como verificar que las facturas aplicadas existan.

    async def regis_receipt(
        self, create_receipt: CreateReceipt
    ) -> tuple[ReceiptInDb, ClientInDb]:
        """
        Valida y registra un nuevo recibo de pago.
        """

        # Comprueba si ya existe un recibo con ese número.
        receipt = await self.receipts_repo.get_receipt_by_doc_number(
            create_receipt.docNumber
        )
        if receipt is not None:
            raise DocumentAlreadyExists(
                "Receipt with this document number already exists"
            )

        # Realiza las validaciones de datos relacionados.
        await self._validate_document(create_receipt)

        # Inicia el proceso transaccional con lógica de reintentos.
        max_retries = 3
        for _ in range(max_retries):
            try:
                return await process_receipt(create_receipt)
            except OperationFailure as e:
                if e.code == 112:  # WriteConflict
                    await asyncio.sleep(0.3)
                else:
                    raise InvalidOperation(f"Database operation failed: {e}")
            except Exception as e:
                raise InvalidOperation(f"An unexpected error occurred: {e}")

        raise InvalidOperation("Server is too busy, please try again later")

    async def delete_receipt(self, receipt_id: str) -> tuple[ReceiptInDb, ClientInDb]:
        """
        Elimina un recibo revertiendo las transacciones asociadas.
        """
        receipt = await self.receipts_repo.get_receipt_by_id(receipt_id)
        if receipt is None:
            raise ReceiptNotFound("Receipt not found", receipt_id=receipt_id)

        if receipt.isDeleted:
            raise ReceiptAlreadyDeleted("Receipt already deleted")

        max_retries = 3
        for _ in range(max_retries):
            try:
                return await reverse_receipt(receipt)
            except OperationFailure as e:
                if e.code == 112:
                    await asyncio.sleep(0.3)
                else:
                    raise InvalidOperation(f"Database operation failed: {e}")
            except Exception as e:
                raise InvalidOperation(f"An unexpected error occurred: {e}")

        raise InvalidOperation("Server is too busy, please try again later")
