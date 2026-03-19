import copy
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.modules.ai_gateway import service as ai_service
from app.modules.audit import service as audit_service
from app.modules.auth.local_users_service import local_user_store
from app.modules.auth.token_service import create_access_token
from app.modules.backup import service as backup_service
from app.modules.example_notes import service as example_notes_service
from app.modules.feature_flags import service as feature_flags_service
from app.modules.i18n import service as i18n_service
from app.modules.integrations import service as integrations_service
from app.modules.rbac import service as rbac_service
from app.modules.security import rate_limit as rate_limit_service
from app.modules.tenants import service as tenant_service
from app.modules.university_core import service as university_core_service


client = TestClient(app)
os.environ.setdefault("AUTH_DEV_DEMO_COMPATIBILITY", "true")
os.environ.setdefault("RBAC_ALLOW_DEV_FALLBACK", "true")

DEFAULT_FLAGS = copy.deepcopy(feature_flags_service._flags)
DEFAULT_LANGUAGES = copy.deepcopy(i18n_service.languages)


def _auth_headers(user_id: str, roles: list[str]) -> dict[str, str]:
    token = create_access_token(user_id=user_id, roles=roles, auth_source="test")
    return {"Authorization": f"Bearer {token}"}


def _configure_db_only_role_resolution(monkeypatch, assignments: dict[str, list[str]]) -> None:
    monkeypatch.setenv("AUTH_DEV_DEMO_COMPATIBILITY", "true")
    monkeypatch.setenv("RBAC_ALLOW_DEV_FALLBACK", "false")
    monkeypatch.setattr(
        rbac_service,
        "_get_user_roles_db",
        lambda user_id: list(assignments.get(user_id, [])),
    )

    def fake_resolve(roles: list[str]) -> set[str]:
        granted: set[str] = set()
        for role in roles:
            granted.update(rbac_service.BASELINE_ROLE_PERMISSIONS.get(role, set()))
        return granted

    monkeypatch.setattr(rbac_service, "_resolve_permissions_db", fake_resolve)


ADMIN_HEADERS = _auth_headers("owner@example.com", ["admin"])


def _reset_local_user_store() -> None:
    local_user_store._users_by_id.clear()
    local_user_store._users_by_login.clear()
    local_user_store._counter = 0
    local_user_store._loaded = False


def _reset_template_state() -> None:
    client.cookies.clear()
    rate_limit_service.clear_rate_limit_state()
    ai_service.clear_ai_gateway_state()
    audit_service.clear_audit_events()
    backup_service._backup_history.clear()
    example_notes_service.clear_example_notes()
    integrations_service._settings.clear()
    integrations_service._fernet.cache_clear()
    university_core_service.clear_university_state()
    tenant_service.clear_tenant_state()
    if hasattr(rbac_service, "_clear_permission_cache"):
        rbac_service._clear_permission_cache()
    _reset_local_user_store()
    i18n_service.languages.clear()
    i18n_service.languages.update(copy.deepcopy(DEFAULT_LANGUAGES))
    feature_flags_service._flags.clear()
    feature_flags_service._flags.update(copy.deepcopy(DEFAULT_FLAGS))


@pytest.fixture(autouse=True)
def reset_shared_state(monkeypatch):
    monkeypatch.setenv("AUTH_DEV_DEMO_COMPATIBILITY", "true")
    monkeypatch.setenv("RBAC_ALLOW_DEV_FALLBACK", "true")
    _reset_template_state()
    yield
    _reset_template_state()
