from kardex.repos.v1.common.filter_params import ProductTransactionFilterParams
from kardex.repos.v1.product_transactions import (
    ProductTransactionsDataSource,
    ProductTransactionsRepository,
    ProductTransactionInDb,
)

from responses.v1 import ListResponse


class ProductTransactionsController:
    def __init__(
        self,
        transaction_repo: ProductTransactionsRepository,
    ) -> None:
        self.transaction_repo = transaction_repo

    async def get_all_product_transactions(
        self, query_params: ProductTransactionFilterParams
    ) -> ListResponse[ProductTransactionInDb]:
        transactions = await self.transaction_repo.get_all_product_transactions(query_params)

        return ListResponse(count=len(transactions), data=transactions)


product_transactions_controller = ProductTransactionsController(
    transaction_repo=ProductTransactionsRepository(
        product_transactions_ds=ProductTransactionsDataSource()
    )
)
