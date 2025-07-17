from pathlib import Path


def create_repos_directory(name: str, version: int) -> Path:
    # check "app" folder
    app_folder = Path("app")
    if not app_folder.exists():
        app_folder.mkdir()

    # check "repos" folder
    module_folder_path = app_folder / "repos"
    if not module_folder_path.exists():
        module_folder_path.mkdir()

    # check "repos/v{version}" folder
    version_folder_path = module_folder_path / f"v{version}"
    if not version_folder_path.exists():
        version_folder_path.mkdir()

    # check "repos/v{version}/{name}" folder
    output_folder_path = version_folder_path / name
    if not output_folder_path.exists():
        output_folder_path.mkdir()

    return output_folder_path


def create_generated_output_directory(name: str) -> Path:
    # check "generated" folder
    generated_folder_path = Path("generated_output")
    if not generated_folder_path.exists():
        generated_folder_path.mkdir()

    # check "generated/{name}" folder
    output_folder_path = generated_folder_path / name
    if not output_folder_path.exists():
        output_folder_path.mkdir()

    return output_folder_path
