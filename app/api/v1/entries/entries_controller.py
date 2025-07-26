from repos.v1.transactions import CreateEntryTransaction, BatchEntryTransaction
from repos.v1.account_balances import AccountBalanceInDb
from core.ledge.ledge_manager import LedgerManager
from core.ledge.batch_ledge_manager import BatchLedgerManager


class EntriesController:
    def __init__(
        self, ledge_manager: LedgerManager, batch_ledge_manager: BatchLedgerManager
    ) -> None:
        self.ledge_manager = ledge_manager
        self.batch_ledge_manager = batch_ledge_manager
        pass

    async def create_entry(self, body: CreateEntryTransaction) -> AccountBalanceInDb:
        return await self.ledge_manager.create_entry(body)

    async def batch_entry(
        self,
        body: BatchEntryTransaction,
    ) -> list[AccountBalanceInDb]:
        return await self.batch_ledge_manager.create_batch_entry(body)


entries_controller = EntriesController(
    LedgerManager(),
    BatchLedgerManager(),
)
