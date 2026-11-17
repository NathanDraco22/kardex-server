from .data.product_accounts_datasource import ProductAccountsDataSource
from .models.product_account_model import (
    ProductAccountInDb,
)
from kardex.kardex_config import KardexConfig
from kardex.services.mongo_collections.v1 import ProductsCollection
from kardex.tools import DirectStockAdjustmentBlocked, InvalidOperation

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
        if KardexConfig().followTransaction:
            if "currentStock" in kwargs:
                raise DirectStockAdjustmentBlocked(
                    "Direct stock updates are not allowed when followTransaction is active."
                )
            product = await ProductsCollection.get_instance().fetch_product_by_id(
                product_id
            )
            if product is None or product.get("productType", "item") == "item":
                raise DirectStockAdjustmentBlocked(
                    "Direct stock updates are not allowed when followTransaction is active."
                )
            if "averageCost" in kwargs:
                kwargs.setdefault("lastCost", kwargs["averageCost"])
                kwargs.setdefault("maximumCost", kwargs["averageCost"])
        result = await self.product_accounts_ds.update_product_account_stock_and_cost(
            product_id, branch_id, **kwargs
        )
        if result is None:
            return None
        return ProductAccountInDb.model_validate(result)

    async def add_product_account_stock(
        self, product_id: str, branch_id: str, **kwargs
    ) -> ProductAccountInDb | None:
        if KardexConfig().followTransaction:
            raise DirectStockAdjustmentBlocked(
                "Direct stock adjustments are not allowed when followTransaction is active."
            )
        product = await ProductsCollection.get_instance().fetch_product_by_id(
            product_id
        )
        if product is not None and product.get("productType", "item") != "item":
            raise InvalidOperation(
                "Los servicios y productos no inventariables no manejan existencias."
            )
        result = await self.product_accounts_ds.add_product_account_stock(
            product_id, branch_id, **kwargs
        )
        if result is None:
            return None
        return ProductAccountInDb.model_validate(result)

    async def substract_product_account_stock(
        self, product_id: str, branch_id: str, **kwargs
    ) -> ProductAccountInDb | None:
        if KardexConfig().followTransaction:
            raise DirectStockAdjustmentBlocked(
                "Direct stock adjustments are not allowed when followTransaction is active."
            )
        product = await ProductsCollection.get_instance().fetch_product_by_id(
            product_id
        )
        if product is not None and product.get("productType", "item") != "item":
            raise InvalidOperation(
                "Los servicios y productos no inventariables no manejan existencias."
            )
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
