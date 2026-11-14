import sys
from pathlib import Path

import pytest

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from kardex.kardex_config import KardexContext, kardexCtx
from kardex.repos.v1.branches import BranchInDb, BranchesRepository
from kardex.tools import BranchesTool, EtagTool
from kardex.tools.kardex_exceptions import TenantContextMissingError


def _set_tenant(nickname: str):
    return kardexCtx.set(KardexContext(businessNickname=nickname))


def test_etag_cache_is_per_tenant():
    tool = EtagTool()

    token = _set_tenant("tienda-a")
    try:
        tool.set_tag("branches_count", "3")
        tool.set_last_update_branch_etag("100")
    finally:
        kardexCtx.reset(token)

    token = _set_tenant("tienda-b")
    try:
        tool.set_tag("branches_count", "7")
        tenant_b_tag = tool.get_branches_etag()
        assert tenant_b_tag is not None
        assert tenant_b_tag.value == "7_-"
        count_tag = tool.get_etag("branches_count")
        assert count_tag is not None
        assert count_tag.value == "7"
    finally:
        kardexCtx.reset(token)

    token = _set_tenant("tienda-a")
    try:
        tenant_a_tag = tool.get_branches_etag()
        assert tenant_a_tag is not None
        assert tenant_a_tag.value == "3_100"
    finally:
        kardexCtx.reset(token)


@pytest.mark.asyncio
async def test_branches_tool_cache_is_per_tenant(monkeypatch):
    async def fake_get_all_branches(self, *args, **kwargs):
        tenant = kardexCtx.get().businessNickname
        return [BranchInDb(id="branch-1", name=tenant, createdAt=0)]

    monkeypatch.setattr(BranchesRepository, "get_all_branches", fake_get_all_branches)

    tool = BranchesTool()

    token = _set_tenant("tienda-a")
    try:
        await tool.ensure_loaded()
        branch = tool.get_branch_by_id("branch-1")
        assert branch is not None
        assert branch.name == "tienda-a"
    finally:
        kardexCtx.reset(token)

    token = _set_tenant("tienda-b")
    try:
        await tool.ensure_loaded()
        branch = tool.get_branch_by_id("branch-1")
        assert branch is not None
        assert branch.name == "tienda-b"
    finally:
        kardexCtx.reset(token)


@pytest.mark.asyncio
async def test_cache_tools_require_tenant():
    with pytest.raises(TenantContextMissingError):
        EtagTool().set_tag("branches_count", "1")

    with pytest.raises(TenantContextMissingError):
        await BranchesTool().ensure_loaded()
