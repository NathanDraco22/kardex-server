from repos.v1.transactions import (
    CreateEntryTransaction,
    CreateExitTransaction,
    BatchEntryTransaction,
    BatchExitTransaction,
    TransactionInDb,
)

from repos.v1.account_balances import AccountBalanceInDb

from services.mongo_collections.v1 import TransactionsCollection
from services.mongo_collections.v1 import AccountBalancesCollection
from services import MongoService

from tools import TimeTools, UuidTool


async def process_account_entry_transaction(
    entry: CreateEntryTransaction,
) -> AccountBalanceInDb:
    client = MongoService().client

    transaction_col = TransactionsCollection()
    account_balance_col = AccountBalancesCollection()

    async with await client.start_session() as session:
        async with session.start_transaction():
            result = await account_balance_col.update_account_balance_with_session(
                entry.accountId,
                entry.branchId,
                entry.quantity,
                updated_at=TimeTools.get_now_utc(),
                session=session,
            )

            entry_data = entry.model_dump()

            new_transaction = TransactionInDb(
                id=UuidTool.generate_uuid(),
                createdAt=TimeTools.get_now_utc(),
                **entry_data,
            )

            transaction_data = new_transaction.model_dump()

            await transaction_col.create_transaction_with_session(
                transaction_data,
                session,
            )

            return AccountBalanceInDb.model_validate(result)


class InsufficientBalanceError(Exception):
    pass


async def process_account_exit_transaction(
    exit: CreateExitTransaction,
) -> AccountBalanceInDb:
    client = MongoService().client

    transaction_col = TransactionsCollection()
    account_balance_col = AccountBalancesCollection()

    async with await client.start_session() as session:
        async with session.start_transaction():
            result = await account_balance_col.subtract_account_balance_with_session(
                exit.accountId,
                exit.branchId,
                exit.quantity,
                updated_at=TimeTools.get_now_utc(),
                session=session,
            )

            if result is None:
                raise InsufficientBalanceError()

            exit_data = exit.model_dump()

            new_transaction = TransactionInDb(
                id=UuidTool.generate_uuid(),
                createdAt=TimeTools.get_now_utc(),
                **exit_data,
            )

            transaction_data = new_transaction.model_dump()

            await transaction_col.create_transaction_with_session(
                transaction_data,
                session,
            )

            return AccountBalanceInDb.model_validate(result)


async def process_batch_account_entry_transaction(
    batch_entry_transaction: BatchEntryTransaction,
) -> list[AccountBalanceInDb]:
    client = MongoService().client

    transaction_col = TransactionsCollection()
    account_balance_col = AccountBalancesCollection()

    async with await client.start_session() as session:
        async with session.start_transaction():
            updated_balances: list[AccountBalanceInDb] = []

            create_entry_transacions: list[TransactionInDb] = []

            for entry_item in batch_entry_transaction.items:
                result = await account_balance_col.update_account_balance_with_session(
                    entry_item.accountId,
                    batch_entry_transaction.branchId,
                    entry_item.quantity,
                    updated_at=TimeTools.get_now_utc(),
                    session=session,
                )

                updated_balance = AccountBalanceInDb.model_validate(result)

                updated_balances.append(updated_balance)

                new_entry_transaction = CreateEntryTransaction(
                    accountId=entry_item.accountId,
                    branchId=batch_entry_transaction.branchId,
                    quantity=entry_item.quantity,
                )

                entry_data = new_entry_transaction.model_dump()

                new_transaction = TransactionInDb(
                    id=UuidTool.generate_uuid(),
                    createdAt=TimeTools.get_now_utc(),
                    **entry_data,
                )

                create_entry_transacions.append(new_transaction)

            entry_data = [entry.model_dump() for entry in create_entry_transacions]

            await transaction_col.create_many_transactions_with_session(
                entry_data,
                session,
            )

            return updated_balances


async def process_batch_account_exit_transaction(
    batch_exit_transaction: BatchExitTransaction,
) -> list[AccountBalanceInDb]:
    client = MongoService().client

    transaction_col = TransactionsCollection()
    account_balance_col = AccountBalancesCollection()

    async with await client.start_session() as session:
        async with session.start_transaction():
            updated_balances: list[AccountBalanceInDb] = []

            create_exit_transacions: list[TransactionInDb] = []

            for exit_item in batch_exit_transaction.items:
                result = (
                    await account_balance_col.subtract_account_balance_with_session(
                        exit_item.accountId,
                        batch_exit_transaction.branchId,
                        exit_item.quantity,
                        updated_at=TimeTools.get_now_utc(),
                        session=session,
                    )
                )

                if result is None:
                    raise InsufficientBalanceError()

                updated_balance = AccountBalanceInDb.model_validate(result)

                updated_balances.append(updated_balance)

                new_exit_transaction = CreateExitTransaction(
                    accountId=exit_item.accountId,
                    branchId=batch_exit_transaction.branchId,
                    quantity=exit_item.quantity,
                )

                exit_data = new_exit_transaction.model_dump()

                transaction = TransactionInDb(
                    id=UuidTool.generate_uuid(),
                    createdAt=TimeTools.get_now_utc(),
                    **exit_data,
                )

                create_exit_transacions.append(transaction)

            exit_data = [exit.model_dump() for exit in create_exit_transacions]

            await transaction_col.create_many_transactions_with_session(
                exit_data,
                session,
            )

            return updated_balances
