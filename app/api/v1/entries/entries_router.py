from fastapi import APIRouter

from .entries_controller import entries_controller

from repos.v1.transactions import CreateEntryTransaction, BatchEntryTransaction
from repos.v1.account_balances import AccountBalanceInDb

entries_router = APIRouter(tags=["entriesV1"])


@entries_router.post("")
async def create_entry(create_entry: CreateEntryTransaction) -> AccountBalanceInDb:
    return await entries_controller.create_entry(create_entry)


@entries_router.post("/batch")
async def batch_entry(body: BatchEntryTransaction) -> list[AccountBalanceInDb]:
    return await entries_controller.batch_entry(body)
