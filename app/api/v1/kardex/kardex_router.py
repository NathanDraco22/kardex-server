from fastapi import APIRouter


from responses.v1 import ListResponse
from repos.v1.movements import MovementInDb

from .kardex_controller import kardex_controller

kardex_router = APIRouter(tags=["kardexV1"])


@kardex_router.get("/{product_id}")
async def get_product_kardex(
    product_id: str, branch_id: str, start_date: int, end_date: int
) -> ListResponse[MovementInDb]:
    return await kardex_controller.get_product_kardex(
        product_id, branch_id, start_date, end_date
    )
