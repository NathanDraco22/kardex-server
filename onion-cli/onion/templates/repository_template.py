from string import Template
from onion.utils.string_utils import get_entity_name_variations


repository_template_content = Template(
    """
class ${Name_plural}Repository:
    async def create_${single_name}(self, create_${single_name}: Create${Name}) -> ${Name}InDb:
        # TODO: implement create
        raise NotImplementedError()

    async def get_all_${plural_name}(self) -> list[${Name}InDb]:
        # TODO: implement get all
        raise NotImplementedError()

    async def get_${single_name}_by_id(self, ${single_name}_id: str) -> ${Name}InDb | None :
        # TODO: implement get by id
        raise NotImplementedError()

    async def update_${single_name}_by_id(self, ${single_name}_id: str, ${single_name}: Update${Name}) -> ${Name}InDb | None:
        # TODO: implement update
        raise NotImplementedError()

    async def delete_${single_name}_by_id(self, ${single_name}_id: str) -> ${Name}InDb | None:
        # TODO: implement delete
        raise NotImplementedError()
"""
)


def get_repository_template(singular_name: str) -> str:
    if not singular_name or not isinstance(singular_name, str):
        raise ValueError("name is not a valid string")

    variations = get_entity_name_variations(singular_name)

    return repository_template_content.substitute(
        Name=variations.Name,
        Name_plural=variations.Name_plural,
        plural_name=variations.plural_name,
        single_name=variations.single_name,
    )


repository_with_relative_datasource_template_content = Template(
    """from .data.${plural_name}_datasource import ${Name_plural}DataSource
from .models.${single_name}_model import Create${Name}, Update${Name}, ${Name}InDb


class ${Name_plural}Repository:
    def __init__(self, ${plural_name}_ds: ${Name_plural}DataSource):
        self.${plural_name}_ds = ${plural_name}_ds

    async def create_${single_name}(self, create_${single_name}: Create${Name}) -> ${Name}InDb:
        # TODO: implement create
        raise NotImplementedError()

    async def get_all_${plural_name}(self) -> list[${Name}InDb]:
        results = await self.${plural_name}_ds.get_all_${plural_name}()
        models = [${Name}InDb.model_validate(result) for result in results]
        return models

    async def get_${single_name}_by_id(self, ${single_name}_id: str) -> ${Name}InDb | None :
        result = await self.${plural_name}_ds.get_${single_name}_by_id(${single_name}_id)
        
        if result is None:
            return None
        
        return ${Name}InDb.model_validate(result)

    async def update_${single_name}_by_id(self, ${single_name}_id: str, ${single_name}: Update${Name}) -> ${Name}InDb | None:
        # TODO: implement update
        raise NotImplementedError()

    async def delete_${single_name}_by_id(self, ${single_name}_id: str) -> ${Name}InDb | None:
        result = await self.${plural_name}_ds.delete_${single_name}_by_id(${single_name}_id)
        
        if result is None:
            return None
        
        return ${Name}InDb.model_validate(result)
"""
)


def get_repository_with_relative_datasource_template(singular_name: str) -> str:
    if not singular_name or not isinstance(singular_name, str):
        raise ValueError("name is not a valid string")

    variations = get_entity_name_variations(singular_name)

    return repository_with_relative_datasource_template_content.substitute(
        Name=variations.Name,
        Name_plural=variations.Name_plural,
        plural_name=variations.plural_name,
        single_name=variations.single_name,
    )
