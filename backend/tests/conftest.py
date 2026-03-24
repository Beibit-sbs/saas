# ruff: noqa: E402

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
from app.modules.auth.mfa_service import clear_mfa_state
from app.modules.auth.session_service import clear_sessions_state
from app.modules.auth.token_service import create_access_token
from app.modules.backup import service as backup_service
from app.modules.example_notes import service as example_notes_service
from app.modules.feature_flags import service as feature_flags_service
from app.modules.i18n import service as i18n_service
from app.modules.integrations import service as integrations_service
from app.modules.jobs import service as jobs_service
from app.modules.plans import service as plans_service
from app.modules.quotas import service as quotas_service
from app.modules.rbac import service as rbac_service
from app.modules.observability.security_signals import clear_security_signal_state
from app.modules.security import rate_limit as rate_limit_service
from app.modules.tenants import service as tenant_service
from app.modules.usage import service as usage_service
from app.modules.university_core import service as university_core_service
from app.platform.analytics import service as analytics_service
from app.platform.kpi import service as kpi_service
from app.platform.automation import service as automation_service
from app.platform.context import service as context_service
from app.platform.uow import UnitOfWork
from app.platform.webhooks import service as webhook_service


client = TestClient(app)
os.environ.setdefault("AUTH_DEV_DEMO_COMPATIBILITY", "true")
os.environ.setdefault("RBAC_ALLOW_DEV_FALLBACK", "true")

DEFAULT_FLAGS = copy.deepcopy(feature_flags_service._flags)
DEFAULT_FLAGS_BY_TENANT = {
    tenant_id: copy.deepcopy(store)
    for tenant_id, store in feature_flags_service._flags_by_tenant.items()
}
DEFAULT_LANGUAGES = copy.deepcopy(i18n_service.languages)


def _sync_user_roles_for_tests(user_id: str, roles: list[str], tenant_id: int = 1) -> dict[str, object]:
    normalized_user_id = str(user_id or "").strip()
    if not normalized_user_id:
        raise ValueError("user_id is required")

    normalized_tenant_id = int(tenant_id)
    desired_roles = sorted({str(role).strip() for role in roles if str(role).strip()})
    current_roles = set(rbac_service.get_user_roles_for_tenant(normalized_user_id, normalized_tenant_id))

    for role in sorted(current_roles - set(desired_roles)):
        rbac_service.revoke_role_for_tenant(normalized_tenant_id, normalized_user_id, role)

    for role in desired_roles:
        try:
            rbac_service.assign_role_to_user(normalized_tenant_id, normalized_user_id, role)
        except ValueError as exc:
            # Some tests intentionally rely on non-platform role labels.
            if "unknown role" not in str(exc):
                raise

    synced_roles = rbac_service.get_user_roles_for_tenant(normalized_user_id, normalized_tenant_id)
    return {"user_id": normalized_user_id, "roles": sorted(synced_roles)}


def _auth_headers(user_id: str, roles: list[str]) -> dict[str, str]:
    # Keep RBAC resolution consistent between in-memory and DB-backed test paths.
    # In DB mode, permission checks read assignments from app_user_roles, so we
    # mirror test token roles into trusted role assignments.
    for role in roles:
        try:
            rbac_service.assign_role_to_user(tenant_id=1, user_id=user_id, role=role)
        except ValueError as exc:
            # Some tests intentionally use non-platform roles (e.g. "student")
            # to validate permission denial paths.
            if "unknown role" not in str(exc):
                raise
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
    clear_security_signal_state()
    rate_limit_service.clear_rate_limit_state()
    ai_service.clear_ai_gateway_state()
    audit_service.clear_audit_events()
    backup_service._backup_history.clear()
    jobs_service.clear_jobs_state()
    usage_service.clear_usage_state()
    example_notes_service.clear_example_notes()
    integrations_service._settings.clear()
    integrations_service._fernet.cache_clear()
    university_core_service.clear_university_state()
    analytics_service.clear_analytics_state()
    kpi_service.clear_kpi_state()
    automation_service.clear_automation_state()
    context_service.clear_context_state()
    with UnitOfWork() as uow:
        uow.outbox_event_repository.clear_state(conn=uow.conn)
        uow.analytics_repository.clear_state()
    webhook_service.clear_webhook_state()
    tenant_service.clear_tenant_state()
    plans_service.clear_plans_state()
    quotas_service.clear_quotas_state()
    if hasattr(rbac_service, "_clear_permission_cache"):
        rbac_service._clear_permission_cache()
    _reset_local_user_store()
    clear_mfa_state()
    clear_sessions_state()
    i18n_service.languages.clear()
    i18n_service.languages.update(copy.deepcopy(DEFAULT_LANGUAGES))
    feature_flags_service._flags.clear()
    feature_flags_service._flags.update(copy.deepcopy(DEFAULT_FLAGS))
    feature_flags_service._flags_by_tenant.clear()
    feature_flags_service._flags_by_tenant.update(
        {
            tenant_id: copy.deepcopy(store)
            for tenant_id, store in DEFAULT_FLAGS_BY_TENANT.items()
        }
    )


@pytest.fixture(autouse=True)
def reset_shared_state(monkeypatch):
    monkeypatch.setenv("AUTH_DEV_DEMO_COMPATIBILITY", "true")
    monkeypatch.setenv("RBAC_ALLOW_DEV_FALLBACK", "true")
    monkeypatch.setattr("app.modules.auth.router.sync_user_roles_from_trusted_source", _sync_user_roles_for_tests)
    monkeypatch.setattr("app.modules.admin.local_users_router.sync_user_roles_from_trusted_source", _sync_user_roles_for_tests)
    _reset_template_state()
    yield
    _reset_template_state()
