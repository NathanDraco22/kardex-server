from tools import UuidTool, TimeTools

from .data.accounts_datasource import AccountsDataSource
from .models.account_model import CreateAccount, UpdateAccount, AccountInDb


class AccountsRepository:
    def __init__(self, accounts_ds: AccountsDataSource):
        self.accounts_ds = accounts_ds

    async def create_account(self, create_account: CreateAccount) -> AccountInDb:
        new_account = AccountInDb(
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_utc(),
            **create_account.model_dump(),
        )

        result = await self.accounts_ds.create_account(new_account.model_dump())

        return AccountInDb.model_validate(result)

    async def get_all_accounts(self) -> list[AccountInDb]:
        results = await self.accounts_ds.get_all_accounts()
        models = [AccountInDb.model_validate(result) for result in results]
        return models

    async def get_account_by_id(self, account_id: str) -> AccountInDb | None:
        result = await self.accounts_ds.get_account_by_id(account_id)

        if result is None:
            return None

        return AccountInDb.model_validate(result)

    async def update_account_by_id(
        self, account_id: str, account: UpdateAccount
    ) -> AccountInDb | None:
        update_account_data = account.model_dump(exclude_unset=True)

        update_account_data["updatedAt"] = TimeTools.get_now_utc()

        result = await self.accounts_ds.update_account_by_id(
            account_id, update_account_data
        )

        if result is None:
            return None

        return AccountInDb.model_validate(result)

    async def delete_account_by_id(self, account_id: str) -> AccountInDb | None:
        result = await self.accounts_ds.delete_account_by_id(account_id)

        if result is None:
            return None

        return AccountInDb.model_validate(result)

    async def count_accounts(self, account_ids: list[str]) -> int:
        return await self.accounts_ds.count_accounts(account_ids)
