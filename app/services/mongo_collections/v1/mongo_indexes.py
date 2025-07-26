from services.mongo_collections.v1 import ProductsCollection


async def create_indexes():
    collection = ProductsCollection()
    await collection.create_indexes()
