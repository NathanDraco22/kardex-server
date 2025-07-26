from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import ProductAccountsCollection


class ProductAccountsDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

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
