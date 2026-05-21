from typing import Any, AsyncGenerator

from kardex.services.mongo_collections.v1 import ProductAccountsCollection


class InventoriesDataSource:
    def get_all_inventories_by_branch(
        self, branch_id: str
    ) -> AsyncGenerator[dict[str, Any], None]:
        collection = ProductAccountsCollection.get_instance()
        return collection.get_all_product_accounts_with_product(branch_id)

    async def get_total_current_stock(self, branch_id: str) -> int:
        collection = ProductAccountsCollection.get_instance()
        return await collection.get_total_current_stock(branch_id)
