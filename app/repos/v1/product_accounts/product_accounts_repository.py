from .data.product_accounts_datasource import ProductAccountsDataSource
from .models.product_account_model import (
    ProductAccountInDb,
)


class ProductAccountsRepository:
    def __init__(self, product_accounts_ds: ProductAccountsDataSource):
        self.product_accounts_ds = product_accounts_ds

    async def create_product_account(
        self, product_account: ProductAccountInDb
    ) -> ProductAccountInDb:
        await self.product_accounts_ds.create_product_account(
            product_account.model_dump()
        )
        return product_account

    async def get_product_account_by_product_and_branch_id(
        self, product_id: str, branch_id: str
    ) -> ProductAccountInDb | None:
        result = (
            await self.product_accounts_ds.get_product_account_by_product_and_branch_id(
                product_id, branch_id
            )
        )

        if result is None:
            return None

        return ProductAccountInDb.model_validate(result)
