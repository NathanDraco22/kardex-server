from fastapi import HTTPException, status

from repos.v1.product_sale_profiles import (
    UpdateProductSaleProfile,
    ProductSaleProfileInDb,
    ProductSaleProfileInDbWithProduct,
    ProductSaleProfilesRepository,
    ProductSaleProfilesDataSource,
)

from responses.v1 import ListResponse


class ProductSaleProfilesController:
    def __init__(
        self, product_sale_profiles_repo: ProductSaleProfilesRepository
    ) -> None:
        self.product_sale_profiles_repo = product_sale_profiles_repo

    async def get_all_product_sale_profiles(
        self, branch_id: str
    ) -> ListResponse[ProductSaleProfileInDbWithProduct]:
        product_sale_profiles = (
            await self.product_sale_profiles_repo.get_all_product_sale_profiles(
                branch_id
            )
        )
        return ListResponse(
            count=len(product_sale_profiles),
            data=product_sale_profiles,
        )

    async def update_product_sale_profile_by_id(
        self,
        branch_id: str,
        product_id: str,
        body: UpdateProductSaleProfile,
    ) -> ProductSaleProfileInDb:
        updated_product_sale_profile = (
            await self.product_sale_profiles_repo.update_product_sale_profile_by_id(
                branch_id,
                product_id,
                body,
            )
        )
        if updated_product_sale_profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ProductSaleProfile not found",
            )
        return updated_product_sale_profile


product_sale_profiles_controller = ProductSaleProfilesController(
    product_sale_profiles_repo=ProductSaleProfilesRepository(
        product_sale_profiles_ds=ProductSaleProfilesDataSource(),
    ),
)
