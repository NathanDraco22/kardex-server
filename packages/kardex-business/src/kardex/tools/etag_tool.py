from dataclasses import dataclass



@dataclass
class Etag:
    key: str
    value: str


class EtagTool:
    _instance: "EtagTool|None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(cls, cls).__new__(cls)
        return cls._instance

    _tags: dict[str, Etag] = {}

    def set_last_update_branch_etag(self, value: str):
        self._tags["last_update_branch"] = Etag("last_update_branch", value)

    def set_tag(self, key: str, value: str):
        self._tags[key] = Etag(key, value)

    def get_etag(self, key: str) -> Etag | None:
        return self._tags.get(key)

    async def update_branches_etags(self):
        from kardex.services.mongo_collections.v1 import BranchesCollection

        collection = BranchesCollection.get_instance()
        count = await collection._collection.estimated_document_count()
        self.set_tag("branches_count", str(count))

    def get_branches_etag(self) -> Etag | None:
        branches_count = self._tags.get("branches_count")
        last_update_branch = self._tags.get("last_update_branch")
        branches_count_value = (
            branches_count.value if branches_count is not None else "-"
        )
        last_update_branch_value = (
            last_update_branch.value if last_update_branch is not None else "-"
        )
        return Etag(
            "branches_count",
            str(branches_count_value) + "_" + str(last_update_branch_value),
        )

    def set_projection_file_etag(self, value: str):
        self._tags["projection"] = Etag("projection", value)

    def get_projection_file_etag(self) -> Etag | None:
        return self._tags.get("projection")

    def estimation_etag(self, value: str):
        self._tags["estimation"] = Etag("estimation", value)

    def get_estimation_etag(self) -> Etag | None:
        return self._tags.get("estimation")
