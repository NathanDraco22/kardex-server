from .data.product_prices_datasource import ProductPricesDataSource
from .models.product_price_model import (
    CreateProductPrice,
    UpdateProductPrice,
    ProductPriceInDb,
)

from tools import TimeTools, UuidTool


class ProductPricesRepository:
    def __init__(self, product_prices_ds: ProductPricesDataSource):
        self.product_prices_ds = product_prices_ds

    async def create_product_price(
        self, create_product_price: CreateProductPrice
    ) -> ProductPriceInDb:
        new_product_price = ProductPriceInDb(
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_utc(),
            **create_product_price.model_dump(),
        )

        result = await self.product_prices_ds.create_product_price(
            new_product_price.model_dump()
        )

        return ProductPriceInDb.model_validate(result)

    async def get_all_product_prices(self) -> list[ProductPriceInDb]:
        results = await self.product_prices_ds.get_all_product_prices()
        models = [ProductPriceInDb.model_validate(result) for result in results]
        return models

    async def get_product_price_by_id(
        self, product_price_id: str
    ) -> ProductPriceInDb | None:
        result = await self.product_prices_ds.get_product_price_by_id(product_price_id)

        if result is None:
            return None

        return ProductPriceInDb.model_validate(result)

    async def update_product_price_by_id(
        self, product_price_id: str, product_price: UpdateProductPrice
    ) -> ProductPriceInDb | None:
        updated_product_price_data = product_price.model_dump(exclude_unset=True)

        updated_product_price_data["updatedAt"] = TimeTools.get_now_utc()

        result = await self.product_prices_ds.update_product_price_by_id(
            product_price_id, updated_product_price_data
        )

        if result is None:
            return None

        return ProductPriceInDb.model_validate(result)

    async def delete_product_price_by_id(
        self, product_price_id: str
    ) -> ProductPriceInDb | None:
        result = await self.product_prices_ds.delete_product_price_by_id(
            product_price_id
        )

        if result is None:
            return None

        return ProductPriceInDb.model_validate(result)
