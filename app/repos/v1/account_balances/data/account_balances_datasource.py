from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import AccountBalancesCollection


class AccountBalancesDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def get_account_balance(
        self, account_id: str, branch_id: str
    ) -> dict[str, Any] | None:
        collection = AccountBalancesCollection()
        return await collection.fetch_account_balance(account_id, branch_id)
