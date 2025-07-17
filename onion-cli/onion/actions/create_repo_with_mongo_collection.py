from .create_mongo_collection import create_mongo_collection
from .create_repo import create_repo


def create_repo_with_mongo_collection(name: str, version: int) -> None:
    create_mongo_collection(name, version)
    create_repo(name, version, True)
