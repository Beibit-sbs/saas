"""A-031.1-RUNTIME domain tests: rector assignment workflow service logic.

Tests: transition matrix, tenant validation, service invariants.
Uses MagicMock(spec=Session) — no real DB required.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import (
    DomainValidationError,
    TenantRequiredError,
    TenantResourceNotFoundError,
)
from app.modules.rector_assignment_workflow import permissions
from app.modules.rector_assignment_workflow.models import (
    AssignmentPriority,
    AssignmentStatus,
    AuditEventType,
    CommentVisibility,
    EscalationStatus,
    EvidenceType,
    ReportStatus,
    RectorAssignment,
    RectorAssignmentAuditEvent,
    RectorAssignmentComment,
    RectorAssignmentEscalation,
    RectorAssignmentEvidence,
    RectorAssignmentReport,
    RectorAssignmentStatusHistory,
    RectorAssignmentTemplate,
)


# ===========================================================================
# 1. Imports and module constants
# ===========================================================================

class TestModuleImports:
    def test_module_name_constant(self):
        from app.modules.rector_assignment_workflow import MODULE_NAME
        assert MODULE_NAME == "rector_assignment_workflow"

    def test_contract_version(self):
        from app.modules.rector_assignment_workflow import CONTRACT_VERSION
        assert CONTRACT_VERSION == "A-031.1"

    def test_uce_primary(self):
        from app.modules.rector_assignment_workflow import UCE_PRIMARY
        assert UCE_PRIMARY == "UCE-099"

    def test_permissions_importable(self):
        assert permissions.CREATE == "admin.rector_assignments.create"
        assert permissions.READ == "admin.rector_assignments.read"
        assert permissions.ASSIGN == "admin.rector_assignments.assign"
        assert permissions.DASHBOARD_READ == "admin.rector_assignments.dashboard.read"

    def test_all_permissions_frozenset(self):
        assert isinstance(permissions.ALL_PERMISSIONS, frozenset)
        assert len(permissions.ALL_PERMISSIONS) == 20

    def test_models_importable(self):
        assert RectorAssignment.__tablename__ == "rector_assignments"
        assert RectorAssignmentReport.__tablename__ == "rector_assignment_reports"
        assert RectorAssignmentAuditEvent.__tablename__ == "rector_assignment_audit_events"
        assert RectorAssignmentStatusHistory.__tablename__ == "rector_assignment_status_history"


# ===========================================================================
# 2. AssignmentStatus constants and transitions
# ===========================================================================

class TestAssignmentStatusTransitions:
    def test_all_statuses_present(self):
        assert AssignmentStatus.DRAFT in AssignmentStatus.ALL
        assert AssignmentStatus.ASSIGNED in AssignmentStatus.ALL
        assert AssignmentStatus.ACCEPTED in AssignmentStatus.ALL
        assert AssignmentStatus.IN_PROGRESS in AssignmentStatus.ALL
        assert AssignmentStatus.REPORT_SUBMITTED in AssignmentStatus.ALL
        assert AssignmentStatus.RETURNED_FOR_REVISION in AssignmentStatus.ALL
        assert AssignmentStatus.COMPLETED in AssignmentStatus.ALL
        assert AssignmentStatus.OVERDUE in AssignmentStatus.ALL
        assert AssignmentStatus.ESCALATED in AssignmentStatus.ALL
        assert AssignmentStatus.CANCELLED in AssignmentStatus.ALL
        assert AssignmentStatus.ARCHIVED in AssignmentStatus.ALL

    def test_terminal_statuses(self):
        assert AssignmentStatus.COMPLETED in AssignmentStatus.TERMINAL
        assert AssignmentStatus.CANCELLED in AssignmentStatus.TERMINAL
        assert AssignmentStatus.ARCHIVED in AssignmentStatus.TERMINAL
        assert AssignmentStatus.DRAFT not in AssignmentStatus.TERMINAL

    def test_active_statuses(self):
        assert AssignmentStatus.ASSIGNED in AssignmentStatus.ACTIVE
        assert AssignmentStatus.ACCEPTED in AssignmentStatus.ACTIVE
        assert AssignmentStatus.IN_PROGRESS in AssignmentStatus.ACTIVE
        assert AssignmentStatus.OVERDUE in AssignmentStatus.ACTIVE
        assert AssignmentStatus.DRAFT not in AssignmentStatus.ACTIVE

    def test_draft_can_go_to_assigned(self):
        assert AssignmentStatus.ASSIGNED in AssignmentStatus.ALLOWED_TRANSITIONS[AssignmentStatus.DRAFT]

    def test_draft_can_be_cancelled(self):
        assert AssignmentStatus.CANCELLED in AssignmentStatus.ALLOWED_TRANSITIONS[AssignmentStatus.DRAFT]

    def test_draft_cannot_complete_directly(self):
        assert AssignmentStatus.COMPLETED not in AssignmentStatus.ALLOWED_TRANSITIONS[AssignmentStatus.DRAFT]

    def test_assigned_can_accept(self):
        assert AssignmentStatus.ACCEPTED in AssignmentStatus.ALLOWED_TRANSITIONS[AssignmentStatus.ASSIGNED]

    def test_report_submitted_can_complete(self):
        assert AssignmentStatus.COMPLETED in AssignmentStatus.ALLOWED_TRANSITIONS[AssignmentStatus.REPORT_SUBMITTED]

    def test_report_submitted_can_return(self):
        assert AssignmentStatus.RETURNED_FOR_REVISION in AssignmentStatus.ALLOWED_TRANSITIONS[AssignmentStatus.REPORT_SUBMITTED]

    def test_completed_can_archive(self):
        assert AssignmentStatus.ARCHIVED in AssignmentStatus.ALLOWED_TRANSITIONS[AssignmentStatus.COMPLETED]

    def test_archived_has_no_transitions(self):
        assert len(AssignmentStatus.ALLOWED_TRANSITIONS[AssignmentStatus.ARCHIVED]) == 0

    def test_escalated_can_complete(self):
        assert AssignmentStatus.COMPLETED in AssignmentStatus.ALLOWED_TRANSITIONS[AssignmentStatus.ESCALATED]

    def test_overdue_can_escalate(self):
        assert AssignmentStatus.ESCALATED in AssignmentStatus.ALLOWED_TRANSITIONS[AssignmentStatus.OVERDUE]

    def test_overdue_can_submit_report(self):
        assert AssignmentStatus.REPORT_SUBMITTED in AssignmentStatus.ALLOWED_TRANSITIONS[AssignmentStatus.OVERDUE]

    def test_all_statuses_have_transition_entry(self):
        for status in AssignmentStatus.ALL:
            assert status in AssignmentStatus.ALLOWED_TRANSITIONS, f"{status} missing from ALLOWED_TRANSITIONS"

    def test_complete_to_archived_only(self):
        transitions = AssignmentStatus.ALLOWED_TRANSITIONS[AssignmentStatus.COMPLETED]
        assert transitions == frozenset({AssignmentStatus.ARCHIVED})

    def test_returned_can_go_in_progress(self):
        assert AssignmentStatus.IN_PROGRESS in AssignmentStatus.ALLOWED_TRANSITIONS[AssignmentStatus.RETURNED_FOR_REVISION]

    def test_returned_can_resubmit_report(self):
        assert AssignmentStatus.REPORT_SUBMITTED in AssignmentStatus.ALLOWED_TRANSITIONS[AssignmentStatus.RETURNED_FOR_REVISION]


# ===========================================================================
# 3. Service — tenant validation fail-closed
# ===========================================================================

class TestServiceTenantValidation:
    def test_list_assignments_none_tenant(self):
        from app.modules.rector_assignment_workflow.service import list_assignments
        db = MagicMock(spec=Session)
        with pytest.raises((DomainValidationError, TenantRequiredError, ValueError)):
            list_assignments(None, db)

    def test_list_assignments_zero_tenant(self):
        from app.modules.rector_assignment_workflow.service import list_assignments
        db = MagicMock(spec=Session)
        with pytest.raises((DomainValidationError, TenantRequiredError, ValueError)):
            list_assignments(0, db)

    def test_get_assignment_detail_none_tenant(self):
        from app.modules.rector_assignment_workflow.service import get_assignment_detail
        db = MagicMock(spec=Session)
        with pytest.raises((DomainValidationError, TenantRequiredError, ValueError)):
            get_assignment_detail(None, 1, db)

    def test_get_dashboard_summary_none_tenant(self):
        from app.modules.rector_assignment_workflow.service import get_dashboard_summary
        db = MagicMock(spec=Session)
        with pytest.raises((DomainValidationError, TenantRequiredError, ValueError)):
            get_dashboard_summary(None, db)


# ===========================================================================
# 4. Service — transition guard
# ===========================================================================

class TestTransitionGuard:
    def _build_assignment(self, status: str) -> MagicMock:
        a = MagicMock(spec=RectorAssignment)
        a.id = 1
        a.tenant_id = 1
        a.status = status
        a.version = 1
        a.is_archived = False
        return a

    def test_invalid_transition_raises_domain_error(self):
        from app.modules.rector_assignment_workflow.service import _assert_transition_allowed
        with pytest.raises(DomainValidationError):
            _assert_transition_allowed(AssignmentStatus.DRAFT, AssignmentStatus.COMPLETED)

    def test_valid_transition_no_error(self):
        from app.modules.rector_assignment_workflow.service import _assert_transition_allowed
        _assert_transition_allowed(AssignmentStatus.DRAFT, AssignmentStatus.ASSIGNED)

    def test_archived_transition_to_any_raises(self):
        from app.modules.rector_assignment_workflow.service import _assert_transition_allowed
        for s in [AssignmentStatus.DRAFT, AssignmentStatus.COMPLETED, AssignmentStatus.CANCELLED]:
            with pytest.raises(DomainValidationError):
                _assert_transition_allowed(AssignmentStatus.ARCHIVED, s)

    def test_cancel_requires_reason(self):
        from app.modules.rector_assignment_workflow.service import cancel_assignment
        db = MagicMock(spec=Session)
        with pytest.raises((DomainValidationError, ValueError)):
            cancel_assignment(1, 1, 1, None, "", db)

    def test_return_requires_reason(self):
        from app.modules.rector_assignment_workflow.service import return_assignment_for_revision
        db = MagicMock(spec=Session)
        with pytest.raises((DomainValidationError, ValueError)):
            return_assignment_for_revision(1, 1, 1, None, "   ", db)


# ===========================================================================
# 5. AssignmentPriority constants
# ===========================================================================

class TestPriorityConstants:
    def test_all_priorities_present(self):
        for p in ("LOW", "NORMAL", "HIGH", "CRITICAL"):
            assert p in AssignmentPriority.ALL

    def test_frozenset(self):
        assert isinstance(AssignmentPriority.ALL, frozenset)


# ===========================================================================
# 6. Model tablenames
# ===========================================================================

class TestModelTablenames:
    def test_assignment_tablename(self):
        assert RectorAssignment.__tablename__ == "rector_assignments"

    def test_assignee_tablename(self):
        from app.modules.rector_assignment_workflow.models import RectorAssignmentAssignee
        assert RectorAssignmentAssignee.__tablename__ == "rector_assignment_assignees"

    def test_task_tablename(self):
        from app.modules.rector_assignment_workflow.models import RectorAssignmentTask
        assert RectorAssignmentTask.__tablename__ == "rector_assignment_tasks"

    def test_report_tablename(self):
        assert RectorAssignmentReport.__tablename__ == "rector_assignment_reports"

    def test_evidence_tablename(self):
        assert RectorAssignmentEvidence.__tablename__ == "rector_assignment_evidence"

    def test_comment_tablename(self):
        assert RectorAssignmentComment.__tablename__ == "rector_assignment_comments"

    def test_status_history_tablename(self):
        assert RectorAssignmentStatusHistory.__tablename__ == "rector_assignment_status_history"

    def test_escalation_tablename(self):
        assert RectorAssignmentEscalation.__tablename__ == "rector_assignment_escalations"

    def test_template_tablename(self):
        assert RectorAssignmentTemplate.__tablename__ == "rector_assignment_templates"

    def test_audit_event_tablename(self):
        assert RectorAssignmentAuditEvent.__tablename__ == "rector_assignment_audit_events"


# ===========================================================================
# 7. Schema validation
# ===========================================================================

class TestSchemaValidation:
    def test_create_request_requires_title(self):
        from app.modules.rector_assignment_workflow.schemas import AssignmentCreateRequest
        with pytest.raises(Exception):
            AssignmentCreateRequest(title="")

    def test_create_request_valid(self):
        from app.modules.rector_assignment_workflow.schemas import AssignmentCreateRequest
        r = AssignmentCreateRequest(title="Test assignment")
        assert r.title == "Test assignment"
        assert r.priority == "NORMAL"
        assert r.recurrence_type == "NONE"
        assert r.assignees == []
        assert r.tasks == []

    def test_create_request_invalid_priority(self):
        from app.modules.rector_assignment_workflow.schemas import AssignmentCreateRequest
        with pytest.raises(Exception):
            AssignmentCreateRequest(title="T", priority="ULTRA")

    def test_create_request_invalid_recurrence(self):
        from app.modules.rector_assignment_workflow.schemas import AssignmentCreateRequest
        with pytest.raises(Exception):
            AssignmentCreateRequest(title="T", recurrence_type="FORTNIGHTLY")

    def test_evidence_create_bad_url(self):
        from app.modules.rector_assignment_workflow.schemas import EvidenceCreateRequest
        with pytest.raises(Exception):
            EvidenceCreateRequest(evidence_type="LINK", title="Test", url="http://not-secure.com")

    def test_evidence_create_https_ok(self):
        from app.modules.rector_assignment_workflow.schemas import EvidenceCreateRequest
        r = EvidenceCreateRequest(evidence_type="LINK", title="Test", url="https://example.com/file")
        assert r.url == "https://example.com/file"

    def test_report_period_end_before_start_rejected(self):
        from app.modules.rector_assignment_workflow.schemas import AssignmentReportCreateRequest
        from datetime import date
        with pytest.raises(Exception):
            AssignmentReportCreateRequest(
                reporting_period_start=date(2024, 5, 1),
                reporting_period_end=date(2024, 4, 1),
                progress_percent=50,
                summary="test",
            )

    def test_report_review_invalid_action(self):
        from app.modules.rector_assignment_workflow.schemas import ReportReviewRequest
        with pytest.raises(Exception):
            ReportReviewRequest(action="approve_and_close")

    def test_escalation_level_max(self):
        from app.modules.rector_assignment_workflow.schemas import EscalationRequest
        with pytest.raises(Exception):
            EscalationRequest(reason="test", escalation_level=5, escalated_to_role="dean")

    def test_dashboard_response_fake_metrics_false(self):
        from app.modules.rector_assignment_workflow.schemas import DashboardSummaryResponse
        from datetime import datetime
        r = DashboardSummaryResponse(
            tenant_id=1,
            computed_at=datetime.now(),
            total_assignments=0,
            active_count=0,
            draft_count=0,
            overdue_count=0,
            escalated_count=0,
            completed_count=0,
            cancelled_count=0,
            report_submitted_count=0,
            returned_count=0,
            due_this_week=0,
            due_today=0,
            completion_rate_30d=0.0,
            average_days_to_complete=None,
            by_status={},
            by_priority={},
            by_unit=[],
            top_overdue=[],
        )
        assert r.fake_metrics is False
        assert r.data_source == "computed_from_assignments"


# ===========================================================================
# 8. Enum constants
# ===========================================================================

class TestEnumConstants:
    def test_audit_event_types_exist(self):
        assert AuditEventType.ASSIGNMENT_CREATED == "ASSIGNMENT_CREATED"
        assert AuditEventType.ASSIGNMENT_ASSIGNED == "ASSIGNMENT_ASSIGNED"
        assert AuditEventType.ASSIGNMENT_COMPLETED == "ASSIGNMENT_COMPLETED"
        assert AuditEventType.REPORT_SUBMITTED == "REPORT_SUBMITTED"
        assert AuditEventType.EVIDENCE_ATTACHED == "EVIDENCE_ATTACHED"
        assert AuditEventType.ASSIGNMENT_CANCELLED == "ASSIGNMENT_CANCELLED"
        assert AuditEventType.ASSIGNMENT_ARCHIVED == "ASSIGNMENT_ARCHIVED"
        assert AuditEventType.ASSIGNMENT_ESCALATED == "ASSIGNMENT_ESCALATED"
        assert AuditEventType.RETURNED_FOR_REVISION == "RETURNED_FOR_REVISION"

    def test_comment_visibility_values(self):
        assert CommentVisibility.INTERNAL == "INTERNAL"
        assert CommentVisibility.ASSIGNEES == "ASSIGNEES"
        assert CommentVisibility.LEADERSHIP == "LEADERSHIP"

    def test_escalation_status_values(self):
        assert EscalationStatus.OPEN == "OPEN"
        assert EscalationStatus.RESOLVED == "RESOLVED"
        assert EscalationStatus.CANCELLED == "CANCELLED"

    def test_evidence_type_values(self):
        assert EvidenceType.FILE == "FILE"
        assert EvidenceType.LINK == "LINK"
        assert EvidenceType.TEXT == "TEXT"

    def test_report_status_values(self):
        assert ReportStatus.SUBMITTED == "SUBMITTED"
        assert ReportStatus.RETURNED == "RETURNED"
        assert ReportStatus.ACCEPTED == "ACCEPTED"
