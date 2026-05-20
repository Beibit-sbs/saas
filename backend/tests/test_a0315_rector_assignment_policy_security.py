"""A-031.5-RUNTIME escalation policy and security tests.

Tests: EscalationPolicy CRUD/validation, RBAC, tenant isolation,
no-hard-delete enforcement, no-live-dispatch.
Uses MagicMock(spec=Session) — no real DB required.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import (
    DomainValidationError,
    TenantResourceNotFoundError,
)
from app.modules.rector_assignment_workflow import permissions
from app.modules.rector_assignment_workflow.models import (
    AuditEventType,
    EscalationTargetRole,
    RectorAssignmentEscalationPolicy,
)
from app.modules.rector_assignment_workflow.schemas import (
    RectorAssignmentEscalationPolicyCreateRequest,
    RectorAssignmentEscalationPolicyUpdateRequest,
    RectorAssignmentEscalationPolicyResponse,
    RectorAssignmentEscalationPolicyListResponse,
)
from app.main import app
from app.modules.rector_assignment_workflow.dependencies import get_rector_assignment_db
from tests.conftest import ADMIN_HEADERS, _auth_headers, client

BASE = "/api/admin/rector-assignments"

# Numeric actor so int(actor) works in routes that need user_id
ADMIN_INT_HEADERS = _auth_headers("1", ["admin"], tenant_id=1)
NO_HEADERS: dict = {}
VIEWER_HEADERS = _auth_headers("viewer@example.com", ["viewer"], tenant_id=1)


@pytest.fixture(autouse=True)
def _override_db():
    session = MagicMock(spec=Session)
    app.dependency_overrides[get_rector_assignment_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_rector_assignment_db, None)


def _mock_escalation_policy(
    *,
    policy_id: int = 1,
    tenant_id: int = 1,
    priority: str = "NORMAL",
    level: int = 1,
    to_role: str = "CONTROLLER",
    hours: int = 72,
    manual_confirm: bool = True,
    is_active: bool = True,
    archived_at: datetime | None = None,
) -> MagicMock:
    mock = MagicMock()
    mock.id = policy_id
    mock.tenant_id = tenant_id
    mock.assignment_priority = priority
    mock.escalation_level = level
    mock.escalate_to_role = to_role
    mock.escalate_after_hours = hours
    mock.require_manual_confirmation = manual_confirm
    mock.is_active = is_active
    mock.created_by_user_id = 1
    mock.created_at = datetime(2025, 1, 1)
    mock.updated_at = datetime(2025, 1, 1)
    mock.archived_at = archived_at
    return mock


# ===========================================================================
# 1. EscalationTargetRole constants
# ===========================================================================

class TestEscalationTargetRoleConstants:
    def test_controller(self):
        assert EscalationTargetRole.CONTROLLER == "CONTROLLER"

    def test_prorector(self):
        assert EscalationTargetRole.PRORECTOR == "PRORECTOR"

    def test_rector(self):
        assert EscalationTargetRole.RECTOR == "RECTOR"

    def test_platform_admin(self):
        assert EscalationTargetRole.PLATFORM_ADMIN == "PLATFORM_ADMIN"

    def test_all_frozenset(self):
        assert isinstance(EscalationTargetRole.ALL, frozenset)
        assert len(EscalationTargetRole.ALL) == 4


# ===========================================================================
# 2. RectorAssignmentEscalationPolicy model
# ===========================================================================

class TestEscalationPolicyModel:
    def test_tablename(self):
        assert RectorAssignmentEscalationPolicy.__tablename__ == "rector_assignment_escalation_policies"

    def test_has_tenant_id(self):
        assert hasattr(RectorAssignmentEscalationPolicy, "tenant_id")

    def test_has_assignment_priority(self):
        assert hasattr(RectorAssignmentEscalationPolicy, "assignment_priority")

    def test_has_escalation_level(self):
        assert hasattr(RectorAssignmentEscalationPolicy, "escalation_level")

    def test_has_escalate_to_role(self):
        assert hasattr(RectorAssignmentEscalationPolicy, "escalate_to_role")

    def test_has_escalate_after_hours(self):
        assert hasattr(RectorAssignmentEscalationPolicy, "escalate_after_hours")

    def test_has_require_manual_confirmation(self):
        assert hasattr(RectorAssignmentEscalationPolicy, "require_manual_confirmation")

    def test_has_is_active(self):
        assert hasattr(RectorAssignmentEscalationPolicy, "is_active")

    def test_has_archived_at(self):
        assert hasattr(RectorAssignmentEscalationPolicy, "archived_at")

    def test_has_created_by_user_id(self):
        assert hasattr(RectorAssignmentEscalationPolicy, "created_by_user_id")


# ===========================================================================
# 3. Escalation Policy schema validation
# ===========================================================================

class TestEscalationPolicySchemas:
    def test_create_valid(self):
        req = RectorAssignmentEscalationPolicyCreateRequest(
            assignment_priority="NORMAL",
            escalation_level=1,
            escalate_to_role="CONTROLLER",
        )
        assert req.assignment_priority == "NORMAL"
        assert req.escalation_level == 1
        assert req.escalate_to_role == "CONTROLLER"
        assert req.escalate_after_hours == 72
        assert req.require_manual_confirmation is True

    def test_require_manual_confirmation_default_true(self):
        req = RectorAssignmentEscalationPolicyCreateRequest(
            assignment_priority="HIGH",
            escalation_level=2,
            escalate_to_role="PRORECTOR",
        )
        assert req.require_manual_confirmation is True

    def test_escalation_level_bounds(self):
        # Level 0 should fail
        with pytest.raises(Exception):
            RectorAssignmentEscalationPolicyCreateRequest(
                assignment_priority="NORMAL",
                escalation_level=0,
                escalate_to_role="CONTROLLER",
            )
        # Level 5 should fail
        with pytest.raises(Exception):
            RectorAssignmentEscalationPolicyCreateRequest(
                assignment_priority="NORMAL",
                escalation_level=5,
                escalate_to_role="CONTROLLER",
            )

    def test_escalation_level_max_4(self):
        req = RectorAssignmentEscalationPolicyCreateRequest(
            assignment_priority="CRITICAL",
            escalation_level=4,
            escalate_to_role="PLATFORM_ADMIN",
        )
        assert req.escalation_level == 4

    def test_escalate_after_hours_ge_1(self):
        with pytest.raises(Exception):
            RectorAssignmentEscalationPolicyCreateRequest(
                assignment_priority="NORMAL",
                escalation_level=1,
                escalate_to_role="CONTROLLER",
                escalate_after_hours=0,
            )

    def test_update_request_all_optional(self):
        req = RectorAssignmentEscalationPolicyUpdateRequest()
        assert req.assignment_priority is None
        assert req.escalation_level is None
        assert req.escalate_to_role is None
        assert req.require_manual_confirmation is None


# ===========================================================================
# 4. Escalation Policy API — no auth returns 401/403
# ===========================================================================

class TestEscalationPolicyNoAuth:
    def test_list_no_auth(self):
        resp = client.get(f"{BASE}/escalation-policies")
        assert resp.status_code in (401, 403)

    def test_create_no_auth(self):
        resp = client.post(
            f"{BASE}/escalation-policies",
            json={"assignment_priority": "NORMAL", "escalation_level": 1, "escalate_to_role": "CONTROLLER"},
        )
        assert resp.status_code in (401, 403)

    def test_update_no_auth(self):
        resp = client.patch(
            f"{BASE}/escalation-policies/1",
            json={"escalate_to_role": "PRORECTOR"},
        )
        assert resp.status_code in (401, 403)

    def test_archive_no_auth(self):
        resp = client.post(f"{BASE}/escalation-policies/1/archive")
        assert resp.status_code in (401, 403)


# ===========================================================================
# 5. Escalation Policy API — authenticated routes
# ===========================================================================

class TestEscalationPolicyAuthenticatedRoutes:
    def test_list_returns_200(self):
        with patch(
            "app.modules.rector_assignment_workflow.router.list_escalation_policies",
            return_value=([], 0),
        ):
            resp = client.get(f"{BASE}/escalation-policies", headers=ADMIN_HEADERS)
            assert resp.status_code == 200
            assert resp.json()["items"] == []
            assert resp.json()["total"] == 0

    def test_create_returns_201(self):
        mock_policy = _mock_escalation_policy()
        with patch(
            "app.modules.rector_assignment_workflow.router.create_escalation_policy",
            return_value=mock_policy,
        ):
            resp = client.post(
                f"{BASE}/escalation-policies",
                json={"assignment_priority": "NORMAL", "escalation_level": 1, "escalate_to_role": "CONTROLLER"},
                headers=ADMIN_INT_HEADERS,
            )
            assert resp.status_code == 201

    def test_update_returns_200(self):
        mock_policy = _mock_escalation_policy()
        with patch(
            "app.modules.rector_assignment_workflow.router.update_escalation_policy",
            return_value=mock_policy,
        ):
            resp = client.patch(
                f"{BASE}/escalation-policies/1",
                json={"escalate_after_hours": 96},
                headers=ADMIN_INT_HEADERS,
            )
            assert resp.status_code == 200

    def test_archive_returns_200(self):
        mock_policy = _mock_escalation_policy(is_active=False, archived_at=datetime(2025, 1, 2))
        with patch(
            "app.modules.rector_assignment_workflow.router.archive_escalation_policy",
            return_value=mock_policy,
        ):
            resp = client.post(f"{BASE}/escalation-policies/1/archive", headers=ADMIN_INT_HEADERS)
            assert resp.status_code == 200

    def test_create_requires_priority(self):
        resp = client.post(
            f"{BASE}/escalation-policies",
            json={"escalation_level": 1, "escalate_to_role": "CONTROLLER"},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 422

    def test_create_requires_level(self):
        resp = client.post(
            f"{BASE}/escalation-policies",
            json={"assignment_priority": "NORMAL", "escalate_to_role": "CONTROLLER"},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 422

    def test_create_level_0_returns_422(self):
        resp = client.post(
            f"{BASE}/escalation-policies",
            json={"assignment_priority": "NORMAL", "escalation_level": 0, "escalate_to_role": "CONTROLLER"},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 422

    def test_not_found_returns_404(self):
        with patch(
            "app.modules.rector_assignment_workflow.router.update_escalation_policy",
            side_effect=TenantResourceNotFoundError("escalation policy 99 not found"),
        ):
            resp = client.patch(
                f"{BASE}/escalation-policies/99",
                json={"escalate_to_role": "RECTOR"},
                headers=ADMIN_INT_HEADERS,
            )
            assert resp.status_code == 404


# ===========================================================================
# 6. Escalation Policy service validation
# ===========================================================================

class TestEscalationPolicyServiceValidation:
    def test_update_archived_policy_raises(self):
        from app.modules.rector_assignment_workflow.service import update_escalation_policy
        db = MagicMock(spec=Session)
        mock_policy = MagicMock()
        mock_policy.is_active = False
        with patch(
            "app.modules.rector_assignment_workflow.service.repo_get_escalation_policy",
            return_value=mock_policy,
        ):
            with pytest.raises(DomainValidationError):
                update_escalation_policy(1, 1, 1, RectorAssignmentEscalationPolicyUpdateRequest(), db)

    def test_archive_already_archived_raises(self):
        from app.modules.rector_assignment_workflow.service import archive_escalation_policy
        db = MagicMock(spec=Session)
        mock_policy = MagicMock()
        mock_policy.is_active = False
        with patch(
            "app.modules.rector_assignment_workflow.service.repo_get_escalation_policy",
            return_value=mock_policy,
        ):
            with pytest.raises(DomainValidationError):
                archive_escalation_policy(1, 1, 1, db)

    def test_update_nonexistent_raises(self):
        from app.modules.rector_assignment_workflow.service import update_escalation_policy
        db = MagicMock(spec=Session)
        with patch(
            "app.modules.rector_assignment_workflow.service.repo_get_escalation_policy",
            return_value=None,
        ):
            with pytest.raises(TenantResourceNotFoundError):
                update_escalation_policy(1, 99, 1, RectorAssignmentEscalationPolicyUpdateRequest(), db)

    def test_archive_nonexistent_raises(self):
        from app.modules.rector_assignment_workflow.service import archive_escalation_policy
        db = MagicMock(spec=Session)
        with patch(
            "app.modules.rector_assignment_workflow.service.repo_get_escalation_policy",
            return_value=None,
        ):
            with pytest.raises(TenantResourceNotFoundError):
                archive_escalation_policy(1, 99, 1, db)

    def test_create_writes_audit(self):
        from app.modules.rector_assignment_workflow.service import create_escalation_policy
        db = MagicMock(spec=Session)
        mock_policy = _mock_escalation_policy()
        payload = RectorAssignmentEscalationPolicyCreateRequest(
            assignment_priority="NORMAL",
            escalation_level=1,
            escalate_to_role="CONTROLLER",
        )
        with patch(
            "app.modules.rector_assignment_workflow.service.repo_create_escalation_policy",
            return_value=mock_policy,
        ), patch(
            "app.modules.rector_assignment_workflow.service._write_audit",
        ) as mock_audit, patch(
            "app.modules.rector_assignment_workflow.service.validate_tenant_id_provided",
        ):
            create_escalation_policy(1, 1, payload, db)
            assert mock_audit.called


# ===========================================================================
# 7. RBAC: permission string correctness
# ===========================================================================

class TestRbacPermissions:
    def test_outbox_read_string(self):
        assert permissions.OUTBOX_READ == "admin.rector_assignments.outbox.read"

    def test_outbox_manage_string(self):
        assert permissions.OUTBOX_MANAGE == "admin.rector_assignments.outbox.manage"

    def test_sla_manage_string(self):
        assert permissions.SLA_MANAGE == "admin.rector_assignments.sla.manage"

    def test_escalation_policy_manage_string(self):
        assert permissions.ESCALATION_POLICY_MANAGE == "admin.rector_assignments.escalation_policy.manage"

    def test_legacy_permissions_intact(self):
        assert permissions.CREATE == "admin.rector_assignments.create"
        assert permissions.READ == "admin.rector_assignments.read"
        assert permissions.ADMIN == "admin.rector_assignments.admin"
        assert permissions.DASHBOARD_READ == "admin.rector_assignments.dashboard.read"


# ===========================================================================
# 8. Security: no hard delete in any new entity
# ===========================================================================

class TestNoHardDeleteSecurity:
    def test_sla_policy_has_no_delete_method(self):
        """SLA policy should be archived (soft delete) not hard deleted."""
        from app.modules.rector_assignment_workflow import service as svc
        # Archive exists, delete should NOT exist
        assert hasattr(svc, "archive_sla_policy")
        assert not hasattr(svc, "delete_sla_policy")
        assert not hasattr(svc, "hard_delete_sla_policy")

    def test_escalation_policy_has_no_delete_method(self):
        from app.modules.rector_assignment_workflow import service as svc
        assert hasattr(svc, "archive_escalation_policy")
        assert not hasattr(svc, "delete_escalation_policy")
        assert not hasattr(svc, "hard_delete_escalation_policy")

    def test_outbox_has_no_delete_method(self):
        from app.modules.rector_assignment_workflow import service as svc
        assert hasattr(svc, "cancel_outbox_event")
        assert not hasattr(svc, "delete_outbox_event")
        assert not hasattr(svc, "hard_delete_outbox_event")


# ===========================================================================
# 9. Security: no live dispatch or provider calls
# ===========================================================================

class TestNoLiveDispatch:
    def test_no_smtp_import_in_service(self):
        import app.modules.rector_assignment_workflow.service as svc_module
        import inspect
        source = inspect.getsource(svc_module)
        assert "smtplib" not in source
        assert "send_mail" not in source.lower() or "_send_mail" not in source.lower()

    def test_no_sms_provider_in_service(self):
        import app.modules.rector_assignment_workflow.service as svc_module
        import inspect
        source = inspect.getsource(svc_module)
        assert "twilio" not in source.lower()
        assert "vonage" not in source.lower()

    def test_no_external_http_in_service(self):
        import app.modules.rector_assignment_workflow.service as svc_module
        import inspect
        source = inspect.getsource(svc_module)
        assert "requests.post" not in source
        assert "httpx.post" not in source

    def test_no_smtp_in_router(self):
        import app.modules.rector_assignment_workflow.router as router_module
        import inspect
        source = inspect.getsource(router_module)
        assert "smtplib" not in source


# ===========================================================================
# 10. Outbox lifecycle wiring verification
# ===========================================================================

class TestOutboxLifecycleWiring:
    """Verify outbox events are created during lifecycle transitions."""

    def test_create_assignment_creates_outbox_event(self):
        from app.modules.rector_assignment_workflow.service import create_assignment
        from app.modules.rector_assignment_workflow.schemas import AssignmentCreateRequest
        db = MagicMock(spec=Session)
        mock_assignment = MagicMock()
        mock_assignment.id = 1
        mock_assignment.tenant_id = 1
        mock_assignment.status = "DRAFT"
        mock_outbox = MagicMock()
        mock_outbox.id = 100

        payload = AssignmentCreateRequest(title="Test", priority="NORMAL", recurrence_type="NONE")

        with patch("app.modules.rector_assignment_workflow.service.repo_create_assignment", return_value=mock_assignment), \
             patch("app.modules.rector_assignment_workflow.service.repo_create_status_history"), \
             patch("app.modules.rector_assignment_workflow.service._write_audit"), \
             patch("app.modules.rector_assignment_workflow.service.repo_create_outbox_event", return_value=mock_outbox) as mock_queue, \
             patch("app.modules.rector_assignment_workflow.service.repo_create_audit_event"), \
             patch("app.modules.rector_assignment_workflow.service.log_admin_action"), \
             patch("app.modules.rector_assignment_workflow.service.validate_tenant_id_provided"):
            create_assignment(1, 1, "admin", payload, db)
            # Outbox event should have been created
            assert mock_queue.called

    def test_complete_assignment_creates_outbox_event(self):
        from app.modules.rector_assignment_workflow.service import complete_assignment
        db = MagicMock(spec=Session)
        mock_assignment = MagicMock()
        mock_assignment.id = 1
        mock_assignment.tenant_id = 1
        mock_assignment.status = "REPORT_SUBMITTED"
        mock_outbox = MagicMock()
        mock_outbox.id = 101

        with patch("app.modules.rector_assignment_workflow.service.repo_require_assignment", return_value=mock_assignment), \
             patch("app.modules.rector_assignment_workflow.service._transition"), \
             patch("app.modules.rector_assignment_workflow.service._write_audit"), \
             patch("app.modules.rector_assignment_workflow.service.repo_create_outbox_event", return_value=mock_outbox) as mock_queue, \
             patch("app.modules.rector_assignment_workflow.service.repo_create_audit_event"), \
             patch("app.modules.rector_assignment_workflow.service.validate_tenant_id_provided"):
            complete_assignment(1, 1, 1, "admin", None, db)
            assert mock_queue.called

    def test_escalate_assignment_creates_outbox_event(self):
        from app.modules.rector_assignment_workflow.service import escalate_assignment
        from app.modules.rector_assignment_workflow.schemas import EscalationRequest
        db = MagicMock(spec=Session)
        mock_assignment = MagicMock()
        mock_assignment.id = 1
        mock_assignment.tenant_id = 1
        mock_assignment.status = "OVERDUE"
        mock_outbox = MagicMock()
        mock_outbox.id = 102
        mock_escalation = MagicMock()
        mock_escalation.id = 10

        payload = EscalationRequest(reason="past due", escalation_level=1, escalated_to_role="dean")

        with patch("app.modules.rector_assignment_workflow.service.repo_require_assignment", return_value=mock_assignment), \
             patch("app.modules.rector_assignment_workflow.service._transition"), \
             patch("app.modules.rector_assignment_workflow.service.repo_create_escalation", return_value=mock_escalation), \
             patch("app.modules.rector_assignment_workflow.service._write_audit"), \
             patch("app.modules.rector_assignment_workflow.service.repo_create_outbox_event", return_value=mock_outbox) as mock_queue, \
             patch("app.modules.rector_assignment_workflow.service.repo_create_audit_event"), \
             patch("app.modules.rector_assignment_workflow.service.validate_tenant_id_provided"):
            escalate_assignment(1, 1, 1, "admin", payload, db)
            assert mock_queue.called


# ===========================================================================
# 11. Tenant isolation checks
# ===========================================================================

class TestTenantIsolation:
    def test_list_sla_policies_tenant_required(self):
        from app.modules.rector_assignment_workflow.service import list_sla_policies
        db = MagicMock(spec=Session)
        with pytest.raises(Exception):
            list_sla_policies(0, db)

    def test_list_escalation_policies_tenant_required(self):
        from app.modules.rector_assignment_workflow.service import list_escalation_policies
        db = MagicMock(spec=Session)
        with pytest.raises(Exception):
            list_escalation_policies(0, db)

    def test_list_outbox_events_tenant_required(self):
        from app.modules.rector_assignment_workflow.service import list_outbox_events
        db = MagicMock(spec=Session)
        with pytest.raises(Exception):
            list_outbox_events(0, db)
