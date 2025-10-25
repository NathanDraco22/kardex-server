from .data.product_transactions_datasource import ProductTransactionsDataSource
from .models.product_transaction_model import ProductTransactionInDb


class ProductTransactionsRepository:
    def __init__(self, product_transactions_ds: ProductTransactionsDataSource):
        self.product_transactions_ds = product_transactions_ds

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
