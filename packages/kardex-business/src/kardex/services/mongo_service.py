import os
from typing import Any

from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection


class MongoService:
    """Cliente Mongo unico del proceso.

    La base de datos ya no se resuelve con ``DB_NAME``: se resuelve por el
    tenant del request (``kardexCtx``) o por un ``database_name`` explicito
    (runners y pruebas). Si no hay ninguno de los dos se lanza
    ``TenantContextMissingError``.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(cls, cls).__new__(cls)
        return cls._instance

    client: AsyncMongoClient[dict[str, Any]]

    async def init_client(self) -> None:
        url: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        self.client = AsyncMongoClient(url)

    async def init_service(self) -> None:
        """Alias historico de ``init_client``. Ya no crea indices."""

        await self.init_client()

    def get_collection(
        self,
        collection_name: str,
        database_name: str | None = None,
    ) -> AsyncCollection[dict[str, Any]]:
        from kardex.kardex_config import kardexCtx
        from kardex.tools.kardex_exceptions import TenantContextMissingError

        target = database_name or kardexCtx.get().businessNickname

        if not target:
            raise TenantContextMissingError(
                "No tenant in context and no database_name provided"
            )

        db = self.client.get_database(target)
        return db.get_collection(collection_name)
