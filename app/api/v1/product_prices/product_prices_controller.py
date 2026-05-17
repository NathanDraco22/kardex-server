from fastapi import HTTPException, status

from kardex.repos.v1.product_prices import (
    CreateProductPrice,
    UpdateProductPrice,
    ProductPriceInDb,
    ProductPricesRepository,
    ProductPricesDataSource,
)

from responses.v1 import ListResponse


class ProductPricesController:
    def __init__(self, product_prices_repo: ProductPricesRepository) -> None:
        self.product_prices_repo = product_prices_repo

    async def create_product_price(self, body: CreateProductPrice) -> ProductPriceInDb:
        return await self.product_prices_repo.create_product_price(body)

    async def get_all_product_prices(self) -> ListResponse[ProductPriceInDb]:
        product_prices = await self.product_prices_repo.get_all_product_prices()
        return ListResponse(
            data=product_prices,
            count=len(product_prices),
        )

    async def get_product_price_by_id(self, product_price_id: str) -> ProductPriceInDb:
        product_price = await self.product_prices_repo.get_product_price_by_id(
            product_price_id
        )
        if product_price is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ProductPrice not found",
            )
        return product_price

    async def update_product_price_by_id(
        self, product_price_id: str, body: UpdateProductPrice
    ) -> ProductPriceInDb:
        updated_product_price = (
            await self.product_prices_repo.update_product_price_by_id(
                product_price_id, body
            )
        )
        if updated_product_price is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ProductPrice not found",
            )
        return updated_product_price


product_prices_controller = ProductPricesController(
    product_prices_repo=ProductPricesRepository(
        product_prices_ds=ProductPricesDataSource(),
    ),
)
