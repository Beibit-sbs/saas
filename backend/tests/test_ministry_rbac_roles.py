"""Tests for Ministry of Education RBAC roles (TIER-3 GCC compliance)."""

from __future__ import annotations

import pytest

from app.modules.rbac import service as rbac_service
from app.modules.rbac.service import (
    BASELINE_ROLE_PERMISSIONS,
    ROLE_HIERARCHY,
    resolve_permissions_for_tenant,
)

MINISTRY_ROLES = ["ministry_observer", "ministry_auditor", "ministry_admin"]


# ------------------------------------------------------------------
# Role registration
# ------------------------------------------------------------------


@pytest.mark.parametrize("role", MINISTRY_ROLES)
def test_ministry_role_exists_in_baseline(role: str) -> None:
    assert role in BASELINE_ROLE_PERMISSIONS, f"{role} missing from BASELINE_ROLE_PERMISSIONS"


@pytest.mark.parametrize("role", MINISTRY_ROLES)
def test_ministry_role_in_hierarchy(role: str) -> None:
    assert role in ROLE_HIERARCHY, f"{role} missing from ROLE_HIERARCHY"


# ------------------------------------------------------------------
# Permission sets — read-only scope for ministry_observer
# ------------------------------------------------------------------


def test_ministry_observer_has_audit_read() -> None:
    perms = BASELINE_ROLE_PERMISSIONS["ministry_observer"]
    assert "admin.audit.read" in perms


def test_ministry_observer_has_no_write_permissions() -> None:
    perms = BASELINE_ROLE_PERMISSIONS["ministry_observer"]
    write_perms = {p for p in perms if ".write" in p or ".manage" in p}
    assert write_perms == set(), f"ministry_observer should not have write perms: {write_perms}"


# ------------------------------------------------------------------
# ministry_auditor — superset of observer
# ------------------------------------------------------------------


def test_ministry_auditor_has_export_permissions() -> None:
    perms = BASELINE_ROLE_PERMISSIONS["ministry_auditor"]
    assert "admin.audit.export" in perms
    assert "compliance.export" in perms


def test_ministry_auditor_subsumes_observer() -> None:
    observer_perms = BASELINE_ROLE_PERMISSIONS["ministry_observer"]
    auditor_perms = BASELINE_ROLE_PERMISSIONS["ministry_auditor"]
    missing = observer_perms - auditor_perms
    assert missing == set(), f"ministry_auditor missing observer perms: {missing}"


# ------------------------------------------------------------------
# ministry_admin — full ministry access
# ------------------------------------------------------------------


def test_ministry_admin_has_tenant_write() -> None:
    perms = BASELINE_ROLE_PERMISSIONS["ministry_admin"]
    assert "admin.tenants.write" in perms


def test_ministry_admin_has_compliance_write() -> None:
    perms = BASELINE_ROLE_PERMISSIONS["ministry_admin"]
    assert "compliance.write" in perms


# ------------------------------------------------------------------
# Hierarchy ordering
# ------------------------------------------------------------------


def test_ministry_hierarchy_order() -> None:
    assert ROLE_HIERARCHY["ministry_admin"] > ROLE_HIERARCHY["ministry_auditor"]
    assert ROLE_HIERARCHY["ministry_auditor"] > ROLE_HIERARCHY["ministry_observer"]
    # Ministry observer is below auditor (standard platform role)
    assert ROLE_HIERARCHY["ministry_observer"] < ROLE_HIERARCHY["auditor"]
    # ministry_admin is below admin
    assert ROLE_HIERARCHY["ministry_admin"] < ROLE_HIERARCHY["admin"]


# ------------------------------------------------------------------
# resolve_permissions_for_tenant integration
# ------------------------------------------------------------------


def test_resolve_ministry_observer_permissions() -> None:
    perms = resolve_permissions_for_tenant(["ministry_observer"], tenant_id=1)
    assert "admin.audit.read" in perms
    assert "admin.dashboard.read" in perms


def test_resolve_ministry_auditor_permissions() -> None:
    perms = resolve_permissions_for_tenant(["ministry_auditor"], tenant_id=1)
    assert "admin.audit.export" in perms
    assert "compliance.export" in perms


def test_resolve_ministry_admin_permissions() -> None:
    perms = resolve_permissions_for_tenant(["ministry_admin"], tenant_id=1)
    assert "admin.tenants.write" in perms
    assert "compliance.write" in perms


# ------------------------------------------------------------------
# Role assignment (in-memory path)
# ------------------------------------------------------------------


def test_assign_ministry_observer_role(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    result = rbac_service.assign_role_to_user(
        tenant_id=1,
        user_id="ministry-user@moe.gov.sa",
        role="ministry_observer",
    )
    assert "ministry_observer" in result["roles"]


def test_assign_ministry_auditor_role(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    result = rbac_service.assign_role_to_user(
        tenant_id=1,
        user_id="auditor@moe.gov.sa",
        role="ministry_auditor",
    )
    assert "ministry_auditor" in result["roles"]


def test_assign_ministry_admin_role(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    result = rbac_service.assign_role_to_user(
        tenant_id=1,
        user_id="moe-admin@moe.gov.sa",
        role="ministry_admin",
    )
    assert "ministry_admin" in result["roles"]
