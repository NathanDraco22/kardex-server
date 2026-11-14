import sys
from pathlib import Path

import pytest
from pymongo import AsyncMongoClient

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import MetaCollection
from kardex.services.mongo_collections.v1.meta_collection import (
    TENANT_META_KIND,
    write_tenant_meta_document,
)
from kardex.services.mongo_indexes import (
    ensure_indexes_for_tenant,
    get_target_indexes_version,
)
from test.mongo_test_utils import mongo_available, mongo_url
from kardex.core.tenant.migrate_tenants import (
    list_tenant_databases,
    parse_args,
    run,
)

pytestmark = pytest.mark.skipif(
    not mongo_available(),
    reason="MongoDB no disponible: se omite la prueba del runner",
)

TENANT = "mt_test_migrate"
FOREIGN = "mt_test_foreign"
LEGACY = "mt_test_legacy"


async def _service() -> MongoService:
    service = MongoService()
    if not hasattr(service, "client"):
        await service.init_client()
    return service


async def _drop_databases() -> None:
    service = await _service()
    for name in (TENANT, FOREIGN, LEGACY):
        await service.client.drop_database(name)


@pytest.mark.asyncio
async def test_ensure_indexes_applies_when_version_is_behind():
    await _drop_databases()

    try:
        await write_tenant_meta_document(TENANT, False, 0)

        action = await ensure_indexes_for_tenant(TENANT)

        meta = await MetaCollection.get_instance(TENANT).read_tenant_meta()

        assert action == "updated"
        assert meta is not None
        assert meta["isProvisioned"] is True
        assert meta["indexesVersion"] == get_target_indexes_version()
    finally:
        await _drop_databases()


@pytest.mark.asyncio
async def test_ensure_indexes_skips_when_version_matches():
    await _drop_databases()

    try:
        target = get_target_indexes_version()
        await write_tenant_meta_document(TENANT, True, target)

        assert await ensure_indexes_for_tenant(TENANT) == "skipped"
    finally:
        await _drop_databases()


@pytest.mark.asyncio
async def test_ensure_indexes_does_not_downgrade_newer_database():
    await _drop_databases()

    try:
        newer = get_target_indexes_version() + 1
        await write_tenant_meta_document(TENANT, True, newer)

        assert await ensure_indexes_for_tenant(TENANT) == "skipped-newer"

        meta = await MetaCollection.get_instance(TENANT).read_tenant_meta()
        assert meta is not None
        assert meta["indexesVersion"] == newer
    finally:
        await _drop_databases()


@pytest.mark.asyncio
async def test_runner_enumerates_only_kardex_tenants():
    await _drop_databases()

    try:
        await write_tenant_meta_document(TENANT, True, 1)

        client: AsyncMongoClient = AsyncMongoClient(mongo_url())
        try:
            await client[FOREIGN]["Meta"].insert_one(
                {"_id": "tenant", "kind": "otra-cosa"}
            )
            await client["mt_test_without_meta"]["Product"].insert_one({"id": "x"})

            tenants = await list_tenant_databases(client)
        finally:
            await client.close()

        assert TENANT in tenants
        assert FOREIGN not in tenants
        assert "mt_test_without_meta" not in tenants
        assert {"admin", "local", "config"}.isdisjoint(tenants)
    finally:
        await _drop_databases()


@pytest.mark.asyncio
async def test_runner_dry_run_does_not_write():
    await _drop_databases()

    try:
        await write_tenant_meta_document(TENANT, False, 0)

        exit_code = await run(
            parse_args(["--indexes", "--tenant", TENANT, "--dry-run"])
        )

        meta = await MetaCollection.get_instance(TENANT).read_tenant_meta()

        assert exit_code == 0
        assert meta is not None
        assert meta["indexesVersion"] == 0
        assert meta["kind"] == TENANT_META_KIND
    finally:
        await _drop_databases()


@pytest.mark.asyncio
async def test_adopt_dry_run_does_not_write():
    await _drop_databases()

    try:
        service = await _service()
        await service.client[LEGACY]["CoreSettings"].insert_one(
            {
                "_id": "cs-1",
                "id": "cs-1",
                "nickname": "  TiendaLegacy ",
                "token": "content-token",
                "createdAt": 1,
            }
        )

        exit_code = await run(
            parse_args(["--adopt", "--tenant", LEGACY, "--dry-run"])
        )

        meta = await MetaCollection.get_instance(LEGACY).read_tenant_meta()
        document = await service.client[LEGACY]["CoreSettings"].find_one(
            {"_id": "cs-1"}
        )

        assert exit_code == 0
        assert meta is None
        assert document is not None
        assert document["nickname"] == "  TiendaLegacy "
    finally:
        await _drop_databases()


@pytest.mark.asyncio
async def test_adopt_creates_meta_and_normalizes_nicknames():
    await _drop_databases()

    try:
        service = await _service()
        await service.client[LEGACY]["CoreSettings"].insert_one(
            {
                "_id": "cs-1",
                "id": "cs-1",
                "nickname": "  TiendaLegacy ",
                "token": "content-token",
                "createdAt": 1,
            }
        )

        exit_code = await run(parse_args(["--adopt", "--tenant", LEGACY]))

        meta = await MetaCollection.get_instance(LEGACY).read_tenant_meta()
        document = await service.client[LEGACY]["CoreSettings"].find_one(
            {"_id": "cs-1"}
        )

        assert exit_code == 0
        assert meta is not None
        assert meta["kind"] == TENANT_META_KIND
        assert meta["nickname"] == LEGACY
        assert meta["isProvisioned"] is True
        assert meta["indexesVersion"] == get_target_indexes_version()

        assert document is not None
        assert document["nickname"] == LEGACY
    finally:
        await _drop_databases()
