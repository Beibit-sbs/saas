"""
Coverage boost: app.modules.rbac.service — in-memory path functions
and app.modules.rbac.router — governance / error branches.

Tests run without DATABASE_URL so _use_database() is False;
all public functions fall back to the tenant-aware in-memory stores.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.rbac import service as svc
from tests.conftest import ADMIN_HEADERS, _auth_headers

client_local = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _platform_admin_headers():
    """Create a superadmin token for tenant 1."""
    # Assign superadmin directly in the in-memory store so is_platform_admin works
    svc._tenant_user_roles_state.setdefault(1, {})
    svc._tenant_user_roles_state[1]["superadmin@example.com"] = {"superadmin"}
    return _auth_headers("superadmin@example.com", ["superadmin"], tenant_id=1)


# ---------------------------------------------------------------------------
# get_role_hierarchy_level
# ---------------------------------------------------------------------------


class TestGetRoleHierarchyLevel:
    def test_superadmin_is_100(self):
        assert svc.get_role_hierarchy_level("superadmin") == 100

    def test_admin_is_50(self):
        assert svc.get_role_hierarchy_level("admin") == 50

    def test_dean_is_40(self):
        assert svc.get_role_hierarchy_level("dean") == 40

    def test_teacher_is_20(self):
        assert svc.get_role_hierarchy_level("teacher") == 20

    def test_auditor_is_10(self):
        assert svc.get_role_hierarchy_level("auditor") == 10

    def test_student_is_0(self):
        assert svc.get_role_hierarchy_level("student") == 0

    def test_unknown_role_is_minus_one(self):
        assert svc.get_role_hierarchy_level("unknownrole") == -1

    def test_case_insensitive(self):
        assert svc.get_role_hierarchy_level("ADMIN") == 50
        assert svc.get_role_hierarchy_level("SuperAdmin") == 100


# ---------------------------------------------------------------------------
# get_highest_role_level
# ---------------------------------------------------------------------------


class TestGetHighestRoleLevel:
    def test_empty_list_is_minus_one(self):
        assert svc.get_highest_role_level([]) == -1

    def test_single_role(self):
        assert svc.get_highest_role_level(["admin"]) == 50

    def test_multiple_roles_returns_max(self):
        assert svc.get_highest_role_level(["student", "dean", "auditor"]) == 40

    def test_with_unknown_role(self):
        # unknown roles have level -1; max is determined by known roles
        assert svc.get_highest_role_level(["unknown", "teacher"]) == 20


# ---------------------------------------------------------------------------
# is_platform_admin — memory path
# ---------------------------------------------------------------------------


class TestIsPlatformAdmin:
    def test_empty_user_id_returns_false(self):
        assert svc.is_platform_admin("") is False

    def test_whitespace_user_id_returns_false(self):
        assert svc.is_platform_admin("   ") is False

    def test_user_without_superadmin_returns_false(self):
        svc._tenant_user_roles_state.setdefault(1, {})
        svc._tenant_user_roles_state[1]["regular@e.com"] = {"admin"}
        assert svc.is_platform_admin("regular@e.com") is False

    def test_user_with_superadmin_returns_true(self, reset_shared_state):
        svc._tenant_user_roles_state.setdefault(1, {})
        svc._tenant_user_roles_state[1]["sa@e.com"] = {"superadmin"}
        assert svc.is_platform_admin("sa@e.com") is True


# ---------------------------------------------------------------------------
# list_roles_for_tenant
# ---------------------------------------------------------------------------


class TestListRolesForTenant:
    def test_default_tenant_has_baseline_roles(self):
        roles = svc.list_roles_for_tenant(1)
        assert "admin" in roles
        assert "student" in roles
        assert isinstance(roles["admin"], list)

    def test_new_tenant_starts_empty(self):
        roles = svc.list_roles_for_tenant(9999)
        assert isinstance(roles, dict)

    def test_invalid_tenant_raises(self):
        with pytest.raises(ValueError):
            svc.list_roles_for_tenant(-1)


# ---------------------------------------------------------------------------
# add_or_update_role_for_tenant
# ---------------------------------------------------------------------------


class TestAddOrUpdateRoleForTenant:
    def test_adds_new_role(self):
        result = svc.add_or_update_role_for_tenant(1, "researcher", ["research.read"])
        assert "researcher" in result
        assert "research.read" in result["researcher"]

    def test_updates_existing_role(self):
        svc.add_or_update_role_for_tenant(1, "researcher", ["research.read"])
        svc.add_or_update_role_for_tenant(1, "researcher", ["research.read", "research.write"])
        roles = svc.list_roles_for_tenant(1)
        assert "research.write" in roles["researcher"]

    def test_empty_permissions(self):
        result = svc.add_or_update_role_for_tenant(1, "norole", [])
        assert result["norole"] == []

    def test_empty_name_raises(self):
        with pytest.raises(ValueError):
            svc.add_or_update_role_for_tenant(1, "   ", ["read"])

    def test_superadmin_in_non_platform_tenant_raises(self):
        with pytest.raises(PermissionError):
            svc.add_or_update_role_for_tenant(2, "superadmin", [])


# ---------------------------------------------------------------------------
# assign_role_to_user
# ---------------------------------------------------------------------------


class TestAssignRoleToUser:
    def test_assigns_known_role(self):
        result = svc.assign_role_to_user(1, "alice@e.com", "student")
        assert "roles" in result
        assert "student" in result["roles"]

    def test_unknown_role_raises(self):
        with pytest.raises(ValueError, match="unknown role"):
            svc.assign_role_to_user(1, "alice@e.com", "nonexistent_role")

    def test_empty_user_id_raises(self):
        with pytest.raises(ValueError):
            svc.assign_role_to_user(1, "  ", "student")

    def test_empty_role_raises(self):
        with pytest.raises(ValueError):
            svc.assign_role_to_user(1, "alice@e.com", "")


# ---------------------------------------------------------------------------
# get_user_roles_for_tenant
# ---------------------------------------------------------------------------


class TestGetUserRolesForTenant:
    def test_empty_user_returns_empty(self):
        assert svc.get_user_roles_for_tenant("", 1) == []

    def test_user_without_roles_returns_empty(self):
        assert svc.get_user_roles_for_tenant("nobody@e.com", 1) == []

    def test_returns_assigned_roles(self):
        svc.assign_role_to_user(1, "carol@e.com", "teacher")
        roles = svc.get_user_roles_for_tenant("carol@e.com", 1)
        assert "teacher" in roles

    def test_superadmin_included_if_assigned(self, reset_shared_state):
        svc._tenant_user_roles_state.setdefault(1, {})
        svc._tenant_user_roles_state[1]["super@e.com"] = {"superadmin"}
        roles = svc.get_user_roles_for_tenant("super@e.com", 1)
        assert "superadmin" in roles


# ---------------------------------------------------------------------------
# list_user_role_assignments_for_tenant
# ---------------------------------------------------------------------------


class TestListUserRoleAssignmentsForTenant:
    def test_empty_tenant_returns_empty(self):
        result = svc.list_user_role_assignments_for_tenant(8888)
        assert result == []

    def test_returns_all_users_in_tenant(self):
        svc.assign_role_to_user(1, "u1@e.com", "student")
        svc.assign_role_to_user(1, "u2@e.com", "teacher")
        result = svc.list_user_role_assignments_for_tenant(1)
        user_ids = {r["user_id"] for r in result}
        assert "u1@e.com" in user_ids
        assert "u2@e.com" in user_ids

    def test_filter_by_user_id(self):
        svc.assign_role_to_user(1, "only@e.com", "auditor")
        result = svc.list_user_role_assignments_for_tenant(1, user_id="only@e.com")
        assert len(result) >= 1
        assert all(r["user_id"] == "only@e.com" for r in result)

    def test_filter_by_role(self):
        svc.assign_role_to_user(1, "r1@e.com", "dean")
        result = svc.list_user_role_assignments_for_tenant(1, role="dean")
        assert any("dean" in r["roles"] for r in result)

    def test_filter_by_user_and_role(self):
        svc.assign_role_to_user(1, "combo@e.com", "auditor")
        result = svc.list_user_role_assignments_for_tenant(1, user_id="combo@e.com", role="auditor")
        assert len(result) == 1

    def test_filter_by_user_and_role_no_match(self):
        svc.assign_role_to_user(1, "combo2@e.com", "student")
        result = svc.list_user_role_assignments_for_tenant(1, user_id="combo2@e.com", role="dean")
        assert result == []


# ---------------------------------------------------------------------------
# revoke_role_for_tenant
# ---------------------------------------------------------------------------


class TestRevokeRoleForTenant:
    def test_revokes_existing_role(self):
        svc.assign_role_to_user(1, "eve@e.com", "student")
        result = svc.revoke_role_for_tenant(1, "eve@e.com", "student")
        assert result["removed"] is True
        assert "student" not in result["roles"]

    def test_revoke_nonexistent_returns_removed_false(self):
        result = svc.revoke_role_for_tenant(1, "nobody@e.com", "dean")
        assert result["removed"] is False

    def test_empty_user_raises(self):
        with pytest.raises(ValueError):
            svc.revoke_role_for_tenant(1, "", "student")

    def test_empty_role_raises(self):
        with pytest.raises(ValueError):
            svc.revoke_role_for_tenant(1, "u@e.com", "")

    def test_last_role_removed_cleans_entry(self):
        svc.assign_role_to_user(1, "last@e.com", "student")
        svc.revoke_role_for_tenant(1, "last@e.com", "student")
        assignments = svc.list_user_role_assignments_for_tenant(1, user_id="last@e.com")
        assert assignments == []


# ---------------------------------------------------------------------------
# resolve_permissions_for_tenant
# ---------------------------------------------------------------------------


class TestResolvePermissionsForTenant:
    def test_empty_roles_returns_empty(self):
        perms = svc.resolve_permissions_for_tenant([], 1)
        assert perms == set()

    def test_student_perms(self):
        perms = svc.resolve_permissions_for_tenant(["student"], 1)
        assert "enrollments.read" in perms

    def test_admin_has_many_perms(self):
        perms = svc.resolve_permissions_for_tenant(["admin"], 1)
        assert len(perms) > 10

    def test_superadmin_returns_platform_perms(self):
        perms = svc.resolve_permissions_for_tenant(["superadmin"], 1)
        assert "platform.admin.write" in perms

    def test_caches_result(self):
        svc.resolve_permissions_for_tenant(["teacher"], 1)
        # Second call should hit cache (no error)
        perms2 = svc.resolve_permissions_for_tenant(["teacher"], 1)
        assert "grades.write" in perms2


# ---------------------------------------------------------------------------
# API endpoint: GET /api/admin/rbac/roles
# ---------------------------------------------------------------------------


class TestGetRolesEndpoint:
    def test_returns_roles_dict(self):
        response = client_local.get(
            "/api/admin/rbac/roles",
            headers=ADMIN_HEADERS,
        )
        assert response.status_code == 200
        body = response.json()
        assert "roles" in body
        assert "admin" in body["roles"]

    def test_requires_permission(self):
        student_headers = _auth_headers("stu@e.com", ["student"])
        response = client_local.get("/api/admin/rbac/roles", headers=student_headers)
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# API endpoint: GET /api/admin/rbac/assignments
# ---------------------------------------------------------------------------


class TestGetAssignmentsEndpoint:
    def test_returns_assignments(self):
        svc.assign_role_to_user(1, "qa@e.com", "teacher")
        response = client_local.get(
            "/api/admin/rbac/assignments",
            headers=ADMIN_HEADERS,
        )
        assert response.status_code == 200
        body = response.json()
        assert "assignments" in body
        assert isinstance(body["assignments"], list)

    def test_filter_by_user_id_query(self):
        svc.assign_role_to_user(1, "filtered@e.com", "auditor")
        response = client_local.get(
            "/api/admin/rbac/assignments?user_id=filtered@e.com",
            headers=ADMIN_HEADERS,
        )
        assert response.status_code == 200
        body = response.json()
        assert all(a["user_id"] == "filtered@e.com" for a in body["assignments"])


# ---------------------------------------------------------------------------
# API endpoint: DELETE /api/admin/rbac/assignments/{user_id}/{role}
# ---------------------------------------------------------------------------


class TestDeleteAssignmentEndpoint:
    def test_revoke_succeeds(self):
        svc.assign_role_to_user(1, "revoke@e.com", "teacher")
        response = client_local.delete(
            "/api/admin/rbac/assignments/revoke@e.com/teacher",
            headers=ADMIN_HEADERS,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["removed"] is True

    def test_self_revoke_forbidden(self):
        # owner@example.com tries to revoke their own role
        response = client_local.delete(
            "/api/admin/rbac/assignments/owner@example.com/admin",
            headers=ADMIN_HEADERS,
        )
        assert response.status_code == 403

    def test_cannot_revoke_higher_privilege_role(self):
        # admin (level 50) cannot revoke superadmin (level 100) from another user
        # First: make sure superadmin role exists for that user in platform tenant
        svc._tenant_user_roles_state.setdefault(1, {})
        svc._tenant_user_roles_state[1]["victim@e.com"] = {"superadmin"}
        response = client_local.delete(
            "/api/admin/rbac/assignments/victim@e.com/superadmin",
            headers=ADMIN_HEADERS,
        )
        # Should be forbidden - admin can't touch superadmin
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# Role hierarchy governance via POST /api/admin/rbac/assign
# ---------------------------------------------------------------------------


class TestRoleHierarchyGovernance:
    def test_admin_cannot_assign_superadmin(self):
        response = client_local.post(
            "/api/admin/rbac/assign",
            headers=ADMIN_HEADERS,
            json={"user_id": "target@e.com", "role": "superadmin"},
        )
        # superadmin is platform-only role
        assert response.status_code == 403

    def test_admin_cannot_assign_admin_to_other(self):
        """Admin (level 50) cannot assign admin (level 50) to another user — equal level blocked."""
        response = client_local.post(
            "/api/admin/rbac/assign",
            headers=ADMIN_HEADERS,
            json={"user_id": "target2@e.com", "role": "admin"},
        )
        assert response.status_code == 403

    def test_admin_can_assign_lower_privilege_role(self):
        response = client_local.post(
            "/api/admin/rbac/assign",
            headers=ADMIN_HEADERS,
            json={"user_id": "newstudent@e.com", "role": "student"},
        )
        assert response.status_code == 200

    def test_self_role_assignment_forbidden(self):
        response = client_local.post(
            "/api/admin/rbac/assign",
            headers=ADMIN_HEADERS,
            json={"user_id": "owner@example.com", "role": "teacher"},
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# add_or_update_role_for_tenant_with_replay
# ---------------------------------------------------------------------------


class TestAddOrUpdateRoleWithReplay:
    def test_new_role_is_not_replay(self):
        result = svc.add_or_update_role_for_tenant_with_replay(1, "newrole", ["x.read"])
        assert result["idempotent_replay"] is False

    def test_identical_call_is_replay(self):
        svc.add_or_update_role_for_tenant_with_replay(1, "replayrole", ["y.read"])
        result = svc.add_or_update_role_for_tenant_with_replay(1, "replayrole", ["y.read"])
        assert result["idempotent_replay"] is True

    def test_different_permissions_is_not_replay(self):
        svc.add_or_update_role_for_tenant_with_replay(1, "changedole", ["a.read"])
        result = svc.add_or_update_role_for_tenant_with_replay(1, "changedole", ["a.read", "b.write"])
        assert result["idempotent_replay"] is False
