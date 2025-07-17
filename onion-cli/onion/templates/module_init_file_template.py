from string import Template
from onion.utils.string_utils import get_entity_name_variations


init_file_template_content = Template(
    """from .data.${plural_name}_datasource import ${Name_plural}DataSource
from .models.${single_name}_model import Create${Name}, Update${Name}, ${Name}InDb
from .${plural_name}_repository import ${Name_plural}Repository

__all__ = [
    "${Name_plural}DataSource",
    "Create${Name}",
    "Update${Name}",
    "${Name}InDb",
    "${Name_plural}Repository",
]
"""
)


def get_init_file_template(singular_entity_name: str) -> str:
    if not singular_entity_name or not isinstance(singular_entity_name, str):
        raise ValueError("name is not a valid string")

    variations = get_entity_name_variations(singular_entity_name)

    return init_file_template_content.substitute(
        Name=variations.Name,
        single_name=variations.single_name,
        plural_name=variations.plural_name,
        Name_plural=variations.Name_plural,
    )
