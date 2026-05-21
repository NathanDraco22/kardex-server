from kardex.tools import UuidTool, TimeTools, BranchesTool, BranchNotFound
from kardex.core.inventory import (
    InventoryBatchTransformer,
    InventoryEntryBatchItem,
    InventoryEngine,
)
from kardex.repos.v1.entry_docs.models.entry_doc_model import CreateEntryDoc
from kardex.repos.v1.entry_docs import EntryDocInDb
from kardex.repos.v1.product_accounts import ProductAccountInDb


from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import (
    EntryDocsCollection,
    ProductTransactionsCollection,
    ProductAccountsCollection,
    ProductSaleProfilesCollection,
    ProductStatsCollection,
)


async def process_entry_doc(
    entry_doc: CreateEntryDoc,
    follow_transactions: bool,
) -> EntryDocInDb:
    mongo_client = MongoService().client

    # Colecciones
    product_account_col = ProductAccountsCollection.get_instance()
    product_stats_col = ProductStatsCollection.get_instance()
    product_prof_col = ProductSaleProfilesCollection.get_instance()
    prd_transaction_col = ProductTransactionsCollection.get_instance()
    entry_docs_col = EntryDocsCollection.get_instance()

    # Tools
    branches_tool = BranchesTool()

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            current_branch_in_db = branches_tool.get_branch_by_id(entry_doc.branchId)

            if current_branch_in_db is None:
                raise BranchNotFound("Branch not found in process")

            now_in_milliseconds = TimeTools.get_now_in_milliseconds()

            new_entry_data = entry_doc.model_dump()
            new_entry_data["id"] = UuidTool.generate_uuid()
            new_entry_data["createdAt"] = now_in_milliseconds

            insert_result = await entry_docs_col.create_entry_doc_with_session(
                new_entry_data,
                session=session,
            )
            new_entry_doc_in_db = EntryDocInDb.model_validate(insert_result)

            batch_items = [
                InventoryEntryBatchItem(
                    product_id=item.productId,
                    quantity=item.quantity,
                    unit_cost=item.cost,
                )
                for item in entry_doc.items
            ]

            # 4. OBTENER CUENTAS ACTUALES (Snapshot Read)
            product_ids = [item.product_id for item in batch_items]

            existing_accounts_data = (
                await product_account_col.get_accounts_by_branch_id(
                    branch_id=entry_doc.branchId,
                    product_ids=product_ids,
                    session=session,
                )
            )

            accounts_dict = {
                acc["productId"]: ProductAccountInDb.model_validate(acc)
                for acc in existing_accounts_data
            }

            batch_result = InventoryBatchTransformer.prepare_entry(
                branch_id=entry_doc.branchId,
                is_commerce_branch=current_branch_in_db.isCommerce,
                items=batch_items,
                existing_accounts_dict=accounts_dict,
                document_id=new_entry_doc_in_db.id,
                doc_number=new_entry_doc_in_db.docNumber,
                tx_type="entry",
                tx_subtype="entry",
            )

            await InventoryEngine.execute_entry(
                branch_id=entry_doc.branchId,
                batch_result=batch_result,
                session=session,
                account_col=product_account_col,
                profile_col=product_prof_col,
                stats_col=product_stats_col,
                transaction_col=prd_transaction_col,
                follow_transactions=follow_transactions,
            )

            return new_entry_doc_in_db
