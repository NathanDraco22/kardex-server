from fastapi import APIRouter

from repos.v1.product_accounts import ProductAccountInDb, UpdateProductAccount, AddToProductAccount, SubstractToProductAccount
from responses.v1 import ListResponse

from .product_accounts_controller import product_accounts_controller

product_accounts_router = APIRouter(tags=["product_accountsV1"])


@product_accounts_router.get("/products/{product_id}/accounts")
async def get_product_accounts_by_product(
    product_id: str,
) -> ListResponse[ProductAccountInDb]:
    return await product_accounts_controller.get_product_accounts_by_product(product_id)

@product_accounts_router.patch("/products/{product_id}/branches/{branch_id}")
async def update_product_account(
    product_id: str,
    branch_id: str,
    body: UpdateProductAccount,
) -> ProductAccountInDb:
    return await product_accounts_controller.update_product_account(product_id, branch_id, body)

@product_accounts_router.patch("/products/{product_id}/branches/{branch_id}/add")
async def add_product_account(
    product_id: str,
    branch_id: str,
    body: AddToProductAccount,
) -> ProductAccountInDb:
    return await product_accounts_controller.add_product_account(product_id, branch_id, body)

@product_accounts_router.patch("/products/{product_id}/branches/{branch_id}/substract")
async def substract_product_account(
    product_id: str,
    branch_id: str,
    body: SubstractToProductAccount,
) -> ProductAccountInDb:
    return await product_accounts_controller.substract_product_account(product_id, branch_id, body)
