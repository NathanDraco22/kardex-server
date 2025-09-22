from repos.v1.entry_docs.models.entry_doc_model import CreateEntryDoc
from repos.v1.product_accounts import (
    ProductAccountInDb,
)
from repos.v1.product_transactions import ProductTransactionInDb
from repos.v1.product_sale_profiles import CreateProductSaleProfile
from repos.v1.entry_docs import (
    EntryDocInDb,
)

from tools import UuidTool, TimeTools

from services import MongoService
from services.mongo_collections.v1 import (
    EntryDocsCollection,
    ProductTransactionsCollection,
    ProductAccountsCollection,
    ProductSaleProfilesCollection,
)


async def process_entry_doc(
    entry_doc: CreateEntryDoc,
) -> tuple[EntryDocInDb, list[ProductAccountInDb]]:
    mongo_client = MongoService().client
    prd_transaction_col = ProductTransactionsCollection()
    product_account_col = ProductAccountsCollection()
    product_prof = ProductSaleProfilesCollection()

    entry_items = entry_doc.items

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            new_entry_data = entry_doc.model_dump()

            new_entry_data["id"] = UuidTool.generate_uuid()
            new_entry_data["createdAt"] = TimeTools.get_now_in_milliseconds()

            insert_result = await EntryDocsCollection().create_entry_doc_with_session(
                new_entry_data,
                session=session,
            )

            new_entry_doc_in_db = EntryDocInDb.model_validate(insert_result)

            updated_product_accounts: list[ProductAccountInDb] = []

            created_transactions: list[ProductTransactionInDb] = []

            for entry_item in entry_items:
                result = await product_account_col.update_product_account_balance_data(
                    entry_item.productId,
                    entry_doc.branchId,
                    entry_item.quantity,
                    entry_item.cost,
                    session=session,
                )

                updated_product_account = ProductAccountInDb.model_validate(result)

                updated_product_accounts.append(updated_product_account)

                sale_profile = CreateProductSaleProfile(
                    branchId=updated_product_account.branchId,
                    productId=updated_product_account.productId,
                    salePrice=0,
                )
                await (
                    product_prof.create_product_sale_profile_if_not_exist_with_session(
                        sale_profile.branchId,
                        sale_profile.productId,
                        sale_profile.model_dump(),
                        session=session,
                    )
                )

                new_transaction = ProductTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    documentId=new_entry_doc_in_db.id,
                    type="entry",
                    productId=entry_item.productId,
                    branchId=entry_doc.branchId,
                    quantity=entry_item.quantity,
                    averageCost=updated_product_account.averageCost,
                    createdAt=TimeTools.get_now_in_milliseconds(),
                )

                created_transactions.append(new_transaction)

            created_transactions_data = [
                transaction.model_dump() for transaction in created_transactions
            ]
            await prd_transaction_col.create_many_product_transactions_with_session(
                created_transactions_data,
                session=session,
            )

            return new_entry_doc_in_db, updated_product_accounts
