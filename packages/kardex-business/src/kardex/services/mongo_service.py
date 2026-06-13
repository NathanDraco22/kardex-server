import os
from typing import Literal, Any

from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection

DatabaseName = Literal["LedgerDB"]


class MongoService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(cls, cls).__new__(cls)
        return cls._instance

    client: AsyncMongoClient[dict[str, Any]]

    async def init_service(self):
        url: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        self.client = AsyncMongoClient(url)
        await self.create_indexes()

    def get_collection(
        self,
        collection_name: str,
        database_name: DatabaseName = "LedgerDB",
    ) -> AsyncCollection[dict[str, Any]]:
        current_db_name = os.getenv("DB_NAME", database_name)
        db = self.client.get_database(current_db_name)
        return db.get_collection(collection_name)

    async def create_indexes(self):
        pass
