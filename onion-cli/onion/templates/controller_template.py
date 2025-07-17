from string import Template
from onion.utils.string_utils import get_entity_name_variations


basic_controller_template_content = Template(
    """from typing import Any


class ${Name_plural}Controller:
    async def create_${single_name}(self, body: Any) -> Any:
        # TODO: implement create
        raise NotImplementedError()

    async def get_all_${plural_name}(self) -> Any:
        # TODO: implement get all
        raise NotImplementedError()

    async def get_${single_name}_by_id(self, ${single_name}_id: str) -> Any:
        # TODO: implement get by id
        raise NotImplementedError()

    async def update_${single_name}_by_id(self, ${single_name}_id: str, body: Any) -> Any:
        # TODO: implement update
        raise NotImplementedError()

    async def delete_${single_name}_by_id(self, ${single_name}_id: str) -> Any:
        # TODO: implement delete
        raise NotImplementedError()


${plural_name}_controller = ${Name_plural}Controller()
"""
)


def get_basic_controller_template(singular_entity_name: str) -> str:
    if not singular_entity_name or not isinstance(singular_entity_name, str):
        raise ValueError("name is not a valid string")

    variations = get_entity_name_variations(singular_entity_name)

    return basic_controller_template_content.substitute(
        Name_plural=variations.Name_plural,
        single_name=variations.single_name,
        plural_name=variations.plural_name,
    )


controller_class_template_with_module_content = Template(
    """from fastapi import HTTPException, status

from repos.v${version}.${plural_name} import (
    Create${Name}, 
    Update${Name}, 
    ${Name}InDb, 
    ${Name_plural}Repository,
    ${Name_plural}DataSource,
)


class ${Name_plural}Controller:
    def __init__(self, ${plural_name}_repo: ${Name_plural}Repository) -> None:
        self.${plural_name}_repo = ${plural_name}_repo

    async def create_${single_name}(self, body: Create${Name}) -> ${Name}InDb:
        return await self.${plural_name}_repo.create_${single_name}(body)

    async def get_all_${plural_name}(self) -> list[${Name}InDb]:
        ${plural_name} = await self.${plural_name}_repo.get_all_${plural_name}()
        return ${plural_name}

    async def get_${single_name}_by_id(self, ${single_name}_id: str) -> ${Name}InDb:
        ${single_name} = await self.${plural_name}_repo.get_${single_name}_by_id(${single_name}_id)
        if ${single_name} is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="${Name} not found",
            )
        return ${single_name}

    async def update_${single_name}_by_id(self, ${single_name}_id: str, body: Update${Name}) -> ${Name}InDb:
        updated_${single_name} = await self.${plural_name}_repo.update_${single_name}_by_id(${single_name}_id, body)
        if updated_${single_name} is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="${Name} not found",
            )
        return updated_${single_name}

    async def delete_${single_name}_by_id(self, ${single_name}_id: str) -> ${Name}InDb:
        deleted_${single_name} = await self.${plural_name}_repo.delete_${single_name}_by_id(${single_name}_id)
        if deleted_${single_name} is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="${Name} not found",
            )
        return deleted_${single_name}

${plural_name}_controller = ${Name_plural}Controller(
    ${plural_name}_repo=${Name_plural}Repository(
        ${plural_name}_ds=${Name_plural}DataSource(),
    ),
)
"""
)


def get_controller_class_with_module_template(
    singular_entity_name: str,
    version: int,
) -> str:
    if not singular_entity_name or not isinstance(singular_entity_name, str):
        raise ValueError("name is not a valid string")

    variations = get_entity_name_variations(singular_entity_name)

    return controller_class_template_with_module_content.substitute(
        Name=variations.Name,
        Name_plural=variations.Name_plural,
        single_name=variations.single_name,
        plural_name=variations.plural_name,
        version=str(version),
    )
