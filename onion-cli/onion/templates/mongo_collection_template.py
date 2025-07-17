from string import Template
from onion.utils.string_utils import get_entity_name_variations


collection_class_template_content = Template(
    """from typing import Any

from pymongo import ReturnDocument
from services import MongoService


class ${Name_plural}Collection:
    collection_name = "${Name_plural}"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_${single_name}(self, ${single_name}: dict) -> None:
        collection = self.__collection
        await collection.insert_one(${single_name})

    async def fetch_all_${plural_name}(self) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_${single_name}_by_id(self, ${single_name}_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": ${single_name}_id})
        return result

    async def update_${single_name}_by_id(
        self,
        ${single_name}_id: str,
        ${single_name}: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": ${single_name}_id},
            {"$$set": ${single_name}},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_${single_name}_by_id(self, ${single_name}_id: str) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one_and_delete({"id": ${single_name}_id})
        return result
"""
)


def get_mongo_collection_class_template(singular_entity_name: str) -> str:
    if not singular_entity_name or not isinstance(singular_entity_name, str):
        raise ValueError("name is not a valid string")

    variations = get_entity_name_variations(singular_entity_name)

    return collection_class_template_content.substitute(
        Name_plural=variations.Name_plural,
        single_name=variations.single_name,
        plural_name=variations.plural_name,
    )
