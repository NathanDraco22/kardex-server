from typing import Any
from services.mongo_collections.v1 import ProductSaleProfilesCollection


class ProductSaleProfilesDataSource:
    async def create_product_sale_profile(
        self, product_sale_profile: dict[str, Any]
    ) -> dict[str, Any]:
        collection = ProductSaleProfilesCollection()
        await collection.create_product_sale_profile(product_sale_profile)
        return product_sale_profile

    async def get_all_product_sale_profiles(
        self, branch_id: str
    ) -> list[dict[str, Any]]:
        collection = ProductSaleProfilesCollection()
        return await collection.fetch_all_product_sale_profiles(branch_id)

    async def update_product_sale_profile_by_id(
        self, branch_id: str, product_id: str, product_sale_profile: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = ProductSaleProfilesCollection()
        return await collection.update_product_sale_profile_by_id(
            branch_id, product_id, product_sale_profile
        )

    async def delete_product_sale_profile_by_id(
        self, product_sale_profile_id: str
    ) -> dict[str, Any] | None:
        collection = ProductSaleProfilesCollection()
        return await collection.delete_product_sale_profile_by_id(
            product_sale_profile_id
        )
