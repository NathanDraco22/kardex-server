from .data.account_balances_datasource import AccountBalancesDataSource
from .models.account_balance_model import (
    AccountBalanceInDb,
)


class AccountBalancesRepository:
    def __init__(self, account_balances_ds: AccountBalancesDataSource):
        self.account_balances_ds = account_balances_ds

    async def get_account_balance(
        self, account_id: str, branch_id: str
    ) -> AccountBalanceInDb | None:
        res = await self.account_balances_ds.get_account_balance(account_id, branch_id)
        if res is None:
            return None

        return AccountBalanceInDb.model_validate(res)
