from repos.v1.entry_docs.models.entry_doc_model import CreateEntryDoc
from repos.v1.product_accounts import (
    ProductAccountInDb,
)
from repos.v1.product_transactions import ProductTransactionInDb
from repos.v1.product_sale_profiles import CreateProductSaleProfile
from repos.v1.product_stats import CreateProductStat
from repos.v1.entry_docs import (
    EntryDocInDb,
)

from tools import UuidTool, TimeTools, BranchesTool

from services import MongoService
from services.mongo_collections.v1 import (
    EntryDocsCollection,
    ProductTransactionsCollection,
    ProductAccountsCollection,
    ProductSaleProfilesCollection,
    ProductStatsCollection,
)


async def process_entry_doc(
    entry_doc: CreateEntryDoc,
) -> tuple[EntryDocInDb, list[ProductAccountInDb]]:
    mongo_client = MongoService().client
    prd_transaction_col = ProductTransactionsCollection()
    product_account_col = ProductAccountsCollection()
    product_stats_col = ProductStatsCollection()
    product_prof = ProductSaleProfilesCollection()

    entry_items = entry_doc.items

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            new_entry_data = entry_doc.model_dump()

            now_in_milliseconds = TimeTools.get_now_in_milliseconds()

            new_entry_data["id"] = UuidTool.generate_uuid()
            new_entry_data["createdAt"] = now_in_milliseconds

            insert_result = await EntryDocsCollection().create_entry_doc_with_session(
                new_entry_data,
                session=session,
            )

            new_entry_doc_in_db = EntryDocInDb.model_validate(insert_result)

            updated_product_accounts: list[ProductAccountInDb] = []

            created_transactions: list[ProductTransactionInDb] = []

            created_sales_profiles: list[CreateProductSaleProfile] = []
            created_product_stats: list[CreateProductStat] = []

            current_branch_in_db = BranchesTool().get_branch_by_id(entry_doc.branchId)
            if current_branch_in_db is None:
                raise Exception("Branch not found in process")

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

                created_sales_profiles.append(sale_profile)

                if current_branch_in_db.isCommerce:
                    product_stats = CreateProductStat(
                        branchId=updated_product_account.branchId,
                        productId=updated_product_account.productId,
                        startDate=now_in_milliseconds,
                        endDate=now_in_milliseconds,
                        totalUnits=0,
                        totalTransactions=0,
                        daysAnalyzed=0,
                        lastEstimation=now_in_milliseconds,
                    )
                    created_product_stats.append(product_stats)

                new_transaction = ProductTransactionInDb(
                    id=UuidTool.generate_uuid(),
                    documentId=new_entry_doc_in_db.id,
                    docNumber=new_entry_doc_in_db.docNumber,
                    type="entry",
                    subtype="entry",
                    productId=entry_item.productId,
                    branchId=entry_doc.branchId,
                    quantity=entry_item.quantity,
                    averageCost=updated_product_account.averageCost,
                    createdAt=now_in_milliseconds,
                    resultStock=updated_product_account.currentStock,
                )

                created_transactions.append(new_transaction)

            # Create sales profiles
            raw_created_sales_profiles = [
                sale_profile.model_dump() for sale_profile in created_sales_profiles
            ]

            await product_prof.bulk_create_product_sale_profiles(
                raw_created_sales_profiles,
                session=session,
            )

            # Create product stats
            if current_branch_in_db.isCommerce:
                raw_created_product_stats = [
                    product_stat.model_dump() for product_stat in created_product_stats
                ]
                await product_stats_col.bulk_create_product_stats_if_not_exist(
                    raw_created_product_stats,
                    session=session,
                )

            # Create transactions
            created_transactions_data = [
                transaction.model_dump() for transaction in created_transactions
            ]
            await prd_transaction_col.create_many_product_transactions_with_session(
                created_transactions_data,
                session=session,
            )

            return new_entry_doc_in_db, updated_product_accounts
