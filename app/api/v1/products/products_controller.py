from fastapi import HTTPException, status

from responses.v1 import ListResponse

from repos.v1.products import (
    CreateProduct,
    UpdateProduct,
    ProductInDb,
    ProductInDbInBranch,
    ProductsRepository,
    ProductsDataSource,
)


class ProductsController:
    def __init__(self, products_repo: ProductsRepository) -> None:
        self.products_repo = products_repo

    async def create_product(self, body: CreateProduct) -> ProductInDb:
        return await self.products_repo.create_product(body)

    async def get_all_products(self) -> ListResponse[ProductInDb]:
        products = await self.products_repo.get_all_products()
        return ListResponse(
            data=products,
            count=len(products),
        )

    async def get_paginated_products(
        self, offset: int, limit: int
    ) -> ListResponse[ProductInDb]:
        products = await self.products_repo.get_paginated_products(offset, limit)
        return ListResponse(
            data=products,
            count=len(products),
        )

    async def get_product_by_id(self, product_id: str) -> ProductInDb:
        product = await self.products_repo.get_product_by_id(product_id)
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        return product

    async def search_product_by_text(
        self, text_query: str
    ) -> ListResponse[ProductInDb]:
        products = await self.products_repo.search_product_by_text(text_query)
        return ListResponse(
            data=products,
            count=len(products),
        )

    async def search_product_in_branch(
        self,
        branch_id: str,
        text_query: str,
    ) -> ListResponse[ProductInDbInBranch]:
        products = await self.products_repo.search_product_in_branch(
            branch_id, text_query
        )
        return ListResponse(
            data=products,
            count=len(products),
        )

    async def update_product_by_id(
        self, product_id: str, body: UpdateProduct
    ) -> ProductInDb:
        updated_product = await self.products_repo.update_product_by_id(
            product_id, body
        )
        if updated_product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        return updated_product

    async def delete_product_by_id(self, product_id: str) -> ProductInDb:
        deleted_product = await self.products_repo.delete_product_by_id(product_id)
        if deleted_product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        return deleted_product


products_controller = ProductsController(
    products_repo=ProductsRepository(
        products_ds=ProductsDataSource(),
    ),
)
