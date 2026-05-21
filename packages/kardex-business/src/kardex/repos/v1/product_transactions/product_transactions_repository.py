from .data.product_transactions_datasource import ProductTransactionsDataSource
from .models.product_transaction_model import ProductTransactionInDb

class ProductTransactionsRepository:
    _instance: "ProductTransactionsRepository | None" = None

    def __init__(self, product_transactions_ds: ProductTransactionsDataSource):
        self.product_transactions_ds = product_transactions_ds

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ProductTransactionsRepository(
                product_transactions_ds=ProductTransactionsDataSource()
            )
        return cls._instance

    async def get_all_product_transactions(
        self, **kwargs
    ) -> list[ProductTransactionInDb]:
        results = await self.product_transactions_ds.get_all_product_transactions(
            **kwargs
        )
        models = [ProductTransactionInDb.model_validate(result) for result in results]
        return models

    async def get_product_transaction_by_id(
        self, product_transaction_id: str
    ) -> ProductTransactionInDb | None:
        result = await self.product_transactions_ds.get_product_transaction_by_id(
            product_transaction_id
        )

        if result is None:
            return None

        return ProductTransactionInDb.model_validate(result)

    async def estimate_product_stats(self, **kwargs):
        await self.product_transactions_ds.estimate_product_stats(**kwargs)
