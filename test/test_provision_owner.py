import sys
from pathlib import Path

import pytest
from pymongo.errors import DuplicateKeyError

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from kardex.core.tenant.provision_tenant import _create_owner_if_absent
from kardex.repos.v1.users import UsersRepository


class _FakeUsersRepo:
    def __init__(self, owner_appears_after_race: bool) -> None:
        self.owner_appears_after_race = owner_appears_after_race
        self.lookups = 0
        self.created = 0

    async def get_user_by_username(self, username: str):
        self.lookups += 1

        if self.lookups == 1:
            return None

        return object() if self.owner_appears_after_race else None

    async def create_user(self, create_user):
        self.created += 1
        raise DuplicateKeyError("duplicate username")


def _patch_repo(monkeypatch, repo: _FakeUsersRepo) -> None:
    monkeypatch.setattr(
        UsersRepository,
        "get_instance",
        classmethod(lambda cls: repo),
    )


@pytest.mark.asyncio
async def test_owner_race_is_idempotent(monkeypatch):
    repo = _FakeUsersRepo(owner_appears_after_race=True)
    _patch_repo(monkeypatch, repo)

    await _create_owner_if_absent("propietario")

    assert repo.created == 1
    assert repo.lookups == 2


@pytest.mark.asyncio
async def test_owner_race_reraises_if_user_still_missing(monkeypatch):
    repo = _FakeUsersRepo(owner_appears_after_race=False)
    _patch_repo(monkeypatch, repo)

    with pytest.raises(DuplicateKeyError):
        await _create_owner_if_absent("propietario")

    assert repo.created == 1
    assert repo.lookups == 2
