from string import Template

version_router_file_template_content = Template(
    """from fastapi import APIRouter


router_v${api_version} = APIRouter(tags=["apiV${api_version}"])


"""
)


def get_version_router_file_template(api_version: int = 1) -> str:
    if not isinstance(api_version, int) or api_version <= 0:
        raise ValueError("api_version must be a positive integer")

    return version_router_file_template_content.substitute(api_version=api_version)
