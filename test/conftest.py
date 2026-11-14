import sys
from pathlib import Path
from typing import Any, cast

import pytest

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from kardex.tools import BranchesTool, EtagTool
from kardex.tools.app_settings_tool import AppSettingsTool
from kardex.tools.integration_tool import IntegrationTool
from kardex.tools.users_tool import UsersTool


def _private_cache(owner: type, attribute: str) -> dict[str, Any]:
    return cast(dict[str, Any], getattr(owner, attribute))


def _tenant_caches() -> list[dict[str, Any]]:
    return [
        BranchesTool._branches,
        UsersTool._inactive_users,
        EtagTool._tags,
        _private_cache(
            AppSettingsTool, "_AppSettingsTool__current_app_settings"
        ),
        _private_cache(
            IntegrationTool, "_IntegrationTool__current_integration"
        ),
    ]


@pytest.fixture(autouse=True)
def clear_tenant_caches():
    """Aisla las caches en memoria entre pruebas (dicts keyed by nickname)."""

    caches = _tenant_caches()

    for cache in caches:
        cache.clear()

    yield

    for cache in caches:
        cache.clear()
