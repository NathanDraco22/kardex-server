from .create_repo import create_repo
from .create_router import create_router


def create_router_with_module(name: str, version: int) -> None:
    create_repo(name, version, False)
    create_router(name, version, True)
