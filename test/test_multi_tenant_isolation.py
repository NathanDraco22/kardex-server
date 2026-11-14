import sys
from pathlib import Path

import pytest

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from kardex.kardex_config import KardexContext, kardexCtx
from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import MetaCollection
from kardex.services.mongo_collections.v1.meta_collection import (
    write_tenant_meta_document,
)
from kardex.tools import TenantContextMissingError
from test.mongo_test_utils import mongo_available

pytestmark = pytest.mark.skipif(
    not mongo_available(),
    reason="MongoDB no disponible: se omite la prueba de aislamiento",
)

TENANT_A = "mt_test_tenant_a"
TENANT_B = "mt_test_tenant_b"


async def _service() -> MongoService:
    service = MongoService()
    if not hasattr(service, "client"):
        await service.init_client()
    return service


async def _drop_databases() -> None:
    service = await _service()
    for tenant in (TENANT_A, TENANT_B):
        await service.client.drop_database(tenant)


@pytest.mark.asyncio
async def test_same_collection_resolves_per_tenant():
    await _drop_databases()

    try:
        await write_tenant_meta_document(TENANT_A, True, 1)
        await write_tenant_meta_document(TENANT_B, True, 2)

        token = kardexCtx.set(KardexContext(businessNickname=TENANT_A))
        try:
            meta_a = await MetaCollection.get_instance().read_tenant_meta()
        finally:
            kardexCtx.reset(token)

        token = kardexCtx.set(KardexContext(businessNickname=TENANT_B))
        try:
            meta_b = await MetaCollection.get_instance().read_tenant_meta()
        finally:
            kardexCtx.reset(token)

        assert meta_a is not None
        assert meta_a["nickname"] == TENANT_A
        assert meta_a["indexesVersion"] == 1

        assert meta_b is not None
        assert meta_b["nickname"] == TENANT_B
        assert meta_b["indexesVersion"] == 2
    finally:
        await _drop_databases()


@pytest.mark.asyncio
async def test_explicit_instance_targets_one_tenant():
    await _drop_databases()

    try:
        await write_tenant_meta_document(TENANT_A, True, 5)

        meta_a = await MetaCollection.get_instance(TENANT_A).read_tenant_meta()
        meta_b = await MetaCollection.get_instance(TENANT_B).read_tenant_meta()

        assert meta_a is not None
        assert meta_a["indexesVersion"] == 5
        assert meta_b is None
    finally:
        await _drop_databases()


@pytest.mark.asyncio
async def test_collection_without_tenant_fails_instead_of_falling_back():
    with pytest.raises(TenantContextMissingError):
        await MetaCollection.get_instance().read_tenant_meta()
