from services.mongo_collections.v1 import (
    ProductsCollection,
    CountersCollection,
    ClientsCollection,
    ClientTransactionsCollection,
    ProductCategoriesCollection,
    ProductPricesCollection,
    ProductAccountsCollection,
    ProductSaleProfilesCollection,
    InvoicesCollection,
    OrdersCollection,
    ExpirationLogsCollection,
    DevolutionsCollection,
    DailySummariesCollection,
    ExecutiveSummariesCollection,
    TransfersCollection,
    AdjustEntriesCollection,
    AdjustExitsCollection,
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

    collection = ProductCategoriesCollection()
    await collection.create_indexes()

    collection = ProductPricesCollection()
    await collection.create_indexes()

    collection = ProductAccountsCollection()
    await collection.create_index()

    collection = ProductSaleProfilesCollection()
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

    collection = TransfersCollection()
    await collection.create_indexes()

    collection = AdjustEntriesCollection()
    await collection.create_indexes()

    collection = AdjustExitsCollection()
    await collection.create_indexes()
