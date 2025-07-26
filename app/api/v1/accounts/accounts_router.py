from fastapi import APIRouter

from repos.v1.accounts import CreateAccount, UpdateAccount, AccountInDb

from responses.v1 import ListResponse

from .accounts_controller import accounts_controller


accounts_router = APIRouter(tags=["accountsV1"])


@accounts_router.post("")
async def create_account(body: CreateAccount) -> AccountInDb:
    return await accounts_controller.create_account(body)


@accounts_router.get("")
async def get_all_accounts() -> ListResponse[AccountInDb]:
    return await accounts_controller.get_all_accounts()


@accounts_router.get("/{account_id}")
async def get_account_by_id(account_id: str) -> AccountInDb:
    return await accounts_controller.get_account_by_id(account_id)


@accounts_router.patch("/{account_id}")
async def update_account_by_id(account_id: str, body: UpdateAccount) -> AccountInDb:
    return await accounts_controller.update_account_by_id(account_id, body)


@accounts_router.delete("/{account_id}")
async def delete_account_by_id(account_id: str) -> AccountInDb:
    return await accounts_controller.delete_account_by_id(account_id)
