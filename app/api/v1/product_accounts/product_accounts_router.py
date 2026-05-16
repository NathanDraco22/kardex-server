from fastapi import APIRouter
from kardex.repos.v1.product_accounts import ProductAccountInDb
from responses.v1 import ListResponse

from .product_accounts_controller import product_accounts_controller

product_accounts_router = APIRouter(tags=["product_accountsV1"])


@product_accounts_router.get("/products/{product_id}/accounts")
async def get_product_accounts_by_product(
    product_id: str,
) -> ListResponse[ProductAccountInDb]:
    return await product_accounts_controller.get_product_accounts_by_product(product_id)
