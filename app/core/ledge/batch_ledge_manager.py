import asyncio
from fastapi import HTTPException, status
from pymongo.errors import OperationFailure

from repos.v1.branches import BranchesRepository, BranchesDataSource
from repos.v1.accounts import AccountsRepository, AccountsDataSource
from repos.v1.transactions import BatchEntryTransaction, BatchExitTransaction

from repos.v1.account_balances import AccountBalanceInDb

from .db_transactions import (
    process_batch_account_entry_transaction,
    process_batch_account_exit_transaction,
    InsufficientBalanceError,
)


class BatchLedgerManager:
    def __init__(self) -> None:
        self.branches_repo = BranchesRepository(BranchesDataSource())
        self.accounts_repo = AccountsRepository(AccountsDataSource())
        pass

    async def create_batch_entry(
        self,
        batch_entry: BatchEntryTransaction,
    ) -> list[AccountBalanceInDb]:
        branch = await self.branches_repo.get_branch_by_id(batch_entry.branchId)

        if branch is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch not found",
            )

        account_ids = [item.accountId for item in batch_entry.items]

        total_accounts = await self.accounts_repo.count_accounts(account_ids)

        if total_accounts != len(account_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found",
            )

        max_retries = 3
        for _ in range(max_retries):
            try:
                result = await process_batch_account_entry_transaction(batch_entry)
                return result

            except OperationFailure as e:
                if e.code == 112:
                    await asyncio.sleep(0.3)
                    continue
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error processing account entry transaction \n" + str(e),
                    )

            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error processing account entry transaction \n" + str(e),
                )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing account entry transaction",
        )

    async def create_batch_exit(self, create_exit_transaction: BatchExitTransaction):
        branch = await self.branches_repo.get_branch_by_id(
            create_exit_transaction.branchId
        )

        if branch is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch not found",
            )

        account_ids = [item.accountId for item in create_exit_transaction.items]

        total_accounts = await self.accounts_repo.count_accounts(account_ids)

        if total_accounts != len(account_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found",
            )

        max_retries = 3
        for _ in range(max_retries):
            try:
                result = await process_batch_account_exit_transaction(
                    create_exit_transaction
                )
                return result

            except OperationFailure as e:
                if e.code == 112:
                    await asyncio.sleep(0.3)
                    continue
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error processing account entry transaction \n" + str(e),
                    )

            except InsufficientBalanceError as _:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient balance",
                )

            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error processing account entry transaction \n" + str(e),
                )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing account entry transaction",
        )
