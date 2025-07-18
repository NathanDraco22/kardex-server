import os
from typing import Literal, Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo import IndexModel, ASCENDING, DESCENDING

DatabaseName = Literal["KardexDb"]


class MongoService:
    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(MongoService, cls).__new__(cls)
        return cls.instance

    client: AsyncIOMotorClient[dict[str, Any]]

    async def init_service(self):
        url: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        self.client = AsyncIOMotorClient(url)
        await self.create_indexes()

    def get_collection(
        self,
        collection_name: str,
        database_name: DatabaseName = "KardexDb",
    ) -> AsyncIOMotorCollection[dict[str, Any]]:
        db = self.client.get_database(database_name)
        return db.get_collection(collection_name)

    async def create_indexes(self):
        product_col = self.get_collection("Products")

        await product_col.create_indexes(
            [
                IndexModel([("id", ASCENDING)], unique=True),
                IndexModel([("sku", ASCENDING)], unique=True),
            ]
        )
