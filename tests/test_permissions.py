"""
Tests for permission helpers.
"""

from types import SimpleNamespace

import pytest

from services.permissions import (
    AdminOnlyError,
    admin_only,
    has_admin_permission,
    has_allowlisted_admin,
)


def _extract_check(check_decorator):
    async def dummy(interaction):
        return interaction

    decorated = check_decorator(dummy)
    return decorated.__discord_app_commands_checks__[0]


def test_has_allowlisted_admin(monkeypatch):
    monkeypatch.setattr("services.permissions.ADMIN_USER_IDS", [101])
    interaction = SimpleNamespace(user=SimpleNamespace(id=101))

    assert has_allowlisted_admin(interaction) is True


def test_has_admin_permission_allowlist(monkeypatch):
    monkeypatch.setattr("services.permissions.ADMIN_USER_IDS", [202])
    interaction = SimpleNamespace(user=SimpleNamespace(id=202), guild=None)

    assert has_admin_permission(interaction) is True


def test_has_admin_permission_guild_member_permissions(monkeypatch):
    monkeypatch.setattr("services.permissions.ADMIN_USER_IDS", [])

    perms = SimpleNamespace(administrator=True, manage_guild=False)
    member = SimpleNamespace(guild_permissions=perms)
    guild = SimpleNamespace(get_member=lambda _uid: member)
    interaction = SimpleNamespace(user=SimpleNamespace(id=303), guild=guild)

    assert has_admin_permission(interaction) is True


def test_has_admin_permission_user_permissions_fallback(monkeypatch):
    monkeypatch.setattr("services.permissions.ADMIN_USER_IDS", [])

    perms = SimpleNamespace(administrator=False, manage_guild=True)
    interaction = SimpleNamespace(user=SimpleNamespace(id=404, guild_permissions=perms), guild=None)

    assert has_admin_permission(interaction) is True


def test_has_admin_permission_false(monkeypatch):
    monkeypatch.setattr("services.permissions.ADMIN_USER_IDS", [])
    interaction = SimpleNamespace(user=SimpleNamespace(id=505), guild=None)

    assert has_admin_permission(interaction) is False


@pytest.mark.asyncio
async def test_admin_only_allows_admin(monkeypatch):
    monkeypatch.setattr("services.permissions.ADMIN_USER_IDS", [606])
    interaction = SimpleNamespace(user=SimpleNamespace(id=606), guild=None)
    check = _extract_check(admin_only())

    assert await check(interaction) is True


@pytest.mark.asyncio
async def test_admin_only_raises_for_non_admin(monkeypatch):
    monkeypatch.setattr("services.permissions.ADMIN_USER_IDS", [])
    interaction = SimpleNamespace(user=SimpleNamespace(id=707), guild=None)
    check = _extract_check(admin_only("Nope"))

    with pytest.raises(AdminOnlyError, match="Nope"):
        await check(interaction)
