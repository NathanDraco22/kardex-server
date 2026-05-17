from fastapi import HTTPException, status

from kardex.repos.v1.product_categories import (
    CreateProductCategory,
    UpdateProductCategory,
    ProductCategoryInDb,
    ProductCategoriesRepository,
    ProductCategoriesDataSource,
)

from responses.v1 import ListResponse


class ProductCategoriesController:
    def __init__(self, product_categories_repo: ProductCategoriesRepository) -> None:
        self.product_categories_repo = product_categories_repo

    async def create_product_category(
        self, body: CreateProductCategory
    ) -> ProductCategoryInDb:
        return await self.product_categories_repo.create_product_category(body)

    async def get_all_product_categories(self) -> ListResponse[ProductCategoryInDb]:
        product_categories = (
            await self.product_categories_repo.get_all_product_categories()
        )
        return ListResponse(
            count=len(product_categories),
            data=product_categories,
        )

    async def get_product_category_by_id(
        self, product_category_id: str
    ) -> ProductCategoryInDb:
        product_category = (
            await self.product_categories_repo.get_product_category_by_id(
                product_category_id
            )
        )
        if product_category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ProductCategory not found",
            )
        return product_category

    async def update_product_category_by_id(
        self, product_category_id: str, body: UpdateProductCategory
    ) -> ProductCategoryInDb:
        updated_product_category = (
            await self.product_categories_repo.update_product_category_by_id(
                product_category_id, body
            )
        )
        if updated_product_category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ProductCategory not found",
            )
        return updated_product_category


product_categories_controller = ProductCategoriesController(
    product_categories_repo=ProductCategoriesRepository(
        product_categories_ds=ProductCategoriesDataSource(),
    ),
)
