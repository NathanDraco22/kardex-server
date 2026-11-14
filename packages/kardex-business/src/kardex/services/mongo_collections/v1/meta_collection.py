import os
from typing import Any

from kardex.services import BaseMongoCollection
from kardex.tools import TimeTools

TENANT_META_ID = "tenant"
TENANT_META_KIND = "kardex-tenant"
TENANT_SCHEMA_VERSION = 1


def get_app_version() -> str:
    return os.getenv("APP_VERSION", "1.0.0")


class MetaCollection(BaseMongoCollection):
    """Ficha tecnica de la base de datos de un tenant.

    ``Meta`` es metadata tecnica (version de indices, estado de
    aprovisionamiento). La configuracion de negocio sigue en ``CoreSettings`` y
    ``AppSettings``. No se consulta en el camino caliente de un request.
    """

    collection_name = "Meta"

    async def read_tenant_meta(self) -> dict[str, Any] | None:
        collection = self._collection
        return await collection.find_one({"_id": TENANT_META_ID})

    async def write_tenant_meta(self, meta: dict[str, Any]) -> None:
        collection = self._collection
        now = TimeTools.get_now_in_milliseconds()
        document = {key: value for key, value in meta.items() if key != "_id"}
        await collection.update_one(
            {"_id": TENANT_META_ID},
            {
                "$set": document,
                "$setOnInsert": {"createdAt": now},
            },
            upsert=True,
        )


def build_tenant_meta(
    nickname: str,
    is_provisioned: bool,
    indexes_version: int,
) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "_id": TENANT_META_ID,
        "kind": TENANT_META_KIND,
        "nickname": nickname,
        "schemaVersion": TENANT_SCHEMA_VERSION,
        "indexesVersion": indexes_version,
        "isProvisioned": is_provisioned,
        "appVersion": get_app_version(),
    }

    if is_provisioned:
        meta["provisionedAt"] = TimeTools.get_now_in_milliseconds()

    return meta


async def write_tenant_meta_document(
    nickname: str,
    is_provisioned: bool,
    indexes_version: int,
) -> None:
    """Escribe ``Meta`` en la base del ``nickname`` indicado."""

    collection = MetaCollection.get_instance(nickname)
    await collection.write_tenant_meta(
        build_tenant_meta(nickname, is_provisioned, indexes_version)
    )
