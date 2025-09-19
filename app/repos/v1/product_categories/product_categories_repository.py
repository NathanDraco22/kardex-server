from tools import TimeTools, UuidTool

from .data.product_categories_datasource import ProductCategoriesDataSource
from .models.product_category_model import (
    CreateProductCategory,
    UpdateProductCategory,
    ProductCategoryInDb,
)


class ProductCategoriesRepository:
    def __init__(self, product_categories_ds: ProductCategoriesDataSource):
        self.product_categories_ds = product_categories_ds

    async def create_product_category(
        self, create_product_category: CreateProductCategory
    ) -> ProductCategoryInDb:
        new_product_category = ProductCategoryInDb(
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
            **create_product_category.model_dump(),
        )

        result = await self.product_categories_ds.create_product_category(
            new_product_category.model_dump()
        )

        return ProductCategoryInDb.model_validate(result)

    async def get_all_product_categories(self) -> list[ProductCategoryInDb]:
        results = await self.product_categories_ds.get_all_product_categories()
        models = [ProductCategoryInDb.model_validate(result) for result in results]
        return models

    async def get_product_category_by_id(
        self, product_category_id: str
    ) -> ProductCategoryInDb | None:
        result = await self.product_categories_ds.get_product_category_by_id(
            product_category_id
        )

        if result is None:
            return None

        return ProductCategoryInDb.model_validate(result)

    async def update_product_category_by_id(
        self, product_category_id: str, product_category: UpdateProductCategory
    ) -> ProductCategoryInDb | None:
        updated_product_category_data = product_category.model_dump(exclude_unset=True)

        result = await self.product_categories_ds.update_product_category_by_id(
            product_category_id, updated_product_category_data
        )

        if result is None:
            return None

        return ProductCategoryInDb.model_validate(result)

    async def delete_product_category_by_id(
        self, product_category_id: str
    ) -> ProductCategoryInDb | None:
        result = await self.product_categories_ds.delete_product_category_by_id(
            product_category_id
        )

        if result is None:
            return None

        return ProductCategoryInDb.model_validate(result)
