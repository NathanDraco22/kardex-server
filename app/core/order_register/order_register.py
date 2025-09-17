import asyncio
from fastapi import HTTPException, status
from pymongo.errors import OperationFailure
from typing import List, Tuple


from repos.v1.orders import (
    CreateOrder,
    OrderInDb,
    OrdersRepository,
    OrdersDataSource,
)
from repos.v1.product_accounts import ProductAccountInDb
from repos.v1.branches import BranchesRepository, BranchesDataSource
from repos.v1.products import ProductsRepository, ProductsDataSource
from core.counter_manager.counter_manager import CounterManager

from .process_order import process_order, InsufficientBalanceError


class OrderRegister:
    def __init__(self) -> None:
        self.orders_repo = OrdersRepository(OrdersDataSource())
        self.branches_repo = BranchesRepository(BranchesDataSource())
        self.products_repo = ProductsRepository(ProductsDataSource())

    async def _validate_document(self, doc: CreateOrder):
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

    async def regis_order(
        self, create_order: CreateOrder
    ) -> Tuple[OrderInDb, List[ProductAccountInDb]]:
        if not create_order.docNumber:
            create_order.docNumber = await CounterManager().next_order_number()

        order = await self.orders_repo.get_order_by_doc_number(create_order.docNumber)
        if order is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Order with this document number already exists",
            )

        await self._validate_document(create_order)

        max_retries = 3
        for _ in range(max_retries):
            try:
                return await process_order(create_order)

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
