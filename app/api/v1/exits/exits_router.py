from fastapi import APIRouter

from repos.v1.transactions import CreateExitTransaction, BatchExitTransaction
from repos.v1.account_balances import AccountBalanceInDb
from .exits_controller import exits_controller

exits_router = APIRouter(tags=["exitsV1"])


@exits_router.post("")
async def create_exit(body: CreateExitTransaction) -> AccountBalanceInDb:
    return await exits_controller.create_exit(body)


@exits_router.post("/batch")
async def batch_exit(body: BatchExitTransaction) -> list[AccountBalanceInDb]:
    return await exits_controller.batch_exit(body)
