import asyncio
import sys
from pathlib import Path

import pytest

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from kardex.kardex_config import KardexContext, kardexCtx
from kardex.services import BaseMongoCollection, MongoService
from kardex.services.mongo_collections.v1 import ProductsCollection
from kardex.tools import (
    TenantContextMissingError,
    run_with_tenant_context,
)


def test_mongo_service_requires_tenant():
    with pytest.raises(TenantContextMissingError):
        MongoService().get_collection("Products")


def test_default_collection_instance_has_no_tenant_anchor():
    default_instance = ProductsCollection.get_instance()
    explicit_a = ProductsCollection.get_instance("tienda-a")
    explicit_a_again = ProductsCollection.get_instance("tienda-a")

    assert isinstance(default_instance, BaseMongoCollection)
    assert default_instance.nickname == ""
    assert explicit_a.nickname == "tienda-a"
    assert explicit_a is explicit_a_again
    assert explicit_a is not ProductsCollection.get_instance("tienda-b")


@pytest.mark.asyncio
async def test_run_with_tenant_context_sets_and_restores_context():
    event_loop_tenant = asyncio.current_task()

    async def task() -> str:
        return kardexCtx.get().businessNickname

    assert event_loop_tenant is not None

    outer_token = kardexCtx.set(KardexContext(businessNickname="tienda-a"))
    try:
        seen = await run_with_tenant_context("tienda-b", task)
        after = kardexCtx.get().businessNickname
    finally:
        kardexCtx.reset(outer_token)

    assert seen == "tienda-b"
    assert after == "tienda-a"
    assert kardexCtx.get().businessNickname == ""


@pytest.mark.asyncio
async def test_concurrent_background_tasks_do_not_share_tenant():
    async def delayed_task(expected: str) -> str:
        await asyncio.sleep(0)
        return kardexCtx.get().businessNickname

    results = await asyncio.gather(
        run_with_tenant_context("tienda-a", delayed_task, "tienda-a"),
        run_with_tenant_context("tienda-b", delayed_task, "tienda-b"),
    )

    assert results == ["tienda-a", "tienda-b"]
