from .data.product_accounts_datasource import ProductAccountsDataSource
from .models.product_account_model import (
    ProductAccountInDb,
)

class ProductAccountsRepository:
    _instance: "ProductAccountsRepository | None" = None

    def __init__(self, product_accounts_ds: ProductAccountsDataSource):
        self.product_accounts_ds = product_accounts_ds

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ProductAccountsRepository(
                product_accounts_ds=ProductAccountsDataSource()
            )
        return cls._instance

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

    async def update_product_account_stock_and_cost(
        self, product_id: str, branch_id: str, **kwargs
    ) -> ProductAccountInDb | None:
        result = await self.product_accounts_ds.update_product_account_stock_and_cost(
            product_id, branch_id, **kwargs
        )
        if result is None:
            return None
        return ProductAccountInDb.model_validate(result)

    async def add_product_account_stock(
        self, product_id: str, branch_id: str, **kwargs
    ) -> ProductAccountInDb | None:
        result = await self.product_accounts_ds.add_product_account_stock(
            product_id, branch_id, **kwargs
        )
        if result is None:
            return None
        return ProductAccountInDb.model_validate(result)

    async def substract_product_account_stock(
        self, product_id: str, branch_id: str, **kwargs
    ) -> ProductAccountInDb | None:
        result = await self.product_accounts_ds.substract_product_account_stock(
            product_id, branch_id, **kwargs
        )
        if result is None:
            return None
        return ProductAccountInDb.model_validate(result)

    async def get_product_accounts_by_product(
        self, product_id: str
    ) -> list[ProductAccountInDb]:
        result = await self.product_accounts_ds.get_product_accounts_by_product(
            product_id
        )

        return [ProductAccountInDb.model_validate(account) for account in result]
