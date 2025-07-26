from repos.v1.transactions import CreateExitTransaction, BatchExitTransaction
from repos.v1.account_balances import AccountBalanceInDb
from core.ledge.ledge_manager import LedgerManager
from core.ledge.batch_ledge_manager import BatchLedgerManager


class ExitsController:
    def __init__(
        self, ledge_manager: LedgerManager, batch_ledge_manager: BatchLedgerManager
    ):
        self.ledge_manager = ledge_manager
        self.batch_ledge_manager = batch_ledge_manager

    async def create_exit(self, body: CreateExitTransaction) -> AccountBalanceInDb:
        return await self.ledge_manager.create_exit(body)

    async def batch_exit(self, body: BatchExitTransaction) -> list[AccountBalanceInDb]:
        return await self.batch_ledge_manager.create_batch_exit(body)


exits_controller = ExitsController(
    LedgerManager(),
    BatchLedgerManager(),
)
