from fastapi import APIRouter, Depends
from responses.v1 import ListResponse
from kardex.repos.v1.product_transactions import ProductTransactionInDb


from .product_transactions_controller import product_transactions_controller
from kardex.repos.v1.common.filter_params import ProductTransactionFilterParams
from app_middleware import auth_middleware

prod_tx_router = APIRouter(
    tags=["product_transactionsV1"],
    dependencies=[Depends(auth_middleware)],
)


@prod_tx_router.get("")
async def get_all_product_transactions(
    query_params: ProductTransactionFilterParams = Depends(),
) -> ListResponse[ProductTransactionInDb]:
    return await product_transactions_controller.get_all_product_transactions(
        query_params
    )
