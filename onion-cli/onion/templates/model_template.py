from string import Template
from onion.utils.string_utils import get_entity_name_variations

model_template_file_content = Template(
    """from pydantic import BaseModel


class Base${Name}(BaseModel):
    pass


class Create${Name}(Base${Name}):
    pass


class Update${Name}(BaseModel):
    pass


class ${Name}InDb(Base${Name}):
    id: str
    created_at: str
    updated_at: str
"""
)


def get_model_template(singular_name: str):
    variations = get_entity_name_variations(singular_name)
    return model_template_file_content.substitute(Name=variations.Name)
