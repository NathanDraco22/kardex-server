from fastapi import HTTPException, status

from repos.v1.accounts import (
    CreateAccount,
    UpdateAccount,
    AccountInDb,
    AccountsRepository,
    AccountsDataSource,
)

from responses.v1 import ListResponse


class AccountsController:
    def __init__(self, accounts_repo: AccountsRepository) -> None:
        self.accounts_repo = accounts_repo

    async def create_account(self, body: CreateAccount) -> AccountInDb:
        return await self.accounts_repo.create_account(body)

    async def get_all_accounts(self) -> ListResponse[AccountInDb]:
        accounts = await self.accounts_repo.get_all_accounts()
        return ListResponse(
            count=len(accounts),
            data=accounts,
        )

    async def get_account_by_id(self, account_id: str) -> AccountInDb:
        account = await self.accounts_repo.get_account_by_id(account_id)
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found",
            )
        return account

    async def update_account_by_id(
        self, account_id: str, body: UpdateAccount
    ) -> AccountInDb:
        updated_account = await self.accounts_repo.update_account_by_id(
            account_id, body
        )
        if updated_account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found",
            )
        return updated_account

    async def delete_account_by_id(self, account_id: str) -> AccountInDb:
        deleted_account = await self.accounts_repo.delete_account_by_id(account_id)
        if deleted_account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found",
            )
        return deleted_account


accounts_controller = AccountsController(
    accounts_repo=AccountsRepository(
        accounts_ds=AccountsDataSource(),
    ),
)
