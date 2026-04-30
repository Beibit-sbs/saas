"""W49 domain depth tests — scholarship application cap + revocation alert."""
from unittest.mock import patch

import pytest

from app.modules.scholarship.service import (
    _ACTIVE_APPLICATION_STATUSES,
    _AWARD_REVOCATION_RISK_STATUSES,
    _SCHOLARSHIP_APPLICATION_STATUS_MAX_ACTIVE,
    _ensure_revocation_alert_record,
    create_scholarship_application,
)


def test_scholarship_application_status_cap_dict_structure():
    assert "pending" in _SCHOLARSHIP_APPLICATION_STATUS_MAX_ACTIVE
    assert "under_review" in _SCHOLARSHIP_APPLICATION_STATUS_MAX_ACTIVE
    assert "approved" in _SCHOLARSHIP_APPLICATION_STATUS_MAX_ACTIVE
    assert _SCHOLARSHIP_APPLICATION_STATUS_MAX_ACTIVE["pending"] >= 100
    assert all(isinstance(v, int) for v in _SCHOLARSHIP_APPLICATION_STATUS_MAX_ACTIVE.values())


def test_active_application_statuses_and_award_revocation_risk_statuses():
    assert "pending" in _ACTIVE_APPLICATION_STATUSES
    assert "under_review" in _ACTIVE_APPLICATION_STATUSES
    assert "approved" in _ACTIVE_APPLICATION_STATUSES
    assert "revoked" in _AWARD_REVOCATION_RISK_STATUSES
    assert _ACTIVE_APPLICATION_STATUSES.isdisjoint(_AWARD_REVOCATION_RISK_STATUSES)


def test_create_scholarship_application_raises_when_cap_reached():
    tid = 7
    cap = _SCHOLARSHIP_APPLICATION_STATUS_MAX_ACTIVE.get("under_review", 200)
    fake_existing = [{"status": "under_review"} for _ in range(cap)]

    def fake_list(entity_type, tenant_id):
        if entity_type == "scholarship_applications":
            return fake_existing
        return []

    with patch("app.modules.scholarship.service.list_entities_for_tenant", side_effect=fake_list):
        with patch("app.modules.scholarship.service._check_student_is_enrolled_for_scholarship", return_value=None):
            with pytest.raises(ValueError, match="cap reached"):
                create_scholarship_application(
                    {
                        "application_code": "APP001",
                        "student_id": "STU001",
                        "scholarship_type": "merit",
                        "status": "under_review",
                        "gpa": 3.5,
                        "requested_amount": 5000.0,
                    },
                    tid,
                )


def test_ensure_revocation_alert_record_is_idempotent():
    tid = 20
    award_id = 55
    existing_alert = {
        "integration_source": "scholarship_revocation_queue",
        "source_entity_id": str(award_id),
        "alert_status": "open",
    }
    created: list[dict] = []

    def fake_list(entity_type, tenant_id):
        if entity_type == "scholarship_revocation_alerts":
            return [existing_alert]
        return []

    def fake_create(entity_type, payload, tenant_id):
        created.append(payload)
        return payload

    with patch("app.modules.scholarship.service.list_entities_for_tenant", side_effect=fake_list):
        with patch("app.modules.scholarship.service.create_entity_for_tenant", side_effect=fake_create):
            _ensure_revocation_alert_record(award_id, tid)

    assert len(created) == 0
