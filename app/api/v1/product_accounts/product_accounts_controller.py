from responses.v1 import ListResponse
from repos.v1.product_accounts import (
    ProductAccountsRepository,
    ProductAccountsDataSource,
    ProductAccountInDb,
)


class ProductAccountsController:
    def __init__(self, product_account_repo: ProductAccountsRepository) -> None:
        self.product_account_repo = product_account_repo
        pass

    async def get_product_accounts_by_product(
        self, product_id: str
    ) -> ListResponse[ProductAccountInDb]:
        res = await self.product_account_repo.get_product_accounts_by_product(
            product_id
        )
        return ListResponse(
            data=res,
            count=len(res),
        )


product_accounts_controller = ProductAccountsController(
    product_account_repo=ProductAccountsRepository(
        product_accounts_ds=ProductAccountsDataSource()
    ),
)
