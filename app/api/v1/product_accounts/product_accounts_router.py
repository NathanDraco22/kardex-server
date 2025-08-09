from fastapi import APIRouter

from repos.v1.products import ProductInDbWithAccounts
from responses.v1 import ListResponse

from .product_accounts_controller import product_accounts_controller

product_accounts_router = APIRouter(tags=["product_accountsV1"])


@product_accounts_router.get("/{branch_id}")
async def get_all_product_accounts(
    current_pos: int,
) -> ListResponse[ProductInDbWithAccounts]:
    return await product_accounts_controller.get_all_product_with_accounts(
        branch_id="1", current_pos=current_pos
    )
