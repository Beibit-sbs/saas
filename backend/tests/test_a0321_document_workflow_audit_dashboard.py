"""A-032.1 document workflow audit and dashboard tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.modules.document_workflow_os.schemas import DashboardSummaryResponse
from app.modules.document_workflow_os.service import get_document_workflow_dashboard_summary


def test_dashboard_summary_hardcodes_contract_flags():
    db = MagicMock(spec=Session)
    with (
        patch("app.modules.document_workflow_os.service.repo_compute_dashboard_summary") as mock_summary,
        patch("app.modules.document_workflow_os.service.repo_add_audit_event"),
        patch("app.modules.document_workflow_os.service.log_admin_action"),
    ):
        mock_summary.return_value = {
            "total_documents": 10,
            "registered_documents": 3,
            "under_review_count": 2,
            "returned_for_revision_count": 1,
            "approved_count": 1,
            "signed_count": 1,
            "archived_count": 1,
            "incoming_correspondence_count": 2,
            "outgoing_correspondence_count": 1,
            "overdue_document_reviews": 0,
            "documents_linked_to_assignments": 1,
            "decrees_pending_signature": 1,
            "average_review_cycle_days": None,
        }
        result = get_document_workflow_dashboard_summary(db, 1, 99)

    assert isinstance(result, DashboardSummaryResponse)
    assert result.fake_metrics is False
    assert result.data_source == "computed_from_documents"
    assert result.incomplete_data is False


def test_dashboard_summary_falls_back_without_fake_metrics():
    db = MagicMock(spec=Session)
    with (
        patch("app.modules.document_workflow_os.service.repo_compute_dashboard_summary", side_effect=RuntimeError("db down")),
        patch("app.modules.document_workflow_os.service.repo_add_audit_event"),
        patch("app.modules.document_workflow_os.service.log_admin_action"),
    ):
        result = get_document_workflow_dashboard_summary(db, 1, 99)

    assert result.fake_metrics is False
    assert result.data_source == "computed_from_documents"
    assert result.incomplete_data is True
    assert result.total_documents == 0


def test_dashboard_emits_audit_event():
    db = MagicMock(spec=Session)
    with (
        patch("app.modules.document_workflow_os.service.repo_compute_dashboard_summary") as mock_summary,
        patch("app.modules.document_workflow_os.service.repo_add_audit_event") as mock_audit,
        patch("app.modules.document_workflow_os.service.log_admin_action"),
    ):
        mock_summary.return_value = {
            "total_documents": 1,
            "registered_documents": 0,
            "under_review_count": 0,
            "returned_for_revision_count": 0,
            "approved_count": 0,
            "signed_count": 0,
            "archived_count": 0,
            "incoming_correspondence_count": 0,
            "outgoing_correspondence_count": 0,
            "overdue_document_reviews": 0,
            "documents_linked_to_assignments": 0,
            "decrees_pending_signature": 0,
            "average_review_cycle_days": None,
        }
        get_document_workflow_dashboard_summary(db, 1, 99)

    assert mock_audit.called
