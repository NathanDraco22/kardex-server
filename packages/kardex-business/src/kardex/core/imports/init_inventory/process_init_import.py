import random
from .model.product_import import ProductImport

from kardex.tools import UuidTool, TimeTools
from kardex.tools.search_tools import generate_prefixes

from kardex.repos.v1.product_accounts import ProductAccountInDb
from kardex.repos.v1.product_transactions import ProductTransactionInDb
from kardex.repos.v1.product_sale_profiles import ProductSaleProfileInDb
from kardex.repos.v1.product_stats import CreateProductStat
from kardex.repos.v1.products import ProductInDb
from kardex.repos.v1.adjust_entries import AdjustEntryInDb
from kardex.repos.v1.common.models import UserInfo, EntryItem

from kardex.services import MongoService


from kardex.services.mongo_collections.v1 import (
    ProductsCollection,
    ProductAccountsCollection,
    ProductSaleProfilesCollection,
    ProductStatsCollection,
    ProductTransactionsCollection,
    AdjustEntriesCollection,
)


async def process_init_import(branch_id: str, products: list[ProductImport]) -> None:
    product_col: ProductsCollection = ProductsCollection.get_instance()
    adjust_entry_doc_col: AdjustEntriesCollection = (
        AdjustEntriesCollection.get_instance()
    )
    account_col: ProductAccountsCollection = ProductAccountsCollection.get_instance()
    profile_col: ProductSaleProfilesCollection = (
        ProductSaleProfilesCollection.get_instance()
    )
    stats_col: ProductStatsCollection = ProductStatsCollection.get_instance()
    transaction_col: ProductTransactionsCollection = (
        ProductTransactionsCollection.get_instance()
    )

    now_milliseconds = TimeTools.get_now_in_milliseconds()

    new_products: list[ProductInDb] = []
    new_product_accounts: list[ProductAccountInDb] = []
    new_product_sale_profiles: list[ProductSaleProfileInDb] = []
    new_product_stats: list[CreateProductStat] = []
    new_product_transactions: list[ProductTransactionInDb] = []
    new_product_entry_items: list[EntryItem] = []

    for import_product in products:
        import_product.id = UuidTool.generate_uuid()
        product = ProductInDb(
            **import_product.model_dump(),
            createdAt=now_milliseconds,
        )

        new_products.append(product)

        product_account = ProductAccountInDb(
            productId=product.id,
            branchId=branch_id,
            currentStock=import_product.quantity,
            averageCost=import_product.cost,
            lastCost=import_product.cost,
            maximumCost=import_product.cost,
            createdAt=now_milliseconds,
        )

        new_product_accounts.append(product_account)

        product_sale_profile = ProductSaleProfileInDb(
            productId=product.id,
            branchId=branch_id,
            salePrice=import_product.price,
            salePrice2=import_product.price2,
            salePrice3=import_product.price3,
            updatedAt=now_milliseconds,
        )

        new_product_sale_profiles.append(product_sale_profile)

        product_stat = CreateProductStat(
            productId=product.id,
            branchId=branch_id,
            startDate=now_milliseconds,
            endDate=now_milliseconds,
            totalUnits=0,
            totalTransactions=0,
            daysAnalyzed=0,
            lastEstimation=now_milliseconds,
        )

        new_product_stats.append(product_stat)

        product_transaction = ProductTransactionInDb(
            id=UuidTool.generate_uuid(),
            type="entry",
            subtype="adjustment",
            docNumber="0000",
            documentId="0000",
            quantity=import_product.quantity,
            averageCost=import_product.cost,
            resultStock=import_product.quantity,
            productId=product.id,
            branchId=branch_id,
            createdAt=now_milliseconds,
        )

        new_product_transactions.append(product_transaction)

        entry_item = EntryItem(
            productId=product.id,
            productName=product.name,
            code=product.code,
            brandName=product.brandName,
            unitName=product.unitName,
            cost=import_product.cost,
            quantity=import_product.quantity,
            expirationDate=None,
        )

        new_product_entry_items.append(entry_item)

    # Mongo session
    client = MongoService().client

    new_product_data = []

    for product in new_products:
        data = product.model_dump()
        data["searchPrefixes"] = generate_prefixes(product.name)
        new_product_data.append(data)

    new_product_accounts_data = [
        product_account.model_dump() for product_account in new_product_accounts
    ]

    new_product_sale_profiles_data = [
        product_sale_profile.model_dump()
        for product_sale_profile in new_product_sale_profiles
    ]

    new_product_stats_data = [
        product_stat.model_dump() for product_stat in new_product_stats
    ]

    new_product_transactions_data = [
        product_transaction.model_dump()
        for product_transaction in new_product_transactions
    ]

    new_init_entry_doc = AdjustEntryInDb(
        id="0000",
        branchId=branch_id,
        docNumber="0000",
        description="Inventario inicial",
        createdAt=now_milliseconds,
        items=new_product_entry_items,
        createdBy=UserInfo(
            id="S0000",
            name="Inventario inicial",
        ),
    )

    entry_doc_data = new_init_entry_doc.model_dump()

    async with client.start_session() as session:
        async with await session.start_transaction():
            await adjust_entry_doc_col.create_adjust_entry_with_session(
                entry_doc_data,
                session=session,
            )
            await product_col.create_many_products(
                new_product_data,
                session=session,
            )
            await account_col.create_many_product_accounts(
                new_product_accounts_data,
                session=session,
            )
            await profile_col.bulk_create_product_sale_profiles(
                new_product_sale_profiles_data, session=session
            )
            await stats_col.bulk_create_product_stats_if_not_exist(
                new_product_stats_data, session=session
            )

            await transaction_col.create_many_product_transactions_with_session(
                new_product_transactions_data, session=session
            )


async def process_inventory_import(
    branch_id: str, products: list[ProductImport]
) -> None:
    product_col: ProductsCollection = ProductsCollection.get_instance()
    adjust_entry_doc_col: AdjustEntriesCollection = (
        AdjustEntriesCollection.get_instance()
    )
    account_col: ProductAccountsCollection = ProductAccountsCollection.get_instance()
    profile_col: ProductSaleProfilesCollection = (
        ProductSaleProfilesCollection.get_instance()
    )
    stats_col: ProductStatsCollection = ProductStatsCollection.get_instance()
    transaction_col: ProductTransactionsCollection = (
        ProductTransactionsCollection.get_instance()
    )

    now_milliseconds = TimeTools.get_now_in_milliseconds()

    new_products: list[ProductInDb] = []
    new_product_accounts: list[ProductAccountInDb] = []
    new_product_sale_profiles: list[ProductSaleProfileInDb] = []
    new_product_stats: list[CreateProductStat] = []
    new_product_transactions: list[ProductTransactionInDb] = []
    new_product_entry_items: list[EntryItem] = []

    adjust_doc_id = ""

    number = random.randint(1, 100000)

    adjust_doc_id = "I" + str(number).zfill(6)

    for import_product in products:
        import_product.id = UuidTool.generate_uuid()
        product = ProductInDb(
            **import_product.model_dump(),
            createdAt=now_milliseconds,
        )

        new_products.append(product)

        product_account = ProductAccountInDb(
            productId=product.id,
            branchId=branch_id,
            currentStock=import_product.quantity,
            averageCost=import_product.cost,
            lastCost=import_product.cost,
            maximumCost=import_product.cost,
            createdAt=now_milliseconds,
        )

        new_product_accounts.append(product_account)

        product_sale_profile = ProductSaleProfileInDb(
            productId=product.id,
            branchId=branch_id,
            salePrice=import_product.price,
            salePrice2=import_product.price2,
            salePrice3=import_product.price3,
            updatedAt=now_milliseconds,
        )

        new_product_sale_profiles.append(product_sale_profile)

        product_stat = CreateProductStat(
            productId=product.id,
            branchId=branch_id,
            startDate=now_milliseconds,
            endDate=now_milliseconds,
            totalUnits=0,
            totalTransactions=0,
            daysAnalyzed=0,
            lastEstimation=now_milliseconds,
        )

        new_product_stats.append(product_stat)

        product_transaction = ProductTransactionInDb(
            id=UuidTool.generate_uuid(),
            type="entry",
            subtype="adjustment",
            docNumber=adjust_doc_id,
            documentId=adjust_doc_id,
            quantity=import_product.quantity,
            averageCost=import_product.cost,
            resultStock=import_product.quantity,
            productId=product.id,
            branchId=branch_id,
            createdAt=now_milliseconds,
        )

        new_product_transactions.append(product_transaction)

        entry_item = EntryItem(
            productId=product.id,
            productName=product.name,
            code=product.code,
            brandName=product.brandName,
            unitName=product.unitName,
            cost=import_product.cost,
            quantity=import_product.quantity,
            expirationDate=None,
        )

        new_product_entry_items.append(entry_item)

    # Mongo session
    client = MongoService().client

    new_product_data = []

    for product in new_products:
        data = product.model_dump()
        data["searchPrefixes"] = generate_prefixes(product.name)
        new_product_data.append(data)

    new_product_accounts_data = [
        product_account.model_dump() for product_account in new_product_accounts
    ]

    new_product_sale_profiles_data = [
        product_sale_profile.model_dump()
        for product_sale_profile in new_product_sale_profiles
    ]

    new_product_stats_data = [
        product_stat.model_dump() for product_stat in new_product_stats
    ]

    new_product_transactions_data = [
        product_transaction.model_dump()
        for product_transaction in new_product_transactions
    ]

    new_init_entry_doc = AdjustEntryInDb(
        id=adjust_doc_id,
        branchId=branch_id,
        docNumber=adjust_doc_id,
        description="Importación de inventario",
        createdAt=now_milliseconds,
        items=new_product_entry_items,
        createdBy=UserInfo(
            id="S0000",
            name="Inventario inicial",
        ),
    )

    entry_doc_data = new_init_entry_doc.model_dump()

    async with client.start_session() as session:
        async with await session.start_transaction():
            await adjust_entry_doc_col.create_adjust_entry_with_session(
                entry_doc_data,
                session=session,
            )
            await product_col.create_many_products(
                new_product_data,
                session=session,
            )
            await account_col.create_many_product_accounts(
                new_product_accounts_data,
                session=session,
            )
            await profile_col.bulk_create_product_sale_profiles(
                new_product_sale_profiles_data, session=session
            )
            await stats_col.bulk_create_product_stats_if_not_exist(
                new_product_stats_data, session=session
            )

            await transaction_col.create_many_product_transactions_with_session(
                new_product_transactions_data, session=session
            )
