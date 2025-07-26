from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import ExitDocsCollection


class ExitDocsDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_exit_doc(self, exit_doc: dict[str, Any]) -> dict[str, Any]:
        collection = ExitDocsCollection()
        await collection.create_exit_doc(exit_doc)
        return exit_doc

    async def get_all_exit_docs(self) -> list[dict[str, Any]]:
        collection = ExitDocsCollection()
        return await collection.fetch_all_exit_docs()

    async def get_exit_doc_by_id(self, exit_doc_id: str) -> dict[str, Any] | None:
        collection = ExitDocsCollection()
        return await collection.fetch_exit_doc_by_id(exit_doc_id)

    async def get_exit_doc_by_doc_number(
        self, doc_number: str
    ) -> dict[str, Any] | None:
        collection = ExitDocsCollection()
        return await collection.fetch_exit_doc_by_doc_number(doc_number)
