from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.modules.student_services_support import permissions, service


def _db() -> MagicMock:
    db = MagicMock(spec=Session)
    db.commit.return_value = None
    db.rollback.return_value = None
    return db


def test_required_methods_exist() -> None:
    required = [
        "create_service_request",
        "assign_service_request",
        "update_service_request_status",
        "create_support_case",
        "add_support_case_note",
        "attach_support_evidence_metadata",
        "create_hardship_support_request",
        "evaluate_hardship_readiness",
        "create_disability_accommodation_request",
        "evaluate_accommodation_readiness",
        "create_student_complaint",
        "route_student_complaint",
        "escalate_support_case",
        "compute_student_support_dashboard_summary",
    ]
    for name in required:
        assert hasattr(service, name)


@pytest.mark.parametrize("value", sorted(permissions.ALL_PERMISSIONS))
def test_permissions_namespace_is_admin_student_services(value: str) -> None:
    assert value.startswith("admin.student_services.")


def test_readiness_evaluation_blocks_without_evidence() -> None:
    db = _db()
    payload = service.evaluate_hardship_readiness(db, 1, [])
    assert payload["readiness_status"] == "blocked_missing_required_evidence"
    assert payload["human_review_required"] is True


def test_readiness_evaluation_ready_with_minimum_evidence() -> None:
    db = _db()
    payload = service.evaluate_accommodation_readiness(db, 1, ["doc-a", "doc-b"])
    assert payload["readiness_status"] == "ready_for_human_review"
    assert payload["missing_evidence"] == []
