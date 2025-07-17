from .create_mongo_collection import create_mongo_collection
from .create_repo import create_repo
from .create_router import create_router


def create_router_with_repo_with_mongo(name: str, version: int) -> None:
    create_mongo_collection(name, version)
    create_repo(name, version, True)
    create_router(name, version, True)
