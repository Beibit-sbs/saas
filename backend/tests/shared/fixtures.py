from __future__ import annotations

from collections.abc import Generator
from typing import Callable
from unittest.mock import MagicMock

import pytest

from app.modules.auth.token_service import create_access_token


@pytest.fixture
def auth_headers_factory() -> Callable[[str, list[str]], dict[str, str]]:
    """Build Authorization headers for test users with explicit role sets."""

    def _factory(user_id: str, roles: list[str]) -> dict[str, str]:
        token = create_access_token(user_id=user_id, roles=roles, auth_source="test")
        return {"Authorization": f"Bearer {token}"}

    return _factory


@pytest.fixture
def audit_mock(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patch shared audit logger to assert audit writes without DB side effects."""
    mock = MagicMock(name="log_admin_action")
    monkeypatch.setattr("app.modules.audit.service.log_admin_action", mock)
    return mock


@pytest.fixture
def tenant_factory() -> Callable[..., dict[str, object]]:
    """Build tenant payloads used by tests that require trusted tenant context."""

    def _factory(
        *,
        tenant_id: int = 1,
        status: str = "active",
        slug: str = "tenant-1",
        name: str = "Tenant 1",
    ) -> dict[str, object]:
        return {
            "id": tenant_id,
            "status": status,
            "slug": slug,
            "name": name,
        }

    return _factory


@pytest.fixture
def tenant_session_override() -> Generator[Callable[..., MagicMock], None, None]:
    """Register dependency overrides returning tenant-scoped session mocks.

    Usage:
        session = tenant_session_override(app=app, dependency=get_module_db)
    """
    from app.main import app as shared_app

    installed: list[tuple[object, object, object | None]] = []

    def _install(*, app=shared_app, dependency, session: MagicMock | None = None) -> MagicMock:
        mock_session = session or MagicMock(name="tenant_db_session")
        previous = app.dependency_overrides.get(dependency)
        app.dependency_overrides[dependency] = lambda: mock_session
        installed.append((app, dependency, previous))
        return mock_session

    try:
        yield _install
    finally:
        for app_ref, dependency, previous in reversed(installed):
            if previous is None:
                app_ref.dependency_overrides.pop(dependency, None)
            else:
                app_ref.dependency_overrides[dependency] = previous
