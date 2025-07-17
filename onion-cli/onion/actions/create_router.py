from pathlib import Path
from onion.mediators import Mediator
from onion.templates.router_template import (
    get_basic_router_template,
    get_api_router_with_module_template,
)
from onion.templates.controller_template import (
    get_basic_controller_template,
    get_controller_class_with_module_template,
)
from onion.templates.version_router_template import get_version_router_file_template
from onion.utils.string_utils import (
    singular_to_plural_english,
    get_entity_name_variations,
)


def create_router(input_name: str, version: int, use_module: bool = False) -> None:
    print("Creating router...")
    name = get_entity_name_variations(input_name).single_name
    # check app folder
    app_folder = Path("app")
    if not app_folder.exists():
        app_folder.mkdir()

    # check app/routes folder
    api_folder = app_folder / "api"
    if not api_folder.exists():
        api_folder.mkdir()

    # check app/routes/v{version} folder
    version_folder = api_folder / f"v{version}"
    if not version_folder.exists():
        version_folder.mkdir()

    plural_name = singular_to_plural_english(name)

    # check app/routes/v{version}/{plural_name} folder
    module_folder = version_folder / plural_name
    if not module_folder.exists():
        module_folder.mkdir()

    # check app/routers/v{version}/{name}_router.py
    router_file = module_folder / f"{plural_name}_router.py"
    if not router_file.exists():
        router_file.touch()

    controller_file = module_folder / f"{plural_name}_controller.py"
    if not controller_file.exists():
        controller_file.touch()

    router_content: str
    controller_content: str

    if use_module:
        router_content = get_api_router_with_module_template(name, version)
        controller_content = get_controller_class_with_module_template(name, version)
    else:
        router_content = get_basic_router_template(name, version)
        controller_content = get_basic_controller_template(name)

    router_file.write_text(router_content)
    controller_file.write_text(controller_content)

    # check router.py file
    router_file = version_folder / "router.py"
    if not router_file.exists():
        router_file.touch()
        router_file.write_text(get_version_router_file_template(version))

    create_father_router_file(router_file, plural_name, version)

    Mediator().output_folders.append(f"app/api/v{version}/{plural_name}")


def create_father_router_file(router_file: Path, plural_name: str, version: int):
    import_line = (
        f"from .{plural_name}.{plural_name}_router import {plural_name}_router\n"
    )
    formatted_plural_name = plural_name.replace("_", "-")
    include_route_line = f"router_v{version}.include_router({plural_name}_router, prefix='/{formatted_plural_name}')\n"
    file = router_file.open("r")
    lines = file.readlines()
    header: str = ""
    middle: str = ""
    imports_relative_lines = []
    route_include_lines = []
    for line in lines:
        if line.startswith("from fastapi"):
            header = line
        if line.startswith("from ."):
            imports_relative_lines.append(line)
        if line.startswith("router_"):
            if "APIRouter" in line:
                middle = line
                continue
            route_include_lines.append(line)

    file.close()

    imports_relative_lines = [
        *imports_relative_lines,
        import_line,
    ]

    route_include_lines = [
        *route_include_lines,
        include_route_line,
    ]

    imports_relative_lines = set(imports_relative_lines)
    route_include_lines = set(route_include_lines)

    imports_relative_lines = list(imports_relative_lines)
    route_include_lines = list(route_include_lines)

    imports_relative_lines.sort()
    route_include_lines.sort()

    output_lines = [
        header,
        "\n",
        *imports_relative_lines,
        "\n",
        middle,
        "\n",
        *route_include_lines,
        "\n",
    ]

    file = router_file.open("w")
    file.writelines(output_lines)
    file.close()
