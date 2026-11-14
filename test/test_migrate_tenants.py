import sys
from pathlib import Path

import pytest
from pymongo import AsyncMongoClient
from pymongo.errors import DuplicateKeyError

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import CoreSettingsCollection, MetaCollection
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
    adopt_tenant,
    list_adoptable_databases,
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
UPPER_LEGACY = "MT_Test_LegacyUpper"
DUPLICATE = "mt_test_dup_index"


async def _service() -> MongoService:
    service = MongoService()
    if not hasattr(service, "client"):
        await service.init_client()
    return service


async def _drop_databases() -> None:
    service = await _service()
    for name in (TENANT, FOREIGN, LEGACY, UPPER_LEGACY, DUPLICATE):
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


@pytest.mark.asyncio
async def test_adopt_skips_database_with_foreign_meta():
    await _drop_databases()

    try:
        service = await _service()
        await service.client[FOREIGN]["Meta"].insert_one(
            {"_id": "tenant", "kind": "otra-cosa"}
        )
        await service.client[FOREIGN]["Products"].insert_one({"id": "p1"})

        candidates = await list_adoptable_databases(service.client)
        exit_code = await run(
            parse_args(["--adopt", "--tenant", FOREIGN, "--dry-run"])
        )

        meta = await MetaCollection.get_instance(FOREIGN).read_tenant_meta()

        assert FOREIGN not in candidates
        assert exit_code == 1
        assert meta is not None
        assert meta["kind"] == "otra-cosa"
    finally:
        await _drop_databases()


@pytest.mark.asyncio
async def test_adopt_rejects_non_normalized_database_name():
    await _drop_databases()

    try:
        service = await _service()
        await service.client[UPPER_LEGACY]["Products"].insert_one({"id": "p1"})

        exit_code = await run(
            parse_args(["--adopt", "--tenant", UPPER_LEGACY])
        )

        meta = await MetaCollection.get_instance(UPPER_LEGACY).read_tenant_meta()

        assert exit_code == 1
        assert meta is None
    finally:
        await _drop_databases()


@pytest.mark.asyncio
async def test_adopt_writes_intermediate_meta_until_indexes_run():
    await _drop_databases()

    try:
        service = await _service()
        await service.client[LEGACY]["CoreSettings"].insert_one(
            {
                "_id": "cs-1",
                "id": "cs-1",
                "nickname": "TiendaLegacy",
                "token": "content-token",
                "createdAt": 1,
            }
        )

        await adopt_tenant(service.client, LEGACY)

        meta = await MetaCollection.get_instance(LEGACY).read_tenant_meta()

        assert meta is not None
        assert meta["isProvisioned"] is False
        assert meta["indexesVersion"] == 0

        action = await ensure_indexes_for_tenant(LEGACY)

        closed = await MetaCollection.get_instance(LEGACY).read_tenant_meta()

        assert action == "updated"
        assert closed is not None
        assert closed["isProvisioned"] is True
        assert closed["indexesVersion"] == get_target_indexes_version()
    finally:
        await _drop_databases()


@pytest.mark.asyncio
async def test_core_settings_unique_index_blocks_duplicates():
    await _drop_databases()

    try:
        collection_class = CoreSettingsCollection.get_instance(DUPLICATE)
        await collection_class.create_indexes()
        collection = collection_class._collection

        await collection.insert_one({"nickname": DUPLICATE, "id": "cs-1"})

        with pytest.raises(DuplicateKeyError):
            await collection.insert_one({"nickname": DUPLICATE, "id": "cs-2"})
    finally:
        await _drop_databases()
