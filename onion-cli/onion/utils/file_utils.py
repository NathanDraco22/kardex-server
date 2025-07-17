import ast
from pathlib import Path
from typing import Generator, Any


def remove_file_suffix(file_path: Path) -> Path:
    return file_path.with_suffix("")


def get_py_files_from_dir(dir_path: Path) -> Generator[Path, None, None]:
    files_path = list(dir_path.iterdir())
    files_path.sort()
    for res in files_path:
        if res.is_file():
            if res.name == "__init__.py":
                continue
            if res.suffix != ".py":
                continue
            yield res


def get_classes_definitions_from_file(file_path: Path) -> Generator[str, None, None]:
    opened_file = file_path.open("r")
    readed_file = opened_file.read()
    result_tree = ast.parse(readed_file)
    def_nodes = ast.walk(result_tree)

    for node in def_nodes:
        if isinstance(node, ast.ClassDef):
            yield node.name


def mappers_files_clases(files_path: list[Path]) -> dict[str, list[str]]:
    data_map: dict[str, list[Any]] = {}
    for file in files_path:
        no_sufix_path = remove_file_suffix(file)
        classes = get_classes_definitions_from_file(file)
        data_map[no_sufix_path.name] = []
        for class_name in classes:
            data_map[no_sufix_path.name].append(class_name)

    return data_map


def create_init_file_lines(
    data_map: dict[str, list[str]],
) -> list[str]:
    imports_lines: list[str] = []
    all_imports_lines: list[str] = []

    for key, value in data_map.items():
        import_classes = ",".join(value)
        imports_lines.append(f"from .{key} import {import_classes}\n")
        for class_name in value:
            all_imports_lines.append(f'    "{class_name}",\n')

    init_file_lines = [
        *imports_lines,
        "\n",
        "__all__ = [",
        "\n",
        *all_imports_lines,
        "]",
        "\n",
    ]

    return init_file_lines


def gen_init_from_files(init_dir_path: Path, files_path: list[Path]):
    data_map = mappers_files_clases(files_path)

    init_file_lines = create_init_file_lines(data_map)

    init_file = init_dir_path / "__init__.py"
    opened_file = init_file.open("w")
    opened_file.writelines(init_file_lines)
    opened_file.close()


def gen_init(path: Path):
    path_generarator = get_py_files_from_dir(path)

    files_path = list(path_generarator)

    data_map = mappers_files_clases(files_path)

    init_file_lines = create_init_file_lines(data_map)

    init_file = path / "__init__.py"
    opened_file = init_file.open("w")
    opened_file.writelines(init_file_lines)
    opened_file.close()
