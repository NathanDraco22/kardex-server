from string import Template
from onion.utils.string_utils import get_entity_name_variations


data_source_template_content = Template(
    """from typing import Any


class ${Name_plural}DataSource:
    async def create_${single_name}(self, ${single_name}: dict[str, Any]) -> dict[str, Any]:
        # TODO: implement create
        raise NotImplementedError()

    async def get_all_${plural_name}(self) -> list[dict[str, Any]]:
        # TODO: implement get all
        raise NotImplementedError()

    async def get_${single_name}_by_id(self, ${single_name}_id: str) -> dict[str, Any] | None :
        # TODO: implement get by id
        raise NotImplementedError()

    async def update_${single_name}_by_id(self, ${single_name}_id:str, ${single_name}:dict[str, Any]) -> dict[str, Any] | None:
        # TODO: implement update
        raise NotImplementedError()

    async def delete_${single_name}_by_id(self, ${single_name}_id:str) -> dict[str, Any] | None:
        # TODO: implement delete
        raise NotImplementedError()
"""
)


def get_data_source_template(singular_name: str) -> str:
    if not singular_name or not isinstance(singular_name, str):
        raise ValueError("name is not a valid string")

    variations = get_entity_name_variations(singular_name)

    return data_source_template_content.substitute(
        Name_plural=variations.Name_plural,
        plural_name=variations.plural_name,
        single_name=variations.single_name,
    )


datasource_with_collection_template_content = Template(
    """from typing import Any
from typing_extensions import Self
from services.mongo_collections.v${version} import ${Name_plural}Collection


class ${Name_plural}DataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_${single_name}(self, ${single_name}: dict[str, Any]) -> dict[str, Any]:
        collection = ${Name_plural}Collection()
        await collection.create_${single_name}(${single_name})
        return ${single_name}

    async def get_all_${plural_name}(self) -> list[dict[str, Any]]:
        collection = ${Name_plural}Collection()
        return await collection.fetch_all_${plural_name}()

    async def get_${single_name}_by_id(self, ${single_name}_id: str) -> dict[str, Any] | None:
        collection = ${Name_plural}Collection()
        return await collection.fetch_${single_name}_by_id(${single_name}_id)

    async def update_${single_name}_by_id(
        self, ${single_name}_id: str, ${single_name}: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = ${Name_plural}Collection()
        return await collection.update_${single_name}_by_id(${single_name}_id, ${single_name})

    async def delete_${single_name}_by_id(self, ${single_name}_id: str) -> dict[str, Any] | None:
        collection = ${Name_plural}Collection()
        return await collection.delete_${single_name}_by_id(${single_name}_id)
"""
)


def get_datasource_with_collection_template(singular_name: str, version: int) -> str:
    if not singular_name or not isinstance(singular_name, str):
        raise ValueError("name is not a valid string")

    variations = get_entity_name_variations(singular_name)

    return datasource_with_collection_template_content.substitute(
        Name=variations.Name,
        Name_plural=variations.Name_plural,
        plural_name=variations.plural_name,
        single_name=variations.single_name,
        version=str(version),
    )
