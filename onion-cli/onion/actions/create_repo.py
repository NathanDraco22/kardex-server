from pathlib import Path
from onion.mediators import Mediator
from onion.templates.datasource_template import (
    get_data_source_template,
    get_datasource_with_collection_template,
)
from onion.templates.model_template import get_model_template
from onion.templates.repository_template import (
    get_repository_with_relative_datasource_template,
)
from onion.templates.module_init_file_template import get_init_file_template
from onion.utils.string_utils import (
    get_datasource_filename,
    get_model_filename,
    get_repository_filename,
    get_entity_name_variations,
)
from onion.utils.dir_utils import (
    create_generated_output_directory,
    create_repos_directory,
)


def create_repo(
    input_name: str,
    version: int | None = None,
    use_mongo: bool = False,
) -> None:
    output_folder_path: Path

    variations = get_entity_name_variations(input_name)
    name = variations.single_name

    if version is None:
        output_folder_path = create_generated_output_directory(name)
    else:
        output_folder_path = create_repos_directory(variations.plural_name, version)

    # check "repos/{name}_repository.py" file
    repository_file_path = output_folder_path / get_repository_filename(name)
    if not repository_file_path.exists():
        repository_file_path.touch()

    # check "data" folder
    data_folder_path = output_folder_path / "data"
    if not data_folder_path.exists():
        data_folder_path.mkdir()

    # check "models" folder
    model_folder_path = output_folder_path / "models"
    if not model_folder_path.exists():
        model_folder_path.mkdir()

    # check "data/{name}_datasource.py" file
    datasource_file_path = data_folder_path / get_datasource_filename(name)
    if not datasource_file_path.exists():
        datasource_file_path.touch()

    # check "models/{name}_model.py" file
    model_file_path = model_folder_path / get_model_filename(name)
    if not model_file_path.exists():
        model_file_path.touch()

    datasource_file_content: str
    if use_mongo:
        if version is None:
            raise ValueError("Version is required when using MongoDB.")
        datasource_file_content = get_datasource_with_collection_template(name, version)
    else:
        datasource_file_content = get_data_source_template(name)

    datasource_file_path.write_text(datasource_file_content)

    model_file_path.write_text(get_model_template(name))

    repository_file_path.write_text(
        get_repository_with_relative_datasource_template(name)
    )

    init_file_path = output_folder_path / "__init__.py"
    if not init_file_path.exists():
        init_file_path.touch()

    init_file_path.write_text(get_init_file_template(name))

    Mediator().output_folders.append(f"app/repos/v{version}/{variations.plural_name}")
