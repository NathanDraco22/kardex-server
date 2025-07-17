from string import Template
from onion.utils.string_utils import get_entity_name_variations


basic_router_template_content = Template(
    """from fastapi import APIRouter
from typing import Any

from .${plural_name}_controller import ${plural_name}_controller

${plural_name}_router = APIRouter(tags=["${plural_name}V${version}"])


@${plural_name}_router.post("")
async def create_${single_name}(body: Any) -> Any:
    return await ${plural_name}_controller.create_${single_name}(body)


@${plural_name}_router.get("")
async def get_all_${plural_name}() -> Any:
    return await ${plural_name}_controller.get_all_${plural_name}()


@${plural_name}_router.get("/{${single_name}_id}")
async def get_${single_name}_by_id(${single_name}_id: str) -> Any: 
    return await ${plural_name}_controller.get_${single_name}_by_id(${single_name}_id)


@${plural_name}_router.patch("/{${single_name}_id}")
async def update_${single_name}_by_id(${single_name}_id: str, body: Any) -> Any:
    return await ${plural_name}_controller.update_${single_name}_by_id(${single_name}_id, body)


@${plural_name}_router.delete("/{${single_name}_id}")
async def delete_${single_name}_by_id(${single_name}_id: str) -> Any:
    return await ${plural_name}_controller.delete_${single_name}_by_id(${single_name}_id)
"""
)


def get_basic_router_template(singular_entity_name: str, version: int) -> str:
    if not singular_entity_name or not isinstance(singular_entity_name, str):
        raise ValueError("name is not a valid string")

    variations = get_entity_name_variations(singular_entity_name)

    return basic_router_template_content.substitute(
        single_name=variations.single_name,
        plural_name=variations.plural_name,
        version=str(version),
    )


api_router_template_with_module_content = Template(
    """from fastapi import APIRouter

from repos.v${version}.${plural_name} import Create${Name}, Update${Name}, ${Name}InDb

from .${plural_name}_controller import ${plural_name}_controller


${plural_name}_router = APIRouter(tags=["${plural_name}V${version}"])


@${plural_name}_router.post("")
async def create_${single_name}_endpoint(body: Create${Name}) -> ${Name}InDb:
    return await ${plural_name}_controller.create_${single_name}(body)


@${plural_name}_router.get("")
async def get_all_${plural_name}_endpoint() -> list[${Name}InDb]:
    return await ${plural_name}_controller.get_all_${plural_name}()


@${plural_name}_router.get("/{${single_name}_id}")
async def get_${single_name}_by_id_endpoint(${single_name}_id: str) -> ${Name}InDb:
    return await ${plural_name}_controller.get_${single_name}_by_id(${single_name}_id)


@${plural_name}_router.patch("/{${single_name}_id}")
async def update_${single_name}_by_id_endpoint(${single_name}_id: str, body: Update${Name}) -> ${Name}InDb: 
    return await ${plural_name}_controller.update_${single_name}_by_id(${single_name}_id, body)


@${plural_name}_router.delete("/{${single_name}_id}")
async def delete_${single_name}_by_id_endpoint(${single_name}_id: str) -> ${Name}InDb:
    return await ${plural_name}_controller.delete_${single_name}_by_id(${single_name}_id)
"""
)


def get_api_router_with_module_template(singular_entity_name: str, version: int) -> str:
    if not singular_entity_name or not isinstance(singular_entity_name, str):
        raise ValueError("name is not a valid string")

    variations = get_entity_name_variations(singular_entity_name)

    return api_router_template_with_module_content.substitute(
        Name=variations.Name,
        single_name=variations.single_name,
        plural_name=variations.plural_name,
        version=str(version),
    )
