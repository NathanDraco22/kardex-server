from typing import AsyncIterable
from .data.products_datasource import ProductsDataSource
from .models.product_model import (
    CreateProduct,
    UpdateProduct,
    ProductInDb,
    ProductInDbWithAccounts,
    ProductInDbInBranch,
    CreateProductWithData,
)
from kardex.core.counter_manager.counter_manager import CounterManager
from kardex.tools import UuidTool, TimeTools, generate_prefixes
from kardex.kardex_config import KardexConfig
from kardex.lite.core.product_register.process_create_product import process_create_product
from kardex.core.product_register.process_create_product_with_data import (
    process_create_product_with_data,
)
from kardex.core.product_register.product_type_lifecycle import (
    create_branch_scoped_product,
    update_product_with_type_transition,
)


from kardex.repos.v1.common.filter_params import ProductFilterParams


class ProductsRepository:
    _instance: "ProductsRepository | None" = None

    def __init__(self, products_ds: ProductsDataSource):
        self.products_ds = products_ds

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ProductsRepository(
                products_ds=ProductsDataSource()
            )
        return cls._instance

    async def create_product(self, create_product: CreateProduct) -> ProductInDb:
        if create_product.productType != "item":
            return await create_branch_scoped_product(create_product)

        create_product.branchId = None
        if KardexConfig().createFullProductProfile:
            return await process_create_product(create_product)

        if not create_product.code:
            create_product.code = await CounterManager().next_product_number()

        new_product = ProductInDb(
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
            **create_product.model_dump(),
        )

        new_product_data = new_product.model_dump()
        new_product_data["searchPrefixes"] = generate_prefixes(new_product_data["name"])

        result = await self.products_ds.create_product(new_product_data)

        return ProductInDb.model_validate(result)

    async def create_product_with_data(
        self, body: CreateProductWithData
    ) -> ProductInDbInBranch:
        return await process_create_product_with_data(body)

    async def get_all_products(self) -> list[ProductInDb]:
        results = await self.products_ds.get_all_products()
        models = [ProductInDb.model_validate(result) for result in results]
        return models

    async def get_all_products_with_accounts(
        self, branch_id: str, page: int, limit: int
    ) -> list[ProductInDbWithAccounts]:
        results = await self.products_ds.get_all_products_with_accounts(
            branch_id,
            page,
            limit,
        )
        models = [ProductInDbWithAccounts.model_validate(result) for result in results]
        return models

    async def get_paginated_products(
        self,
        offset: int,
        limit: int,
        branch_id: str | None = None,
        product_type: str | None = None,
        only_inventory: bool | None = None,
    ) -> list[ProductInDb]:
        results = await self.products_ds.get_paginated_products(
            offset,
            limit,
            branch_id=branch_id,
            product_type=product_type,
            only_inventory=only_inventory,
        )
        models = [ProductInDb.model_validate(result) for result in results]
        return models

    async def get_product_by_id(self, product_id: str) -> ProductInDb | None:
        result = await self.products_ds.get_product_by_id(product_id)

        if result is None:
            return None

        return ProductInDb.model_validate(result)

    async def get_product_by_code(self, product_code: str) -> ProductInDb | None:
        result = await self.products_ds.get_product_by_code(product_code)

        if result is None:
            return None

        return ProductInDb.model_validate(result)

    async def search_product_by_text(
        self,
        text_query: str,
        branch_id: str | None = None,
        product_type: str | None = None,
        only_inventory: bool | None = None,
    ) -> list[ProductInDb]:
        results = await self.products_ds.search_product_by_text(
            text_query,
            branch_id=branch_id,
            product_type=product_type,
            only_inventory=only_inventory,
        )
        models = [ProductInDb.model_validate(result) for result in results]
        return models

    async def get_product_by_ids(self, product_ids: list[str]) -> list[ProductInDb]:
        result = await self.products_ds.get_product_by_ids(product_ids)

        return [ProductInDb.model_validate(product) for product in result]

    async def search_product_in_branch(
        self,
        branch_id: str,
        text_query: str,
        product_type: str | None = None,
        only_inventory: bool | None = None,
    ) -> list[ProductInDbInBranch]:
        results = await self.products_ds.search_product_in_branch(
            branch_id,
            text_query,
            product_type=product_type,
            only_inventory=only_inventory,
        )
        models = [ProductInDbInBranch.model_validate(result) for result in results]
        return models

    async def get_products_in_branch_by_ids(
        self,
        branch_id: str,
        product_ids: list[str],
    ) -> list[ProductInDbInBranch]:
        results = await self.products_ds.get_products_in_branch_by_ids(branch_id, product_ids)
        models = [ProductInDbInBranch.model_validate(result) for result in results]
        return models

    async def get_all_product_in_branch(self, params: ProductFilterParams) -> list[ProductInDbInBranch]:
        results = await self.products_ds.get_all_product_in_branch(
            **params.model_dump(exclude_unset=True)
        )
        models = [ProductInDbInBranch.model_validate(result) for result in results]
        return models

    async def get_all_product_in_branch_streamed(
        self, params: ProductFilterParams
    ) -> AsyncIterable[ProductInDbInBranch]:
        async for result in await self.products_ds.get_all_product_in_branch_streamed(
            **params.model_dump(exclude_unset=True)
        ):
            yield ProductInDbInBranch.model_validate(result)

    async def get_product_in_branch_by_id(
        self, product_id: str, branch_id: str
    ) -> ProductInDbInBranch | None:
        result = await self.products_ds.get_product_in_branch_by_id(
            product_id, branch_id
        )

        if result is None:
            return None

        return ProductInDbInBranch.model_validate(result)

    async def update_product_by_id(
        self, product_id: str, product: UpdateProduct
    ) -> ProductInDb | None:
        return await update_product_with_type_transition(product_id, product)

    async def delete_product_by_id(self, product_id: str) -> ProductInDb | None:
        result = await self.products_ds.delete_product_by_id(product_id)

        if result is None:
            return None

        return ProductInDb.model_validate(result)
