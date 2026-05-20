"""A-031.5-RUNTIME outbox and SLA policy tests.

Tests: outbox event creation, status transitions, SLA policy CRUD,
outbox API routes, SLA API routes.
Uses MagicMock(spec=Session) — no real DB required.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, call
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import (
    DomainValidationError,
    TenantResourceNotFoundError,
)
from app.modules.rector_assignment_workflow import permissions
from app.modules.rector_assignment_workflow.models import (
    AuditEventType,
    OutboxChannel,
    OutboxEventType,
    OutboxStatus,
    RectorAssignment,
    RectorAssignmentOutboxEvent,
    RectorAssignmentSlaPolicy,
    SlaPolicyPriority,
)
from app.modules.rector_assignment_workflow.schemas import (
    RectorAssignmentSlaPolicyCreateRequest,
    RectorAssignmentSlaPolicyUpdateRequest,
    RectorAssignmentSlaPolicyResponse,
)
from app.main import app
from app.modules.rector_assignment_workflow.dependencies import get_rector_assignment_db
from tests.conftest import ADMIN_HEADERS, _auth_headers, client

BASE = "/api/admin/rector-assignments"

# Numeric actor headers so int(actor) succeeds in routes that need user_id
ADMIN_INT_HEADERS = _auth_headers("1", ["admin"], tenant_id=1)
SLA_MANAGE_HEADERS = _auth_headers("1", ["admin"], tenant_id=1)
OUTBOX_READ_HEADERS = _auth_headers("1", ["admin"], tenant_id=1)
OUTBOX_MANAGE_HEADERS = _auth_headers("1", ["admin"], tenant_id=1)
NO_HEADERS: dict = {}


@pytest.fixture(autouse=True)
def _override_db():
    session = MagicMock(spec=Session)
    app.dependency_overrides[get_rector_assignment_db] = lambda: session
    yield
    app.dependency_overrides.pop(get_rector_assignment_db, None)


# ===========================================================================
# 1. OutboxStatus constants
# ===========================================================================

class TestOutboxStatusConstants:
    def test_pending_constant(self):
        assert OutboxStatus.PENDING == "PENDING"

    def test_ready_constant(self):
        assert OutboxStatus.READY == "READY"

    def test_cancelled_constant(self):
        assert OutboxStatus.CANCELLED == "CANCELLED"

    def test_all_first_runtime_set(self):
        assert OutboxStatus.ALL_FIRST_RUNTIME == frozenset({"PENDING", "READY", "CANCELLED"})

    def test_no_dispatched_status(self):
        assert "DISPATCHED" not in OutboxStatus.ALL_FIRST_RUNTIME

    def test_no_failed_status(self):
        assert "FAILED" not in OutboxStatus.ALL_FIRST_RUNTIME


# ===========================================================================
# 2. OutboxChannel constants
# ===========================================================================

class TestOutboxChannelConstants:
    def test_in_app_constant(self):
        assert OutboxChannel.IN_APP == "IN_APP"

    def test_email_constant(self):
        assert OutboxChannel.EMAIL == "EMAIL"

    def test_sms_constant(self):
        assert OutboxChannel.SMS == "SMS"

    def test_all_channels(self):
        assert OutboxChannel.ALL == frozenset({"IN_APP", "EMAIL", "SMS"})


# ===========================================================================
# 3. OutboxEventType constants
# ===========================================================================

class TestOutboxEventTypeConstants:
    def test_assignment_created(self):
        assert OutboxEventType.ASSIGNMENT_CREATED == "rector_assignment.created"

    def test_assignment_assigned(self):
        assert OutboxEventType.ASSIGNMENT_ASSIGNED == "rector_assignment.assigned"

    def test_assignment_accepted(self):
        assert OutboxEventType.ASSIGNMENT_ACCEPTED == "rector_assignment.accepted"

    def test_report_submitted(self):
        assert OutboxEventType.REPORT_SUBMITTED == "rector_assignment.report_submitted"

    def test_returned_for_revision(self):
        assert OutboxEventType.RETURNED_FOR_REVISION == "rector_assignment.returned_for_revision"

    def test_assignment_completed(self):
        assert OutboxEventType.ASSIGNMENT_COMPLETED == "rector_assignment.completed"

    def test_assignment_escalated(self):
        assert OutboxEventType.ASSIGNMENT_ESCALATED == "rector_assignment.escalated"

    def test_overdue_detected(self):
        assert OutboxEventType.OVERDUE_DETECTED == "rector_assignment.overdue_detected"

    def test_comment_added(self):
        assert OutboxEventType.COMMENT_ADDED == "rector_assignment.comment_added"

    def test_evidence_attached(self):
        assert OutboxEventType.EVIDENCE_ATTACHED == "rector_assignment.evidence_attached"

    def test_all_event_types_set(self):
        assert len(OutboxEventType.ALL) == 10

    def test_all_is_frozenset(self):
        assert isinstance(OutboxEventType.ALL, frozenset)


# ===========================================================================
# 4. SlaPolicyPriority constants
# ===========================================================================

class TestSlaPolicyPriorityConstants:
    def test_normal(self):
        assert SlaPolicyPriority.NORMAL == "NORMAL"

    def test_high(self):
        assert SlaPolicyPriority.HIGH == "HIGH"

    def test_urgent(self):
        assert SlaPolicyPriority.URGENT == "URGENT"

    def test_critical(self):
        assert SlaPolicyPriority.CRITICAL == "CRITICAL"


# ===========================================================================
# 5. AuditEventType A-031.5 additions
# ===========================================================================

class TestAuditEventTypeAdditions:
    def test_outbox_event_created(self):
        assert AuditEventType.OUTBOX_EVENT_CREATED == "OUTBOX_EVENT_CREATED"

    def test_outbox_event_ready_marked(self):
        assert AuditEventType.OUTBOX_EVENT_READY_MARKED == "OUTBOX_EVENT_READY_MARKED"

    def test_outbox_event_cancelled(self):
        assert AuditEventType.OUTBOX_EVENT_CANCELLED == "OUTBOX_EVENT_CANCELLED"

    def test_sla_policy_created(self):
        assert AuditEventType.SLA_POLICY_CREATED == "SLA_POLICY_CREATED"

    def test_sla_policy_updated(self):
        assert AuditEventType.SLA_POLICY_UPDATED == "SLA_POLICY_UPDATED"

    def test_sla_policy_archived(self):
        assert AuditEventType.SLA_POLICY_ARCHIVED == "SLA_POLICY_ARCHIVED"

    def test_escalation_policy_created(self):
        assert AuditEventType.ESCALATION_POLICY_CREATED == "ESCALATION_POLICY_CREATED"

    def test_escalation_policy_updated(self):
        assert AuditEventType.ESCALATION_POLICY_UPDATED == "ESCALATION_POLICY_UPDATED"

    def test_escalation_policy_archived(self):
        assert AuditEventType.ESCALATION_POLICY_ARCHIVED == "ESCALATION_POLICY_ARCHIVED"

    def test_overdue_event_queued(self):
        assert AuditEventType.OVERDUE_EVENT_QUEUED == "OVERDUE_EVENT_QUEUED"


# ===========================================================================
# 6. RectorAssignmentOutboxEvent model
# ===========================================================================

class TestOutboxEventModel:
    def test_tablename(self):
        assert RectorAssignmentOutboxEvent.__tablename__ == "rector_assignment_outbox_events"

    def test_has_tenant_id(self):
        assert hasattr(RectorAssignmentOutboxEvent, "tenant_id")

    def test_has_assignment_id(self):
        assert hasattr(RectorAssignmentOutboxEvent, "assignment_id")

    def test_has_event_type(self):
        assert hasattr(RectorAssignmentOutboxEvent, "event_type")

    def test_has_status(self):
        assert hasattr(RectorAssignmentOutboxEvent, "status")

    def test_has_channel(self):
        assert hasattr(RectorAssignmentOutboxEvent, "channel")

    def test_has_payload_json(self):
        assert hasattr(RectorAssignmentOutboxEvent, "payload_json")

    def test_has_retry_count(self):
        assert hasattr(RectorAssignmentOutboxEvent, "retry_count")

    def test_has_recipient_user_id(self):
        assert hasattr(RectorAssignmentOutboxEvent, "recipient_user_id")

    def test_has_created_at(self):
        assert hasattr(RectorAssignmentOutboxEvent, "created_at")

    def test_has_updated_at(self):
        assert hasattr(RectorAssignmentOutboxEvent, "updated_at")

    def test_has_next_retry_at(self):
        assert hasattr(RectorAssignmentOutboxEvent, "next_retry_at")


# ===========================================================================
# 7. RectorAssignmentSlaPolicy model
# ===========================================================================

class TestSlaPolicyModel:
    def test_tablename(self):
        assert RectorAssignmentSlaPolicy.__tablename__ == "rector_assignment_sla_policies"

    def test_has_tenant_id(self):
        assert hasattr(RectorAssignmentSlaPolicy, "tenant_id")

    def test_has_name(self):
        assert hasattr(RectorAssignmentSlaPolicy, "name")

    def test_has_due_days(self):
        assert hasattr(RectorAssignmentSlaPolicy, "due_days")

    def test_has_warning_before_hours(self):
        assert hasattr(RectorAssignmentSlaPolicy, "warning_before_hours")

    def test_has_overdue_after_hours(self):
        assert hasattr(RectorAssignmentSlaPolicy, "overdue_after_hours")

    def test_has_escalation_after_hours(self):
        assert hasattr(RectorAssignmentSlaPolicy, "escalation_after_hours")

    def test_has_is_active(self):
        assert hasattr(RectorAssignmentSlaPolicy, "is_active")

    def test_has_archived_at(self):
        assert hasattr(RectorAssignmentSlaPolicy, "archived_at")

    def test_has_created_by_user_id(self):
        assert hasattr(RectorAssignmentSlaPolicy, "created_by_user_id")


# ===========================================================================
# 8. New permissions constants
# ===========================================================================

class TestNewPermissions:
    def test_outbox_read(self):
        assert permissions.OUTBOX_READ == "admin.rector_assignments.outbox.read"

    def test_outbox_manage(self):
        assert permissions.OUTBOX_MANAGE == "admin.rector_assignments.outbox.manage"

    def test_sla_manage(self):
        assert permissions.SLA_MANAGE == "admin.rector_assignments.sla.manage"

    def test_escalation_policy_manage(self):
        assert permissions.ESCALATION_POLICY_MANAGE == "admin.rector_assignments.escalation_policy.manage"

    def test_all_permissions_includes_outbox_read(self):
        assert permissions.OUTBOX_READ in permissions.ALL_PERMISSIONS

    def test_all_permissions_includes_outbox_manage(self):
        assert permissions.OUTBOX_MANAGE in permissions.ALL_PERMISSIONS

    def test_all_permissions_includes_sla_manage(self):
        assert permissions.SLA_MANAGE in permissions.ALL_PERMISSIONS

    def test_all_permissions_includes_escalation_policy_manage(self):
        assert permissions.ESCALATION_POLICY_MANAGE in permissions.ALL_PERMISSIONS

    def test_all_permissions_count(self):
        # Original 20 + 4 new = 24
        assert len(permissions.ALL_PERMISSIONS) == 24


# ===========================================================================
# 9. SLA Policy schema validation
# ===========================================================================

class TestSlaPolicySchemas:
    def test_create_request_valid(self):
        req = RectorAssignmentSlaPolicyCreateRequest(
            name="Standard SLA",
            due_days=14,
        )
        assert req.name == "Standard SLA"
        assert req.due_days == 14
        assert req.warning_before_hours == 48
        assert req.overdue_after_hours == 0
        assert req.escalation_after_hours == 72

    def test_create_request_requires_name(self):
        with pytest.raises(Exception):
            RectorAssignmentSlaPolicyCreateRequest(due_days=14)

    def test_create_request_requires_due_days(self):
        with pytest.raises(Exception):
            RectorAssignmentSlaPolicyCreateRequest(name="Test SLA")

    def test_create_request_due_days_ge_1(self):
        with pytest.raises(Exception):
            RectorAssignmentSlaPolicyCreateRequest(name="Test SLA", due_days=0)

    def test_create_request_with_priority(self):
        req = RectorAssignmentSlaPolicyCreateRequest(
            name="High Priority SLA",
            priority="HIGH",
            due_days=7,
        )
        assert req.priority == "HIGH"

    def test_update_request_all_optional(self):
        req = RectorAssignmentSlaPolicyUpdateRequest()
        assert req.name is None
        assert req.due_days is None

    def test_update_request_due_days_ge_1(self):
        with pytest.raises(Exception):
            RectorAssignmentSlaPolicyUpdateRequest(due_days=0)


# ===========================================================================
# 10. Outbox API — no auth returns 401/403
# ===========================================================================

class TestOutboxNoAuth:
    def test_list_outbox_no_auth(self):
        resp = client.get(f"{BASE}/outbox")
        assert resp.status_code in (401, 403)

    def test_list_assignment_outbox_no_auth(self):
        resp = client.get(f"{BASE}/1/outbox")
        assert resp.status_code in (401, 403)

    def test_mark_ready_no_auth(self):
        resp = client.post(f"{BASE}/1/outbox/1/ready")
        assert resp.status_code in (401, 403)

    def test_cancel_outbox_no_auth(self):
        resp = client.post(f"{BASE}/1/outbox/1/cancel")
        assert resp.status_code in (401, 403)


# ===========================================================================
# 11. SLA Policy API — no auth returns 401/403
# ===========================================================================

class TestSlaPolicyNoAuth:
    def test_list_sla_policies_no_auth(self):
        resp = client.get(f"{BASE}/sla-policies")
        assert resp.status_code in (401, 403)

    def test_create_sla_policy_no_auth(self):
        resp = client.post(f"{BASE}/sla-policies", json={"name": "Test", "due_days": 7})
        assert resp.status_code in (401, 403)

    def test_update_sla_policy_no_auth(self):
        resp = client.patch(f"{BASE}/sla-policies/1", json={"name": "Updated"})
        assert resp.status_code in (401, 403)

    def test_archive_sla_policy_no_auth(self):
        resp = client.post(f"{BASE}/sla-policies/1/archive")
        assert resp.status_code in (401, 403)


# ===========================================================================
# 12. Outbox API — authenticated routes return 200
# ===========================================================================

class TestOutboxAuthenticatedRoutes:
    def test_list_all_outbox_returns_200(self):
        with patch(
            "app.modules.rector_assignment_workflow.router.list_outbox_events",
            return_value=([], 0),
        ):
            resp = client.get(f"{BASE}/outbox", headers=ADMIN_HEADERS)
            assert resp.status_code == 200
            assert resp.json()["items"] == []
            assert resp.json()["total"] == 0

    def test_list_outbox_with_status_filter(self):
        with patch(
            "app.modules.rector_assignment_workflow.router.list_outbox_events",
            return_value=([], 0),
        ):
            resp = client.get(f"{BASE}/outbox?status=PENDING", headers=ADMIN_HEADERS)
            assert resp.status_code == 200

    def test_list_assignment_outbox_returns_200(self):
        with patch(
            "app.modules.rector_assignment_workflow.router.list_assignment_outbox_events",
            return_value=([], 0),
        ):
            resp = client.get(f"{BASE}/1/outbox", headers=ADMIN_HEADERS)
            assert resp.status_code == 200

    def test_mark_outbox_ready_returns_200(self):
        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.tenant_id = 1
        mock_event.assignment_id = 1
        mock_event.event_type = "rector_assignment.created"
        mock_event.recipient_user_id = None
        mock_event.recipient_role = None
        mock_event.channel = "IN_APP"
        mock_event.payload_json = {}
        mock_event.status = "READY"
        mock_event.retry_count = 0
        mock_event.next_retry_at = None
        from datetime import datetime
        mock_event.created_at = datetime(2025, 1, 1)
        mock_event.updated_at = datetime(2025, 1, 1)
        with patch(
            "app.modules.rector_assignment_workflow.router.mark_outbox_event_ready",
            return_value=mock_event,
        ):
            resp = client.post(f"{BASE}/1/outbox/1/ready", headers=OUTBOX_MANAGE_HEADERS)
            assert resp.status_code == 200
            assert resp.json()["status"] == "READY"

    def test_cancel_outbox_event_returns_200(self):
        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.tenant_id = 1
        mock_event.assignment_id = 1
        mock_event.event_type = "rector_assignment.created"
        mock_event.recipient_user_id = None
        mock_event.recipient_role = None
        mock_event.channel = "IN_APP"
        mock_event.payload_json = {}
        mock_event.status = "CANCELLED"
        mock_event.retry_count = 0
        mock_event.next_retry_at = None
        from datetime import datetime
        mock_event.created_at = datetime(2025, 1, 1)
        mock_event.updated_at = datetime(2025, 1, 1)
        with patch(
            "app.modules.rector_assignment_workflow.router.cancel_outbox_event",
            return_value=mock_event,
        ):
            resp = client.post(f"{BASE}/1/outbox/1/cancel", headers=OUTBOX_MANAGE_HEADERS)
            assert resp.status_code == 200
            assert resp.json()["status"] == "CANCELLED"


# ===========================================================================
# 13. SLA Policy API — authenticated routes
# ===========================================================================

class TestSlaPolicyAuthenticatedRoutes:
    def _mock_policy(self):
        from datetime import datetime
        mock = MagicMock()
        mock.id = 1
        mock.tenant_id = 1
        mock.name = "Standard SLA"
        mock.priority = None
        mock.due_days = 14
        mock.warning_before_hours = 48
        mock.overdue_after_hours = 0
        mock.escalation_after_hours = 72
        mock.is_active = True
        mock.created_by_user_id = 1
        mock.created_at = datetime(2025, 1, 1)
        mock.updated_at = datetime(2025, 1, 1)
        mock.archived_at = None
        return mock

    def test_list_sla_policies_returns_200(self):
        with patch(
            "app.modules.rector_assignment_workflow.router.list_sla_policies",
            return_value=([], 0),
        ):
            resp = client.get(f"{BASE}/sla-policies", headers=ADMIN_HEADERS)
            assert resp.status_code == 200
            assert resp.json()["items"] == []

    def test_create_sla_policy_returns_201(self):
        mock_policy = self._mock_policy()
        with patch(
            "app.modules.rector_assignment_workflow.router.create_sla_policy",
            return_value=mock_policy,
        ):
            resp = client.post(
                f"{BASE}/sla-policies",
                json={"name": "Standard SLA", "due_days": 14},
                headers=SLA_MANAGE_HEADERS,
            )
            assert resp.status_code == 201

    def test_update_sla_policy_returns_200(self):
        mock_policy = self._mock_policy()
        with patch(
            "app.modules.rector_assignment_workflow.router.update_sla_policy",
            return_value=mock_policy,
        ):
            resp = client.patch(
                f"{BASE}/sla-policies/1",
                json={"name": "Updated SLA"},
                headers=SLA_MANAGE_HEADERS,
            )
            assert resp.status_code == 200

    def test_archive_sla_policy_returns_200(self):
        mock_policy = self._mock_policy()
        mock_policy.is_active = False
        with patch(
            "app.modules.rector_assignment_workflow.router.archive_sla_policy",
            return_value=mock_policy,
        ):
            resp = client.post(
                f"{BASE}/sla-policies/1/archive",
                headers=SLA_MANAGE_HEADERS,
            )
            assert resp.status_code == 200

    def test_create_sla_requires_name(self):
        resp = client.post(
            f"{BASE}/sla-policies",
            json={"due_days": 14},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 422

    def test_create_sla_requires_due_days(self):
        resp = client.post(
            f"{BASE}/sla-policies",
            json={"name": "Test"},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 422

    def test_sla_not_found_returns_404(self):
        with patch(
            "app.modules.rector_assignment_workflow.router.update_sla_policy",
            side_effect=TenantResourceNotFoundError("SLA policy 99 not found"),
        ):
            resp = client.patch(
                f"{BASE}/sla-policies/99",
                json={"name": "Updated"},
                headers=SLA_MANAGE_HEADERS,
            )
            assert resp.status_code == 404


# ===========================================================================
# 14. Service: outbox event cancel validation
# ===========================================================================

class TestOutboxServiceValidation:
    def test_cancel_already_cancelled_raises(self):
        from app.modules.rector_assignment_workflow.service import cancel_outbox_event

        db = MagicMock(spec=Session)
        mock_assignment = MagicMock()
        mock_assignment.id = 1
        mock_assignment.tenant_id = 1

        mock_event = MagicMock()
        mock_event.assignment_id = 1
        mock_event.status = "CANCELLED"

        with patch("app.modules.rector_assignment_workflow.service.repo_require_assignment", return_value=mock_assignment), \
             patch("app.modules.rector_assignment_workflow.service.repo_get_outbox_event", return_value=mock_event):
            with pytest.raises(DomainValidationError):
                cancel_outbox_event(1, 1, 1, 1, db)

    def test_mark_ready_not_pending_raises(self):
        from app.modules.rector_assignment_workflow.service import mark_outbox_event_ready

        db = MagicMock(spec=Session)
        mock_assignment = MagicMock()
        mock_assignment.id = 1
        mock_assignment.tenant_id = 1

        mock_event = MagicMock()
        mock_event.assignment_id = 1
        mock_event.status = "READY"

        with patch("app.modules.rector_assignment_workflow.service.repo_require_assignment", return_value=mock_assignment), \
             patch("app.modules.rector_assignment_workflow.service.repo_get_outbox_event", return_value=mock_event):
            with pytest.raises(DomainValidationError):
                mark_outbox_event_ready(1, 1, 1, 1, db)

    def test_outbox_event_not_found_raises(self):
        from app.modules.rector_assignment_workflow.service import mark_outbox_event_ready

        db = MagicMock(spec=Session)
        mock_assignment = MagicMock()

        with patch("app.modules.rector_assignment_workflow.service.repo_require_assignment", return_value=mock_assignment), \
             patch("app.modules.rector_assignment_workflow.service.repo_get_outbox_event", return_value=None):
            with pytest.raises(TenantResourceNotFoundError):
                mark_outbox_event_ready(1, 1, 99, 1, db)


# ===========================================================================
# 15. Service: SLA policy validation
# ===========================================================================

class TestSlaPolicyServiceValidation:
    def test_update_archived_sla_policy_raises(self):
        from app.modules.rector_assignment_workflow.service import update_sla_policy

        db = MagicMock(spec=Session)
        mock_policy = MagicMock()
        mock_policy.is_active = False

        with patch("app.modules.rector_assignment_workflow.service.repo_get_sla_policy", return_value=mock_policy):
            with pytest.raises(DomainValidationError):
                update_sla_policy(1, 1, 1, RectorAssignmentSlaPolicyUpdateRequest(name="test"), db)

    def test_archive_already_archived_raises(self):
        from app.modules.rector_assignment_workflow.service import archive_sla_policy

        db = MagicMock(spec=Session)
        mock_policy = MagicMock()
        mock_policy.is_active = False

        with patch("app.modules.rector_assignment_workflow.service.repo_get_sla_policy", return_value=mock_policy):
            with pytest.raises(DomainValidationError):
                archive_sla_policy(1, 1, 1, db)

    def test_update_nonexistent_sla_raises(self):
        from app.modules.rector_assignment_workflow.service import update_sla_policy

        db = MagicMock(spec=Session)
        with patch("app.modules.rector_assignment_workflow.service.repo_get_sla_policy", return_value=None):
            with pytest.raises(TenantResourceNotFoundError):
                update_sla_policy(1, 99, 1, RectorAssignmentSlaPolicyUpdateRequest(), db)

    def test_archive_nonexistent_sla_raises(self):
        from app.modules.rector_assignment_workflow.service import archive_sla_policy

        db = MagicMock(spec=Session)
        with patch("app.modules.rector_assignment_workflow.service.repo_get_sla_policy", return_value=None):
            with pytest.raises(TenantResourceNotFoundError):
                archive_sla_policy(1, 99, 1, db)
