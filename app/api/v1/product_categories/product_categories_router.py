from fastapi import APIRouter

from kardex.repos.v1.product_categories import (
    CreateProductCategory,
    UpdateProductCategory,
    ProductCategoryInDb,
)

from responses.v1 import ListResponse

from .product_categories_controller import product_categories_controller


product_categories_router = APIRouter(tags=["product_categoriesV1"])


@product_categories_router.post("")
async def create_product_category(body: CreateProductCategory) -> ProductCategoryInDb:
    return await product_categories_controller.create_product_category(body)


@product_categories_router.get("")
async def get_all_product_categories() -> ListResponse[ProductCategoryInDb]:
    return await product_categories_controller.get_all_product_categories()


@product_categories_router.get("/{product_category_id}")
async def get_product_category_by_id(product_category_id: str) -> ProductCategoryInDb:
    return await product_categories_controller.get_product_category_by_id(
        product_category_id
    )


@product_categories_router.patch("/{product_category_id}")
async def update_product_category_by_id(
    product_category_id: str, body: UpdateProductCategory
) -> ProductCategoryInDb:
    return await product_categories_controller.update_product_category_by_id(
        product_category_id, body
    )
