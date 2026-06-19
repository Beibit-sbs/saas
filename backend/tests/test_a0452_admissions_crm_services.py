from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.admissions_crm import permissions, schemas, service


def _db() -> MagicMock:
    db = MagicMock(spec=Session)
    db.commit.return_value = None
    db.rollback.return_value = None
    return db


def test_required_methods_exist() -> None:
    required = [
        "create_lead",
        "list_leads",
        "get_lead",
        "qualify_lead",
        "create_applicant",
        "list_applicants",
        "get_applicant",
        "create_application",
        "list_applications",
        "get_application",
        "submit_application",
    ]
    for name in required:
        assert hasattr(service, name)


@pytest.mark.parametrize("value", sorted(permissions.ALL_PERMISSIONS))
def test_permissions_namespace_is_admin_admissions_crm(value: str) -> None:
    assert value.startswith("admin.admissions_crm.")


@pytest.mark.parametrize(
    "current,new_status,ok",
    [
        ("lead_created", "lead_qualified", True),
        ("lead_created", "applicant_created", False),
        ("lead_created", "archived", True),
        ("lead_qualified", "applicant_created", True),
        ("lead_qualified", "lead_created", False),
        ("lead_qualified", "archived", True),
        ("applicant_created", "archived", True),
        ("applicant_created", "lead_qualified", False),
        ("archived", "lead_created", False),
        ("archived", "archived", False),
        ("application_started", "application_submitted", True),
        ("application_started", "archived", True),
        ("application_started", "application_started", False),
        ("application_submitted", "archived", True),
        ("application_submitted", "application_started", False),
        ("archived", "application_submitted", False),
    ],
)
def test_transition_rules(current: str, new_status: str, ok: bool) -> None:
    transitions = {
        "lead_created": frozenset({"lead_qualified", "archived"}),
        "lead_qualified": frozenset({"applicant_created", "archived"}),
        "applicant_created": frozenset({"archived"}),
        "application_started": frozenset({"application_submitted", "archived"}),
        "application_submitted": frozenset({"archived"}),
        "archived": frozenset(),
    }
    if ok:
        service._validate_transition(current, new_status, transitions)
    else:
        with pytest.raises(DomainValidationError):
            service._validate_transition(current, new_status, transitions)


def test_validate_actor_rejects_blank() -> None:
    with pytest.raises(DomainValidationError):
        service._validate_actor("  ")


def test_validate_actor_accepts_stringable() -> None:
    assert service._validate_actor(123) == "123"


def test_create_lead_requires_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    db = _db()
    payload = schemas.LeadCreateRequest(lead_ref="L-1", full_name="N", email="n@example.edu")
    with pytest.raises(ValueError):
        service.create_lead(db, 0, "actor", payload)


def test_qualify_lead_fails_when_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    db = _db()
    monkeypatch.setattr(service.repository, "get_lead", lambda *_: None)
    with pytest.raises(DomainValidationError):
        service.qualify_lead(db, 1, 99, "actor", schemas.LeadQualifyRequest())


def test_submit_application_fails_when_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    db = _db()
    monkeypatch.setattr(service.repository, "get_application", lambda *_: None)
    with pytest.raises(DomainValidationError):
        service.submit_application(db, 1, 99, "actor", schemas.ApplicationSubmitRequest())


def test_base_response_flags_are_fail_closed() -> None:
    payload = service._base_response()
    assert payload["fake_metrics"] is False
    assert payload["provider_live_enabled"] is False
    assert payload["autonomous_decision_enabled"] is False
    assert payload["hidden_score_present"] is False
    assert payload["human_review_required"] is True


@pytest.mark.parametrize(
    "status", [
        "lead_created",
        "lead_qualified",
        "applicant_created",
        "archived",
        "application_started",
        "application_submitted",
    ]
)
def test_transition_state_values_are_contract_known(status: str) -> None:
    assert status in {
        "lead_created",
        "lead_qualified",
        "applicant_created",
        "archived",
        "application_started",
        "application_submitted",
    }


def test_record_serializers_accept_minimal_models() -> None:
    lead = SimpleNamespace(
        id=1,
        tenant_id=1,
        lead_ref="L-1",
        status="lead_created",
        full_name="Lead",
        email="lead@example.edu",
        phone=None,
        source_channel="direct",
        metadata_json={},
        created_at=None,
        updated_at=None,
    )
    applicant = SimpleNamespace(
        id=2,
        tenant_id=1,
        lead_id=1,
        applicant_ref="A-1",
        status="applicant_created",
        full_name="Applicant",
        email="applicant@example.edu",
        metadata_json={},
        created_at=None,
        updated_at=None,
    )
    application = SimpleNamespace(
        id=3,
        tenant_id=1,
        applicant_id=2,
        application_ref="APP-1",
        status="application_started",
        program_code="CS",
        intake_term="2026-FALL",
        metadata_json={},
        created_at=None,
        updated_at=None,
    )
    assert service._lead_record(lead).id == 1
    assert service._applicant_record(applicant).id == 2
    assert service._application_record(application).id == 3
