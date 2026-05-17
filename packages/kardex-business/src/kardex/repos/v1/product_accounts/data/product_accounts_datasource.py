from typing import Any
from kardex.services.mongo_collections.v1 import ProductAccountsCollection


class ProductAccountsDataSource:
    async def create_product_account(
        self, product_account: dict[str, Any]
    ) -> dict[str, Any]:
        collection = ProductAccountsCollection()
        await collection.create_product_account(product_account)
        return product_account

    async def get_product_account_by_product_and_branch_id(
        self, product_id: str, branch_id: str
    ) -> dict[str, Any] | None:
        collection = ProductAccountsCollection()
        return await collection.get_product_account_by_product_and_branch_id(
            product_id, branch_id
        )

    async def update_product_account_stock_and_cost(
        self, product_id: str, branch_id: str, **kwargs
    ) -> dict[str, Any] | None:
        collection = ProductAccountsCollection()
        return await collection.update_product_account_stock_and_cost(
            product_id, branch_id, **kwargs
        )

    async def add_product_account_stock(
        self, product_id: str, branch_id: str, **kwargs
    ) -> dict[str, Any] | None:
        collection = ProductAccountsCollection()
        return await collection.add_product_account_stock(
            product_id, branch_id, **kwargs
        )

    async def substract_product_account_stock(
        self, product_id: str, branch_id: str, **kwargs
    ) -> dict[str, Any] | None:
        collection = ProductAccountsCollection()
        return await collection.substract_product_account_stock(
            product_id, branch_id, **kwargs
        )

    async def get_product_accounts_by_product(
        self, product_id: str
    ) -> list[dict[str, Any]]:
        collection = ProductAccountsCollection()
        return await collection.get_product_accounts_by_product(product_id)

    async def get_product_account_with_product_data(
        self,
        product_id: str,
        branch_id: str,
    ) -> dict[str, Any] | None:
        collection = ProductAccountsCollection()
        return await collection.get_product_account_with_product_data(
            product_id, branch_id
        )
