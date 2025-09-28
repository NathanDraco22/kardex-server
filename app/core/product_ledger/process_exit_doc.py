from tools import UuidTool, TimeTools
from repos.v1.exit_docs import ExitDocInDb, CreateExitDoc
from repos.v1.product_accounts import ProductAccountInDb
from repos.v1.product_transactions import ProductTransactionInDb

from services import MongoService
from services.mongo_collections.v1 import (
    ExitDocsCollection,
    ProductTransactionsCollection,
    ProductAccountsCollection,
)


class InsufficientBalanceError(Exception):
    pass


async def process_exit_doc(
    create_exit_doc: CreateExitDoc,
) -> tuple[ExitDocInDb, list[ProductAccountInDb]]:
    mongo_client = MongoService().client
    prd_transaction_col = ProductTransactionsCollection()
    product_account_col = ProductAccountsCollection()

    exit_items = create_exit_doc.items

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            new_exit_doc_generated_id = UuidTool.generate_uuid()

            updated_product_accounts: list[ProductAccountInDb] = []

            created_transactions: list[ProductTransactionInDb] = []

            for index, exit_item in enumerate(exit_items):
                result = await product_account_col.substract_product_account_data(
                    exit_item.productId,
                    create_exit_doc.branchId,
                    exit_item.quantity,
                    session=session,
                )

                if result is None:
                    raise InsufficientBalanceError()

                updated_product_account = ProductAccountInDb.model_validate(result)

                exit_item.cost = updated_product_account.averageCost

                updated_product_accounts.append(updated_product_account)

                new_transaction = ProductTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    documentId=new_exit_doc_generated_id,
                    type="exit",
                    subtype="exit",
                    productId=exit_item.productId,
                    branchId=create_exit_doc.branchId,
                    quantity=exit_item.quantity,
                    averageCost=updated_product_account.averageCost,
                    createdAt=TimeTools.get_now_in_milliseconds(),
                    resultStock=updated_product_account.currentStock,
                )

                created_transactions.append(new_transaction)

            new_exit_data = create_exit_doc.model_dump()
            new_exit_data["id"] = new_exit_doc_generated_id
            new_exit_data["createdAt"] = TimeTools.get_now_in_milliseconds()

            insert_result = await ExitDocsCollection().create_exit_doc_with_session(
                new_exit_data,
                session=session,
            )

            created_transactions_data = [
                transaction.model_dump() for transaction in created_transactions
            ]
            await prd_transaction_col.create_many_product_transactions_with_session(
                created_transactions_data,
                session=session,
            )

            new_exit_doc_in_db = ExitDocInDb.model_validate(insert_result)

            return new_exit_doc_in_db, updated_product_accounts
