import asyncio
from pymongo.errors import OperationFailure


from kardex.tools import BranchesTool

from kardex.repos.v1.transfers import (
    TransfersRepository,
    TransfersDataSource,
    CreateTransfer,
    TransferInDb,
    ReceiveTransferIntent,
    CancelTransferIntent,
)
from kardex.repos.v1.branches import BranchesRepository, BranchesDataSource
from kardex.repos.v1.product_accounts import (
    ProductAccountsRepository,
    ProductAccountsDataSource,
)
from kardex.repos.v1.products import ProductsRepository, ProductsDataSource


from kardex.tools import (
    InsufficientBalanceError,
    DocumentAlreadyExists,
    BranchNotFound,
    SameBranchTransferError,
    InvalidOperation,
)

from .process_out_transfer import (
    process_outgoing_transfer,
)
from .process_incoming_transfer import process_incoming_transfer
from .process_cancel_transfer import process_cancel_transfer


class TransferManager:
    def __init__(self) -> None:
        self.transfers_repo = TransfersRepository(transfers_ds=TransfersDataSource())
        self.branches_repo = BranchesRepository(branches_ds=BranchesDataSource())
        self.product_accounts_repo = ProductAccountsRepository(
            product_accounts_ds=ProductAccountsDataSource()
        )
        self.products_repo = ProductsRepository(products_ds=ProductsDataSource())

    # ---------------------------------------------------------
    # 1. REGISTRAR SALIDA (CREAR TRASLADO)
    # ---------------------------------------------------------
    async def regis_outgoing_transfer(
        self, create_transfer: CreateTransfer
    ) -> TransferInDb:
        # A. Validar Duplicidad (Opcional, si usas docNumber único)
        if create_transfer.docNumber:
            existing_transfer = await self.transfers_repo.get_transfer_by_doc_number(
                create_transfer.docNumber
            )
            if existing_transfer:
                raise DocumentAlreadyExists("DOCUMENT_EXISTS")

        # B. Validar Referencias (Sucursales y Productos)
        await self._validate_outgoing_transfer(create_transfer)

        # C. Ejecutar Proceso con Reintentos (Optimistic Concurrency Control)
        max_retries = 3
        for _ in range(max_retries):
            try:
                result = await process_outgoing_transfer(create_transfer)
                return result

            except InsufficientBalanceError:
                raise InsufficientBalanceError("INSUFFICIENT_STOCK")

            except OperationFailure as _:
                await asyncio.sleep(0.3)
                continue

            except Exception as e:
                raise InvalidOperation("Error processing transfer exit \n" + str(e))

        raise InvalidOperation("Server is too busy, try again later")

    # ---------------------------------------------------------
    # 2. REGISTRAR ENTRADA (RECIBIR TRASLADO)
    # ---------------------------------------------------------
    async def regis_incoming_transfer(
        self, transfer_id: str, intent: ReceiveTransferIntent
    ) -> TransferInDb:
        # A. Validaciones básicas previas
        # (Nota: process_incoming_transfer valida si ya existe el ID o si ya fue recibido)

        max_retries = 3
        for _ in range(max_retries):
            try:
                result = await process_incoming_transfer(transfer_id, intent)
                return result

            except Exception as e:
                if isinstance(e, OperationFailure) and e.code == 112:
                    await asyncio.sleep(0.3)
                    continue

                raise InvalidOperation(str(e))

        raise InvalidOperation("Server is too busy, try again later")

    # ---------------------------------------------------------
    # 3. CANCELAR TRASLADO (REVERTIR A ORIGEN)
    # ---------------------------------------------------------
    async def cancel_transfer(
        self, transfer_id: str, intent: CancelTransferIntent
    ) -> TransferInDb:
        max_retries = 3
        for _ in range(max_retries):
            try:
                # Llamamos al proceso atómico que creamos
                result = await process_cancel_transfer(transfer_id, intent)
                return result

            except Exception as e:
                error_msg = str(e)

                # A. Errores de Negocio (Validaciones del proceso)
                if "no encontrado" in error_msg or "No se puede cancelar" in error_msg:
                    raise InvalidOperation(error_msg)

                # B. Conflicto de Escritura en Mongo (Reintentar)
                if isinstance(e, OperationFailure) and e.code == 112:
                    await asyncio.sleep(0.3)
                    continue

                # C. Errores inesperados
                raise InvalidOperation("Error canceling transfer \n" + error_msg)

        raise InvalidOperation("Server is too busy, try again later")

    # ---------------------------------------------------------
    # VALIDACIONES PRIVADAS
    # ---------------------------------------------------------
    async def _validate_outgoing_transfer(self, doc: CreateTransfer):
        # 1. Validar Sucursal Origen
        branches_tool = BranchesTool()
        origin_branch = branches_tool.get_branch_by_id(doc.origin)
        if origin_branch is None:
            raise BranchNotFound("ORIGIN_BRANCH_NOT_FOUND", branch_id=doc.origin)

        # 2. Validar Sucursal Destino
        destination_branch = branches_tool.get_branch_by_id(doc.destination)
        if destination_branch is None:
            raise BranchNotFound(
                "DESTINATION_BRANCH_NOT_FOUND", branch_id=doc.destination
            )

        # 3. Validar que Origen y Destino no sean la misma
        if doc.origin == doc.destination:
            raise SameBranchTransferError("ORIGIN_AND_DESTINATION_ARE_SAME")
