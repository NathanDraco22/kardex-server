from .data.product_transactions_datasource import ProductTransactionsDataSource
from .models.product_transaction_model import CreateProductTransaction, UpdateProductTransaction, ProductTransactionInDb


class ProductTransactionsRepository:
    def __init__(self, product_transactions_ds: ProductTransactionsDataSource):
        self.product_transactions_ds = product_transactions_ds

    async def create_product_transaction(self, create_product_transaction: CreateProductTransaction) -> ProductTransactionInDb:
        # TODO: implement create
        raise NotImplementedError()

    async def get_all_product_transactions(self) -> list[ProductTransactionInDb]:
        results = await self.product_transactions_ds.get_all_product_transactions()
        models = [ProductTransactionInDb.model_validate(result) for result in results]
        return models

    async def get_product_transaction_by_id(self, product_transaction_id: str) -> ProductTransactionInDb | None :
        result = await self.product_transactions_ds.get_product_transaction_by_id(product_transaction_id)
        
        if result is None:
            return None
        
        return ProductTransactionInDb.model_validate(result)

    async def update_product_transaction_by_id(self, product_transaction_id: str, product_transaction: UpdateProductTransaction) -> ProductTransactionInDb | None:
        # TODO: implement update
        raise NotImplementedError()

    async def delete_product_transaction_by_id(self, product_transaction_id: str) -> ProductTransactionInDb | None:
        result = await self.product_transactions_ds.delete_product_transaction_by_id(product_transaction_id)
        
        if result is None:
            return None
        
        return ProductTransactionInDb.model_validate(result)
