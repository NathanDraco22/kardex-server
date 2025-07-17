from typer import Typer
from typer import Argument, Option
from rich import print
from onion.mediators import Mediator
from onion.actions.create_repo import create_repo
from onion.actions.create_repo_with_mongo_collection import (
    create_repo_with_mongo_collection,
)
from onion.actions.create_router import create_router
from onion.actions.create_router_with_module import create_router_with_module
from onion.actions.create_router_with_repo_with_mongo import (
    create_router_with_repo_with_mongo,
)

from onion.utils.string_utils import is_plural_english

app = Typer()


@app.command(help="create router, controller and module")
def crud(
    names: list[str] = Argument(help="module name or list of names"),
    version: int = Option(help="version example: 1"),
):
    for name in names:
        if is_plural_english(name):
            raise Exception("plural names are not allowed")

    for name in names:
        create_router_with_module(name, version)

    print("[green]router and module created :heavy_check_mark:[/green]")
    for folder in Mediator().output_folders:
        print(f"[yellow]{folder}[/yellow]")


@app.command(help="create router, controller, module, mongo collection")
def crud_mongo(
    names: list[str] = Argument(help="module name or list of names"),
    version: int = Option(help="version example: 1"),
):
    for name in names:
        if is_plural_english(name):
            raise Exception("plural names are not allowed")

    for name in names:
        create_router_with_repo_with_mongo(name, version)

    print(
        "[green]router, repository and mongo collection created :heavy_check_mark:[/green]"
    )
    for folder in Mediator().output_folders:
        print(f"[yellow]{folder}[/yellow]")


@app.command(help="create a module")
def repo(
    names: list[str] = Argument(help="module name"),
    version: int = Option(help="version example: 1"),
):
    for name in names:
        if is_plural_english(name):
            raise Exception("plural names are not allowed")

    for name in names:
        create_repo(name, version)

    print("[green]repository created :heavy_check_mark:[/green]")
    for folder in Mediator().output_folders:
        print(f"[yellow]{folder}[/yellow]")


@app.command(help="create a module with mongo collection")
def repo_mongo(
    names: list[str] = Argument(help="module name"),
    version: int = Option(help="version example: 1"),
):
    for name in names:
        if is_plural_english(name):
            raise Exception("plural names are not allowed")

    for name in names:
        create_repo_with_mongo_collection(name, version)

    print("[green]repository with mongo collection created :heavy_check_mark:[/green]")
    for folder in Mediator().output_folders:
        print(f"[yellow]{folder}[/yellow]")


@app.command(help="create a router")
def router(
    names: list[str] = Argument(help="router name"),
    version: int = Option(help="version example: 1"),
):
    for name in names:
        if is_plural_english(name):
            raise Exception("plural names are not allowed")

    for name in names:
        create_router(name, version)

    print("[green]router created :heavy_check_mark:[/green]")

    for folder in Mediator().output_folders:
        print(f"[yellow]{folder}[/yellow]")
