from responses.v1 import ListResponse
from repos.v1.products import (
    ProductsRepository,
    ProductInDbWithAccounts,
    ProductsDataSource,
)


class ProductAccountsController:
    def __init__(self, product_repo: ProductsRepository) -> None:
        self.product_repo = product_repo
        pass

    async def get_all_product_with_accounts(
        self, branch_id: str, current_pos: int
    ) -> ListResponse[ProductInDbWithAccounts]:
        LIMIT = 50
        page = int((current_pos / LIMIT) + 1)
        res = await self.product_repo.get_all_products_with_accounts(
            branch_id, page, LIMIT
        )
        models = [ProductInDbWithAccounts.model_validate(result) for result in res]
        return ListResponse(count=len(models), data=models)


product_accounts_controller = ProductAccountsController(
    product_repo=ProductsRepository(
        products_ds=ProductsDataSource(),
    )
)
