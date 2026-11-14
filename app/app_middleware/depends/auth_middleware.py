from fastapi import Request, status
from fastapi.exceptions import HTTPException

from kardex.core.security import TokenManager
from kardex.kardex_config import kardexCtx
from kardex.tools.users_tool import UsersTool


def auth_middleware(req: Request):
    auth_header = req.headers.get("Authorization")
    if auth_header is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    token_type, token = auth_header.split(" ")

    if token_type != "Bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    payload = TokenManager.decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    # El claim del token debe coincidir con el tenant del header. Todos los
    # negocios numeran su primer usuario como "0001": sin esta comparacion un
    # token de A serviria contra la base de B.
    token_tenant = payload.get("tenant") or ""
    context_tenant = kardexCtx.get().businessNickname

    if not token_tenant or token_tenant != context_tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch"
        )

    user_payload = payload.get("user")
    if user_payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    user_id = user_payload.get("id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    user = UsersTool().get_inactive_user_by_id(user_id)

    if user is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )
