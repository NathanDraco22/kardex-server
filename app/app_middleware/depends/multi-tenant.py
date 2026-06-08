from fastapi import Request
from kardex.kardex_config import KardexContext, kardexCtx


async def multi_tenant_middleware(req: Request):
    tenant_nickname = req.headers.get("x-tenant-nickname")
    branch_id = req.headers.get("X-Servin")

    new_ctx = KardexContext(
        businessNickname=tenant_nickname or "", branchId=branch_id or ""
    )

    token = kardexCtx.set(new_ctx)
    try:
        yield
    finally:
        kardexCtx.reset(token)
