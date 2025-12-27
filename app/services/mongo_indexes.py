from services.mongo_collections.v1 import (
    ProductsCollection,
    CountersCollection,
    ClientsCollection,
    ClientTransactionsCollection,
    SuppliersCollection,
    ProductCategoriesCollection,
    ProductPricesCollection,
    EntryDocsCollection,
    ExitDocsCollection,
    ProductAccountsCollection,
    ProductSaleProfilesCollection,
    ProductTransactionsCollection,
    InvoicesCollection,
    OrdersCollection,
    ExpirationLogsCollection,
    DevolutionsCollection,
    DailySummariesCollection,
    ExecutiveSummariesCollection,
    ProductStatsCollection,
)


async def create_indexes():
    collection = CountersCollection()
    await collection.create_indexes()

    collection = ProductsCollection()
    await collection.create_indexes()

    collection = ClientsCollection()
    await collection.create_indexes()

    collection = ClientTransactionsCollection()
    await collection.create_indexes()

    collection = SuppliersCollection()
    await collection.create_indexes()

    collection = ProductCategoriesCollection()
    await collection.create_indexes()

    collection = ProductPricesCollection()
    await collection.create_indexes()

    collection = EntryDocsCollection()
    await collection.create_index()

    collection = ExitDocsCollection()
    await collection.create_index()

    collection = ProductAccountsCollection()
    await collection.create_index()

    collection = ProductSaleProfilesCollection()
    await collection.create_index()

    collection = ProductTransactionsCollection()
    await collection.create_index()

    collection = InvoicesCollection()
    await collection.create_indexes()

    collection = OrdersCollection()
    await collection.create_indexes()

    collection = ExpirationLogsCollection()
    await collection.create_indexes()

    collection = DevolutionsCollection()
    await collection.create_indexes()

    collection = DailySummariesCollection()
    await collection.create_indexes()

    collection = ExecutiveSummariesCollection()
    await collection.create_indexes()

    collection = ProductStatsCollection()
    await collection.create_indexes()
