import asyncio
from fastapi import HTTPException, status
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


from kardex.core.inventory import (
    InsufficientBalanceError,
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
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="DOCUMENT_EXISTS",
                )

        # B. Validar Referencias (Sucursales y Productos)
        await self._validate_outgoing_transfer(create_transfer)

        # C. Ejecutar Proceso con Reintentos (Optimistic Concurrency Control)
        max_retries = 3
        for _ in range(max_retries):
            try:
                result = await process_outgoing_transfer(create_transfer)
                return result

            except InsufficientBalanceError as e:
                # Error de negocio: No hay stock suficiente en Origen
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"INSUFFICIENT_STOCK: {str(e)}",
                )

            except OperationFailure as _:
                # Error 112: WriteConflict (Conflicto concurrente)
                # O error personalizado de bulk_write (desincronización de stock detectada)
                # Reintentamos para obtener un nuevo snapshot del stock
                await asyncio.sleep(0.3)
                continue

            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error processing transfer exit \n" + str(e),
                )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server is too busy, try again later",
        )

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
                # Manejo de conflicto de escritura (MongoDB Concurrent Conflict)
                if isinstance(e, OperationFailure) and e.code == 112:
                    await asyncio.sleep(0.3)
                    continue

                # Error de negocio: Traslado no encontrado o ya procesado
                # Mantener el 400 para errores esperados de flujo
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e),
                )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server is too busy, try again later",
        )

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
                # Ej: "Traslado no encontrado" o "Estado no es inTransit"
                if "no encontrado" in error_msg or "No se puede cancelar" in error_msg:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=error_msg,
                    )

                # B. Conflicto de Escritura en Mongo (Reintentar)
                if isinstance(e, OperationFailure) and e.code == 112:
                    await asyncio.sleep(0.3)
                    continue

                # C. Errores inesperados
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error canceling transfer \n" + error_msg,
                )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server is too busy, try again later",
        )

    # ---------------------------------------------------------
    # VALIDACIONES PRIVADAS
    # ---------------------------------------------------------
    async def _validate_outgoing_transfer(self, doc: CreateTransfer):
        # 1. Validar Sucursal Origen
        branches_tool = BranchesTool()
        origin_branch = branches_tool.get_branch_by_id(doc.origin)
        if origin_branch is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ORIGIN_BRANCH_NOT_FOUND",
            )

        # 2. Validar Sucursal Destino
        destination_branch = branches_tool.get_branch_by_id(doc.destination)
        if destination_branch is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="DESTINATION_BRANCH_NOT_FOUND",
            )

        # 3. Validar que Origen y Destino no sean la misma
        if doc.origin == doc.destination:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ORIGIN_AND_DESTINATION_ARE_SAME",
            )
