from pathlib import Path
import toml
from onion.mediators import Mediator
from onion.utils.string_utils import (
    get_mongo_collection_filename,
    get_entity_name_variations,
)
from onion.templates.mongo_collection_template import (
    get_mongo_collection_class_template,
)
from onion.utils.file_utils import gen_init

from .create_mongo_service import create_mongo_service


def create_mongo_collection(input_name: str, version: int) -> None:
    variations = get_entity_name_variations(input_name)

    name = variations.single_name

    # check "app" folder
    app_folder = Path("app")
    if not app_folder.exists():
        app_folder.mkdir()

    # check "app/services" folder
    service_folder = app_folder / "services"
    if not service_folder.exists():
        service_folder.mkdir()

    # check "app/services/mongo_service.py" file
    mongo_service_file = service_folder / "mongo_service.py"
    if not mongo_service_file.exists():
        create_mongo_service()

    mongo_collection_folder = service_folder / "mongo_collections"
    if not mongo_collection_folder.exists():
        mongo_collection_folder.mkdir()

    # check "app/services/mongo_collections/v{version}" folder
    version_folder = mongo_collection_folder / f"v{version}"
    if not version_folder.exists():
        version_folder.mkdir()

    # check "app/services/mongo_collection.py"
    mongo_collection_file = version_folder / get_mongo_collection_filename(name)
    if not mongo_collection_file.exists():
        mongo_collection_file.touch()

    mongo_collection_file.write_text(get_mongo_collection_class_template(name))

    gen_init(version_folder)

    # check config folder
    config_folder = app_folder / "config"
    if not config_folder.exists():
        config_folder.mkdir()

    # check config/onion-config.toml
    config_file = config_folder / "onion-config.toml"
    if not config_file.exists():
        config_file.touch()

    with open(config_file, "r") as f:
        data = toml.load(f)
        if "mongo-collections" not in data:
            data["mongo-collections"] = []

    data["mongo-collections"] = list(
        set(
            data["mongo-collections"] + [variations.Name_plural],
        ),
    )
    with open(config_file, "w") as f:
        toml.dump(data, f)

    with open(config_file, "r") as f:
        lines = f.readlines()

    with open(config_file, "w") as f:
        lines = [
            "# Don't edit this file manually, it's managed by Onion CLI\n",
            *lines,
        ]
        f.writelines(lines)

    Mediator().output_folders.append(
        f"app/services/mongo_collections/v{version}/{variations.plural_name}_collection.py",
    )
