from typing import TypeVar, Type

from kardex.services import MongoService


T = TypeVar("T", bound="BaseMongoCollection")


class BaseMongoCollection:
    collection_name: str = ""
    _instance: "BaseMongoCollection|None" = None

    def __init__(self) -> None:
        mongo_service = MongoService()
        self._collection = mongo_service.get_collection(self.collection_name)

    @classmethod
    def get_instance(cls: Type[T]) -> T:
        instance_value = cls._instance
        if instance_value is None:
            cls._instance = cls()
            instance_value = cls._instance
        return instance_value  # type: ignore
