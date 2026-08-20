from kardex.services.mongo_collections.v1 import (
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
    TransfersCollection,
    AdjustEntriesCollection,
    AdjustExitsCollection,
    ExpensesCollection,
    ExpenseCategoriesCollection,
    ApiKeysCollection,
)


async def create_indexes():
    collection = ApiKeysCollection.get_instance()
    await collection.create_indexes()

    collection = CountersCollection.get_instance()
    await collection.create_indexes()

    collection = ProductsCollection.get_instance()
    await collection.create_indexes()

    collection = ClientsCollection.get_instance()
    await collection.create_indexes()

    collection = ClientTransactionsCollection.get_instance()
    await collection.create_indexes()

    collection = SuppliersCollection.get_instance()
    await collection.create_indexes()

    collection = ProductCategoriesCollection.get_instance()
    await collection.create_indexes()

    collection = ProductPricesCollection.get_instance()
    await collection.create_indexes()

    collection = EntryDocsCollection.get_instance()
    await collection.create_index()

    collection = ExitDocsCollection.get_instance()
    await collection.create_index()

    collection = ProductAccountsCollection.get_instance()
    await collection.create_index()

    collection = ProductSaleProfilesCollection.get_instance()
    await collection.create_index()

    collection = ProductTransactionsCollection.get_instance()
    await collection.create_index()

    collection = InvoicesCollection.get_instance()
    await collection.create_indexes()

    collection = OrdersCollection.get_instance()
    await collection.create_indexes()

    collection = ExpirationLogsCollection.get_instance()
    await collection.create_indexes()

    collection = DevolutionsCollection.get_instance()
    await collection.create_indexes()

    collection = DailySummariesCollection.get_instance()
    await collection.create_indexes()

    collection = ExecutiveSummariesCollection.get_instance()
    await collection.create_indexes()

    collection = ProductStatsCollection.get_instance()
    await collection.create_indexes()

    collection = TransfersCollection.get_instance()
    await collection.create_indexes()

    collection = AdjustEntriesCollection.get_instance()
    await collection.create_indexes()

    collection = AdjustExitsCollection.get_instance()
    await collection.create_indexes()

    collection = ExpensesCollection.get_instance()
    await collection.create_indexes()

    collection = ExpenseCategoriesCollection.get_instance()
    await collection.create_indexes()
