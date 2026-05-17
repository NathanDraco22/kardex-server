import asyncio
from pymongo.errors import OperationFailure
from typing import List, Tuple


from kardex.repos.v1.orders import (
    CreateOrder,
    OrderInDb,
    OrdersRepository,
    OrdersDataSource,
)
from kardex.repos.v1.product_accounts import ProductAccountInDb
from kardex.repos.v1.branches import BranchesRepository, BranchesDataSource
from kardex.repos.v1.products import ProductsRepository, ProductsDataSource
from kardex.core.counter_manager.counter_manager import CounterManager

from .process_order import process_order
from kardex.tools import InsufficientBalanceError, BranchesTool, BranchNotFound, DocumentAlreadyExists, InvalidOperation


class OrderRegister:
    def __init__(self) -> None:
        self.orders_repo = OrdersRepository(OrdersDataSource())
        self.branches_repo = BranchesRepository(BranchesDataSource())
        self.products_repo = ProductsRepository(ProductsDataSource())

    async def validate_document(self, doc: CreateOrder):
        branch = BranchesTool().get_branch_by_id(doc.branchId)
        if branch is None:
            raise BranchNotFound("BRANCH_NOT_FOUND", branch_id=doc.branchId)

    async def regis_order(
        self, create_order: CreateOrder
    ) -> Tuple[OrderInDb, List[ProductAccountInDb]]:
        if not create_order.docNumber:
            create_order.docNumber = await CounterManager().next_order_number()

        order = await self.orders_repo.get_order_by_doc_number(create_order.docNumber)
        if order is not None:
            raise DocumentAlreadyExists("Order with this document number already exists")

        await self.validate_document(create_order)

        max_retries = 3
        for _ in range(max_retries):
            try:
                return await process_order(create_order)

            except InsufficientBalanceError:
                raise InsufficientBalanceError("INSUFFICIENT_STOCK")

            except OperationFailure as e:
                if e.code == 112:  # WriteConflict
                    await asyncio.sleep(0.3)
                else:
                    raise InvalidOperation(f"Database operation failed: {e}")

            except Exception as e:
                raise InvalidOperation(f"An unexpected error occurred: {e}")

        raise InvalidOperation("Server is too busy, please try again later")
