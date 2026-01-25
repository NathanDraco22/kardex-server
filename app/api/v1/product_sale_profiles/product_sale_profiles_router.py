from fastapi import APIRouter

from repos.v1.product_sale_profiles import (
    UpdateProductSaleProfile,
    ProductSaleProfileInDb,
    ProductSaleProfileInDbWithProduct,
)

from responses.v1 import ListResponse

from .product_sale_profiles_controller import product_sale_profiles_controller


sale_prof_router = APIRouter(tags=["product_sale_profilesV1"])


@sale_prof_router.get("/{branch_id}")
async def get_all_product_sale_profiles(
    branch_id: str,
) -> ListResponse[ProductSaleProfileInDbWithProduct]:
    return await product_sale_profiles_controller.get_all_product_sale_profiles(
        branch_id
    )


@sale_prof_router.patch("/{branch_id}/{product_id}")
async def update_product_sale_profile_by_id(
    branch_id: str, product_id: str, body: UpdateProductSaleProfile
) -> ProductSaleProfileInDb:
    return await product_sale_profiles_controller.update_product_sale_profile_by_id(
        branch_id,
        product_id,
        body,
    )
