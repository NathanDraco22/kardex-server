from fastapi import Header, HTTPException, status


def get_branch_id(
    x_branch: str | None = Header(default=None, alias="X-Branch"),
    branch_id: str | None = Header(default=None, alias="branch-id"),
) -> str:
    """Return the branch id sent by the client.

    The Flutter app sends ``X-Branch`` while legacy clients send ``branch-id``.
    Both headers are accepted so imports/exports keep working during migrations.
    """

    value = (x_branch or branch_id or "").strip()
    if not value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El header de sucursal es obligatorio (X-Branch o branch-id)",
        )
    return value
