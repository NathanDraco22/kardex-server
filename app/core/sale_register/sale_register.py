import asyncio
from fastapi import HTTPException, status
from pymongo.errors import OperationFailure

from repos.v1.sales import CreateSale, SaleInDb, SalesRepository, SalesDataSource
from repos.v1.product_accounts import ProductAccountInDb
from repos.v1.branches import BranchesRepository, BranchesDataSource
from repos.v1.products import ProductsRepository, ProductsDataSource

from .process_sale import process_sale, InsufficientBalanceError


class SaleRegister:
    def __init__(self) -> None:
        """Inicializa los repositorios necesarios."""
        self.sales_repo = SalesRepository(SalesDataSource())
        self.branches_repo = BranchesRepository(BranchesDataSource())
        self.products_repo = ProductsRepository(ProductsDataSource())

    async def _validate_document(self, doc: CreateSale):
        branch = await self.branches_repo.get_branch_by_id(doc.branchId)
        if branch is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="BRANCH_NOT_FOUND"
            )

        product_ids = list(set(item.product.id for item in doc.saleItems))
        products = await self.products_repo.get_product_by_ids(product_ids)
        if len(products) != len(product_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="PRODUCT_NOT_FOUND"
            )

    async def regis_sale(
        self, create_sale: CreateSale
    ) -> tuple[SaleInDb, list[ProductAccountInDb]]:
        await self._validate_document(create_sale)

        max_retries = 3
        for _ in range(max_retries):
            try:
                return await process_sale(create_sale)

            except InsufficientBalanceError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"INSUFFICIENT_STOCK: {e}",
                )

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
