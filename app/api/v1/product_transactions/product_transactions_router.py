from fastapi import APIRouter, Depends
from responses.v1 import ListResponse
from repos.v1.product_transactions import ProductTransactionInDb


from .product_transactions_controller import product_transactions_controller
from .transaction_query_params import TransactionQueryParams

product_transactions_router = APIRouter(tags=["product_transactionsV1"])


@product_transactions_router.get("")
async def get_all_product_transactions(
    query_params: TransactionQueryParams = Depends(),
) -> ListResponse[ProductTransactionInDb]:
    return await product_transactions_controller.get_all_product_transactions(
        query_params
    )
