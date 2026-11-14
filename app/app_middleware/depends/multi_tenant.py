import asyncio

from fastapi import HTTPException, Request, status

from kardex.kardex_config import KardexContext, kardexCtx
from kardex.tools import (
    BranchesTool,
    EtagTool,
    is_valid_tenant_nickname,
    normalize_nickname,
)
from kardex.tools.users_tool import UsersTool


async def multi_tenant_middleware(req: Request):
    """Publica el tenant del request en ``kardexCtx``.

    El header es obligatorio: no hay fallback a ``DB_NAME``. Se declara como
    dependencia del router v1 (request scope, con ``yield``) para que el
    contexto exista antes de resolver los guards de cada modulo y para que el
    ``reset`` ocurra al cerrar el request.
    """

    nickname = normalize_nickname(
        req.headers.get("x-tenant-nickname") or req.headers.get("x-servin")
    )
    branch_id = req.headers.get("x-branch") or req.headers.get("x-branch-id") or ""

    if not nickname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required tenant header ('X-Servin' or 'x-tenant-nickname')",
        )

    if not is_valid_tenant_nickname(nickname):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tenant nickname",
        )

    token = kardexCtx.set(
        KardexContext(businessNickname=nickname, branchId=branch_id)
    )
    try:
        # Caches con getters sincronos: se cargan una vez por tenant aqui.
        await asyncio.gather(
            BranchesTool().ensure_loaded(),
            UsersTool().ensure_loaded(),
            EtagTool().ensure_loaded(),
        )
        yield
    finally:
        kardexCtx.reset(token)
