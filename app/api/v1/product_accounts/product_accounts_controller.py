from responses.v1 import ListResponse
from fastapi import HTTPException, status
from kardex.repos.v1.product_accounts import (
    ProductAccountsRepository,
    ProductAccountsDataSource,
    ProductAccountInDb,
    UpdateProductAccount,
    AddToProductAccount,
    SubstractToProductAccount,
)

from kardex.repos.v1.expiration_logs import (
    ExpirationLogsRepository,
    CreateExpirationLog,
    ProductInfo,
)
from kardex.repos.v1.products import ProductsRepository


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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
            )
        return res

    async def add_product_account(
        self, product_id: str, branch_id: str, add_data: AddToProductAccount
    ) -> ProductAccountInDb:
        kwargs = add_data.model_dump(exclude_none=True)
        res = await self.product_account_repo.add_product_account_stock(
            product_id, branch_id, **kwargs
        )
        if res is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
            )

        try:
            if add_data.expirationDate is not None:
                product_repo = ProductsRepository.get_instance()
                product = await product_repo.get_product_by_id(res.productId)

                if product is not None:
                    create_log = CreateExpirationLog(
                        product=ProductInfo(
                            id=product.id,
                            name=product.name,
                            brandName=product.brandName,
                            categoryName=product.categoryName,
                            code=product.code,
                            unitName=product.unitName,
                        ),
                        branchId=res.branchId,
                        expirationDate=add_data.expirationDate,
                    )
                    expiration_log_repo = ExpirationLogsRepository.get_instance()
                    await expiration_log_repo.create_expiration_log(create_log)
        except Exception as e:
            print(e)

        return res

    async def substract_product_account(
        self, product_id: str, branch_id: str, sub_data: SubstractToProductAccount
    ) -> ProductAccountInDb:
        kwargs = sub_data.model_dump(exclude_none=True)
        res = await self.product_account_repo.substract_product_account_stock(
            product_id, branch_id, **kwargs
        )
        if res is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
            )
        return res


product_accounts_controller = ProductAccountsController(
    product_account_repo=ProductAccountsRepository(
        product_accounts_ds=ProductAccountsDataSource()
    ),
)
