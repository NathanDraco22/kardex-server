from .data.product_sale_profiles_datasource import ProductSaleProfilesDataSource
from .models.product_sale_profile_model import (
    ProductSaleProfileInDbWithProduct,
    UpdateProductSaleProfile,
    ProductSaleProfileInDb,
)

from tools import TimeTools


class ProductSaleProfilesRepository:
    def __init__(self, product_sale_profiles_ds: ProductSaleProfilesDataSource):
        self.product_sale_profiles_ds = product_sale_profiles_ds

    async def get_all_product_sale_profiles(
        self, branch_id: str
    ) -> list[ProductSaleProfileInDbWithProduct]:
        results = await self.product_sale_profiles_ds.get_all_product_sale_profiles(
            branch_id
        )
        models = [
            ProductSaleProfileInDbWithProduct.model_validate(result)
            for result in results
        ]
        return models

    async def update_product_sale_profile_by_id(
        self,
        product_id: str,
        branch_id: str,
        product_sale_profile: UpdateProductSaleProfile,
    ) -> ProductSaleProfileInDb | None:
        update_profile_data = product_sale_profile.model_dump(exclude_unset=True)

        update_profile_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.product_sale_profiles_ds.update_product_sale_profile_by_id(
            product_id, branch_id, update_profile_data
        )

        if result is None:
            return None

        return ProductSaleProfileInDb.model_validate(result)

    async def delete_product_sale_profile_by_id(
        self, product_sale_profile_id: str
    ) -> ProductSaleProfileInDb | None:
        result = await self.product_sale_profiles_ds.delete_product_sale_profile_by_id(
            product_sale_profile_id
        )

        if result is None:
            return None

        return ProductSaleProfileInDb.model_validate(result)
