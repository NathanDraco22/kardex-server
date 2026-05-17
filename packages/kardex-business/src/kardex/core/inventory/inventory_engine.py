from typing import Any

from kardex.services.mongo_collections.v1 import (
    ProductAccountsCollection,
    ProductSaleProfilesCollection,
    ProductStatsCollection,
    ProductTransactionsCollection,
)

from .inventory_batch_transformer import (
    EntryBatchResult,
    ExitBatchResult,
)


class InventoryEngine:
    @staticmethod
    async def execute_entry(
        branch_id: str,
        batch_result: EntryBatchResult,
        session: Any,
        account_col: ProductAccountsCollection,
        profile_col: ProductSaleProfilesCollection,
        stats_col: ProductStatsCollection,
        transaction_col: ProductTransactionsCollection,
        follow_transactions: bool = True,
    ):
        if batch_result.accounts_update:
            await account_col.bulk_update_product_account_balance_with_average_cost(
                branch_id=branch_id,
                bulk_data=batch_result.accounts_update,
                session=session,
            )

        if batch_result.new_profiles:
            raw_profiles = [p.model_dump() for p in batch_result.new_profiles]
            await profile_col.bulk_create_product_sale_profiles(
                raw_profiles, session=session
            )

        if batch_result.new_stats and follow_transactions:
            raw_stats = [s.model_dump() for s in batch_result.new_stats]
            await stats_col.bulk_create_product_stats_if_not_exist(
                raw_stats, session=session
            )

        if batch_result.transactions and follow_transactions:
            raw_txs = [t.model_dump() for t in batch_result.transactions]
            await transaction_col.create_many_product_transactions_with_session(
                raw_txs, session=session
            )

    @staticmethod
    async def execute_exit(
        branch_id: str,
        batch_result: ExitBatchResult,
        session: Any,
        account_col: ProductAccountsCollection,
        transaction_col: ProductTransactionsCollection,
        follow_transactions: bool = True,
    ):
        if batch_result.stock_subtractions:
            await account_col.bulk_substract_product_account_data(
                branch_id=branch_id,
                bulk_to_substrack=batch_result.stock_subtractions,
                session=session,
            )

        if batch_result.transactions and follow_transactions:
            raw_txs = [t.model_dump() for t in batch_result.transactions]
            await transaction_col.create_many_product_transactions_with_session(
                raw_txs,
                session=session,
            )
