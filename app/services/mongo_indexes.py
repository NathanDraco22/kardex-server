from services.mongo_collections.v1 import (
    ProductsCollection,
    ClientsCollection,
    SuppliersCollection,
    ProductCategoriesCollection,
)


async def create_indexes():
    collection = ProductsCollection()
    await collection.create_indexes()

    collection = ClientsCollection()
    await collection.create_indexes()

    collection = SuppliersCollection()
    await collection.create_indexes()

    collection = ProductCategoriesCollection()
    await collection.create_indexes()
