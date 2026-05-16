import asyncio
from fastapi import HTTPException, status
from pymongo.errors import OperationFailure


from kardex.repos.v1.adjust_entries import (
    AdjustEntriesRepository,
    AdjustEntriesDataSource,
    CreateAdjustEntry,
    AdjustEntryInDb,
)

from kardex.repos.v1.adjust_exits import (
    AdjustExitsRepository,
    AdjustExitsDataSource,
    CreateAdjustExit,
    AdjustExitInDb,
)


from kardex.repos.v1.branches import BranchesRepository, BranchesDataSource
from kardex.repos.v1.product_accounts import (
    ProductAccountsRepository,
    ProductAccountInDb,
    ProductAccountsDataSource,
)
from kardex.repos.v1.products import ProductsRepository, ProductsDataSource

from kardex.tools import BranchesTool
from kardex.core.inventory import InsufficientBalanceError

from .process_adjust_entry import process_adjust_entry
from .process_adjust_exit import process_adjust_exit


adjust_mutex = asyncio.Lock()


class AdjustLedgerManager:
    def __init__(self) -> None:
        self.adjust_entries_repo = AdjustEntriesRepository(
            adjust_entries_ds=AdjustEntriesDataSource()
        )
        self.adjust_exits_repo = AdjustExitsRepository(
            adjust_exits_ds=AdjustExitsDataSource()
        )

        self.branches_repo = BranchesRepository(
            branches_ds=BranchesDataSource(),
        )
        self.product_accounts_repo = ProductAccountsRepository(
            product_accounts_ds=ProductAccountsDataSource(),
        )
        self.products_repo = ProductsRepository(
            products_ds=ProductsDataSource(),
        )

    # ---------------------------------------------------------
    # 1. REGISTRAR AJUSTE DE ENTRADA (SOBRANTE / HALLAZGO)
    # ---------------------------------------------------------
    async def regis_adjust_entry(
        self, create_adjust_doc: CreateAdjustEntry
    ) -> tuple[AdjustEntryInDb, list[ProductAccountInDb]]:
        existing_doc = await self.adjust_entries_repo.get_adjust_entry_by_doc_number(
            doc_number=create_adjust_doc.docNumber,
            branch_id=create_adjust_doc.branchId,
        )

        if existing_doc is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="DOCUMENT_EXISTS",
            )

        # B. Validar Referencias
        await self._validate_document(create_adjust_doc)

        loocked = False
        await asyncio.wait_for(adjust_mutex.acquire(), timeout=7)
        loocked = True
        try:
            max_retries = 3
            for _ in range(max_retries):
                try:
                    result = await process_adjust_entry(create_adjust_doc)
                    return result

                except OperationFailure as e:
                    # 112: Write Conflict (Reintentar)
                    if e.code == 112:
                        await asyncio.sleep(0.3)
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error processing adjustment entry \n" + str(e),
                        )

                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error processing adjustment entry \n" + str(e),
                    )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server is too busy, try again later",
            )
        finally:
            if loocked:
                adjust_mutex.release()

    # ---------------------------------------------------------
    # 2. REGISTRAR AJUSTE DE SALIDA (MERMA / PÉRDIDA)
    # ---------------------------------------------------------
    async def regis_adjust_exit(
        self, create_adjust_doc: CreateAdjustExit
    ) -> tuple[AdjustExitInDb, list[ProductAccountInDb]]:
        existing_doc = await self.adjust_exits_repo.get_adjust_exit_by_doc_number(
            doc_number=create_adjust_doc.docNumber, branch_id=create_adjust_doc.branchId
        )

        if existing_doc is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="DOCUMENT_EXISTS",
            )

        # B. Validar Referencias
        await self._validate_document(create_adjust_doc)

        loocked = False
        await asyncio.wait_for(adjust_mutex.acquire(), timeout=7)
        loocked = True
        try:
            # C. Ejecutar con Reintentos
            max_retries = 3
            for _ in range(max_retries):
                try:
                    result = await process_adjust_exit(create_adjust_doc)
                    return result

                # D. Manejo de Stock Insuficiente (Vital en salidas)
                except InsufficientBalanceError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="INSUFFICIENT_STOCK_FOR_ADJUSTMENT",
                    )

                except OperationFailure as e:
                    if e.code == 112:
                        await asyncio.sleep(0.3)
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error processing adjustment exit \n" + str(e),
                        )

                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error processing adjustment exit \n" + str(e),
                    )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server is too busy, try again later",
            )
        finally:
            if loocked:
                adjust_mutex.release()

    # ---------------------------------------------------------
    # VALIDACIONES COMUNES
    # ---------------------------------------------------------
    async def _validate_document(self, doc):
        # 1. Validar Sucursal
        branch = BranchesTool().get_branch_by_id(doc.branchId)
        if branch is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="BRANCH_NOT_FOUND"
            )

        # 2. Validar que los productos existan en el catálogo global
        # Nota: Asumo que tus items tienen 'productId'
        product_ids = list(set(item.productId for item in doc.items))
        products = await self.products_repo.get_product_by_ids(product_ids)

        if len(products) != len(product_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="PRODUCT_NOT_FOUND"
            )
