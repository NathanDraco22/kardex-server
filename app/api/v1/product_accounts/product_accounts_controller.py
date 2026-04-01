from responses.v1 import ListResponse
from fastapi import HTTPException, status
from repos.v1.product_accounts import (
    ProductAccountsRepository,
    ProductAccountsDataSource,
    ProductAccountInDb,
    UpdateProductAccount,
    AddToProductAccount,
    SubstractToProductAccount,
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

    async def update_product_account(
        self, product_id: str, branch_id: str, update_data: UpdateProductAccount
    ) -> ProductAccountInDb:
        kwargs = update_data.model_dump(exclude_none=True)
        res = await self.product_account_repo.update_product_account_stock_and_cost(
            product_id, branch_id, **kwargs
        )
        if res is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        return res

    async def add_product_account(
        self, product_id: str, branch_id: str, add_data: AddToProductAccount
    ) -> ProductAccountInDb:
        kwargs = add_data.model_dump(exclude_none=True)
        res = await self.product_account_repo.add_product_account_stock(
            product_id, branch_id, **kwargs
        )
        if res is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        return res

    async def substract_product_account(
        self, product_id: str, branch_id: str, sub_data: SubstractToProductAccount
    ) -> ProductAccountInDb:
        kwargs = sub_data.model_dump(exclude_none=True)
        res = await self.product_account_repo.substract_product_account_stock(
            product_id, branch_id, **kwargs
        )
        if res is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
        return res


product_accounts_controller = ProductAccountsController(
    product_account_repo=ProductAccountsRepository(
        product_accounts_ds=ProductAccountsDataSource()
    ),
)
