from typing import Any

from services import MongoService


class ExitDocsCollection:
    collection_name = "ExitDocs"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_exit_doc(self, exit_doc: dict) -> None:
        collection = self.__collection
        await collection.insert_one(exit_doc)

    async def fetch_all_exit_docs(self) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_exit_doc_by_id(self, exit_doc_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": exit_doc_id})
        return result

    async def fetch_exit_doc_by_doc_number(
        self, doc_number: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"docNumber": doc_number})
        return result

    async def create_exit_doc_with_session(self, exit_doc: dict, session: Any) -> None:
        collection = self.__collection
        await collection.insert_one(
            exit_doc,
            session=session,
        )
