import asyncio


from fastapi import HTTPException, status
from pymongo.errors import OperationFailure


from repos.v1.receipts import CreateReceipt, ReceiptInDb
from repos.v1.receipts import ReceiptsRepository, ReceiptsDataSource
from repos.v1.clients import ClientsRepository, ClientsDataSource, ClientInDb
from repos.v1.branches import BranchesRepository, BranchesDataSource
from core.counter_manager.counter_manager import CounterManager

from .process_receipt import process_receipt


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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="BRANCH_NOT_FOUND"
            )

        client = await self.clients_repo.get_client_by_id(doc.clientId)
        if client is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="CLIENT_NOT_FOUND"
            )
        # Aquí podrías añadir validaciones extra, como verificar que las facturas aplicadas existan.

    async def regis_receipt(
        self, create_receipt: CreateReceipt
    ) -> tuple[ReceiptInDb, ClientInDb]:
        """
        Valida y registra un nuevo recibo de pago.
        """
        # Genera un número de documento si no se proporciona uno.
        if not create_receipt.docNumber:
            create_receipt.docNumber = await CounterManager().next_receipt_number()

        # Comprueba si ya existe un recibo con ese número.
        receipt = await self.receipts_repo.get_receipt_by_doc_number(
            create_receipt.docNumber
        )
        if receipt is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Receipt with this document number already exists",
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
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Database operation failed: {e}",
                    )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"An unexpected error occurred: {e}",
                )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server is too busy, please try again later",
        )
