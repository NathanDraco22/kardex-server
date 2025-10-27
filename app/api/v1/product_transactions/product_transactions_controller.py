from repos.v1.product_transactions import (
    ProductTransactionsDataSource,
    ProductTransactionsRepository,
    ProductTransactionInDb,
)

from responses.v1 import ListResponse

from .transaction_query_params import TransactionQueryParams


class ProductTransactionsController:
    def __init__(
        self,
        transaction_repo: ProductTransactionsRepository,
    ) -> None:
        self.transaction_repo = transaction_repo

    async def get_all_product_transactions(
        self, query_params: TransactionQueryParams
    ) -> ListResponse[ProductTransactionInDb]:
        query = query_params.model_dump(exclude_unset=True)

        transactions = await self.transaction_repo.get_all_product_transactions(**query)

        return ListResponse(count=len(transactions), data=transactions)


product_transactions_controller = ProductTransactionsController(
    transaction_repo=ProductTransactionsRepository(
        product_transactions_ds=ProductTransactionsDataSource()
    )
)
