from dataclasses import dataclass
from typing_extensions import Self
from services.mongo_collections.v1 import BranchesCollection


@dataclass
class Etag:
    key: str
    value: str


class EtagTool:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    _tags: dict[str, Etag] = {}

    def set_tag(self, key: str, value: str):
        self._tags[key] = Etag(key, value)

    def get_etag(self, key: str) -> Etag | None:
        return self._tags.get(key)

    async def update_branches_etags(self):
        collection = BranchesCollection()
        count = await collection._collection.estimated_document_count()
        self.set_tag("branches_count", str(count))

    def get_branches_etag(self) -> Etag | None:
        return self._tags.get("branches_count")
