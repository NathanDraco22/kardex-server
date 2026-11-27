from fastapi import Depends, HTTPException, Request, status

from kardex.core.role_manager.role_manager import Modules
from kardex.repos.v1.users import UsersDataSource, UsersRepository

from .auth_middleware import auth_middleware

_users_repo = UsersRepository(UsersDataSource())


async def require_settings_access(
    req: Request,
    _: None = Depends(auth_middleware),
) -> None:
    """Exige autenticación y acceso al módulo de Configuraciones."""
    user_id = getattr(req.state, "auth_user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    user = await _users_repo.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    is_root_or_admin = (
        user.id == "root"
        or user.username.lower() == "root"
        or user.role == "Admin"
    )
    has_settings_access = (
        Modules.SETTINGS in user.userRole.access
        or Modules.ALL in user.userRole.access
    )

    if not (is_root_or_admin or has_settings_access):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
        )
