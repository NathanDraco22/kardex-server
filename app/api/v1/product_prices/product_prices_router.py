from fastapi import APIRouter
from kardex.repos.v1.product_prices import (
    CreateProductPrice,
    UpdateProductPrice,
    ProductPriceInDb,
)

from responses.v1 import ListResponse

from .product_prices_controller import product_prices_controller


product_prices_router = APIRouter(tags=["product_pricesV1"])


@product_prices_router.post("")
async def create_product_price(body: CreateProductPrice) -> ProductPriceInDb:
    return await product_prices_controller.create_product_price(body)


@product_prices_router.get("")
async def get_all_product_prices() -> ListResponse[ProductPriceInDb]:
    return await product_prices_controller.get_all_product_prices()


@product_prices_router.get("/{product_price_id}")
async def get_product_price_by_id(product_price_id: str) -> ProductPriceInDb:
    return await product_prices_controller.get_product_price_by_id(product_price_id)


@product_prices_router.patch("/{product_price_id}")
async def update_product_price_by_id(
    product_price_id: str, body: UpdateProductPrice
) -> ProductPriceInDb:
    return await product_prices_controller.update_product_price_by_id(
        product_price_id, body
    )
