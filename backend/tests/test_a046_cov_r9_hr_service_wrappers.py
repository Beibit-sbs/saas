from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.modules.hr_staff_governance import service


class DummyRequest:
    def __init__(self, **values):
        self.__dict__.update(values)

    def model_dump(self, exclude_none: bool = True):
        data = dict(self.__dict__)
        if exclude_none:
            data = {k: v for k, v in data.items() if v is not None}
        return data


@pytest.fixture
def db() -> MagicMock:
    mock = MagicMock()
    mock.commit.return_value = None
    mock.rollback.return_value = None
    mock.refresh.return_value = None
    return mock


@pytest.fixture
def request_obj() -> DummyRequest:
    return DummyRequest(
        status=None,
        notes="note",
        metadata={"k": "v"},
        limitations=["custom_limit"],
        reviewer_id="reviewer-1",
        decision="approve",
        onboarding_ref="onboarding-1",
        appraisal_ref="appraisal-1",
        case_ref="case-1",
        offboarding_ref="offboarding-1",
        provider_name="provider-x",
        recruitment_ref="recruitment-1",
        source_reference="source://r9",
    )


def _entity(status: str = "DRAFT") -> SimpleNamespace:
    return SimpleNamespace(id=1, status=status, recruitment_ref="recruitment-1", source_reference="source://r9", evidence_status="PENDING", staff_ref="staff-1")


def _patch_commit_and_audit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(service, "_commit", lambda _db: None)
    monkeypatch.setattr(service, "_audit", lambda *_args, **_kwargs: None)


def test_merge_limitations_and_payload_helpers() -> None:
    merged = service._merge_limitations(["custom_limit"])
    assert "custom_limit" in merged
    assert "metadata_only_foundation" in merged

    create_payload = service._base_create_payload(DummyRequest(metadata={"x": 1}, limitations=["l1"]), "actor-1")
    assert create_payload["human_review_required"] is True
    assert create_payload["fake_data"] is False
    assert create_payload["provider_connected"] is False

    update_payload = service._base_update_payload(DummyRequest(metadata={"x": 2}, limitations=["l2"]), "actor-2")
    assert update_payload["human_review_required"] is True
    assert "limitations_json" in update_payload


@pytest.mark.parametrize(
    ("fn_name", "repo_calls"),
    [
        ("create_staff_profile", ["repo_create_staff_profile", "repo_record_staff_status_history"]),
        ("update_staff_profile", ["repo_get_staff_profile", "repo_update_staff_profile"]),
        ("create_employee_record", ["repo_create_employee_record"]),
        ("update_employee_record", ["repo_update_employee_record"]),
        ("create_recruitment_request", ["repo_create_recruitment_request"]),
        ("review_recruitment_request", ["repo_update_recruitment_request", "repo_create_hiring_committee_review"]),
        ("create_onboarding_case", ["repo_create_onboarding_case"]),
        ("update_onboarding_case", ["repo_update_onboarding_case"]),
        ("review_probation", ["repo_record_probation_review"]),
        ("create_leave_request", ["repo_create_leave_request"]),
        ("review_leave_request", ["repo_record_leave_review"]),
        ("create_appraisal_cycle", ["repo_create_appraisal_cycle"]),
        ("record_appraisal_review", ["repo_record_appraisal_review"]),
        ("create_training_certification", ["repo_create_training_certification"]),
        ("update_training_certification", ["repo_update_training_certification"]),
        ("create_staff_request", ["repo_create_staff_request"]),
        ("review_staff_request", ["repo_record_staff_request_review"]),
        ("create_staff_appeal", ["repo_create_staff_appeal"]),
        ("review_staff_appeal", ["repo_record_staff_appeal_review"]),
        ("create_policy_exception", ["repo_create_policy_exception"]),
        ("review_policy_exception", ["repo_record_policy_exception_review"]),
        ("create_disciplinary_case", ["repo_create_disciplinary_case"]),
        ("record_disciplinary_review", ["repo_add_disciplinary_evidence", "repo_record_disciplinary_review"]),
        ("create_offboarding_case", ["repo_create_offboarding_case"]),
        ("update_offboarding_case", ["repo_update_offboarding_case"]),
        ("record_access_lifecycle_review", ["repo_record_access_lifecycle_review"]),
        ("create_workload_bridge_record", ["repo_create_workload_bridge_record"]),
        ("create_payroll_readiness_profile", ["repo_create_payroll_readiness_profile"]),
        ("record_provider_readiness_evidence", ["repo_record_provider_readiness_evidence"]),
        ("create_hiring_evidence_pack", ["repo_create_hiring_evidence_pack"]),
        ("create_disciplinary_evidence", ["repo_add_disciplinary_evidence"]),
    ],
)
def test_hr_service_wrapper_calls(monkeypatch: pytest.MonkeyPatch, db: MagicMock, request_obj: DummyRequest, fn_name: str, repo_calls: list[str]):
    _patch_commit_and_audit(monkeypatch)
    for name in repo_calls:
        monkeypatch.setattr(service.repository, name, lambda *_args, **_kwargs: _entity())

    fn = getattr(service, fn_name)

    if fn_name == "update_staff_profile":
        result = fn(db, 1, "actor-1", 1, request_obj)
    elif fn_name in {"update_employee_record", "update_onboarding_case", "review_leave_request", "review_staff_request", "review_staff_appeal", "review_policy_exception", "record_disciplinary_review", "update_offboarding_case", "update_training_certification", "review_recruitment_request"}:
        result = fn(db, 1, "actor-1", 1, request_obj)
    else:
        result = fn(db, 1, "actor-1", request_obj)

    assert result is not None


def test_get_staff_profile_not_found_raises(monkeypatch: pytest.MonkeyPatch, db: MagicMock):
    monkeypatch.setattr(service.repository, "repo_get_staff_profile", lambda *_args, **_kwargs: None)
    with pytest.raises(Exception):
        service.get_staff_profile(db, 1, 999)


def test_summaries_and_health_helpers(monkeypatch: pytest.MonkeyPatch, db: MagicMock):
    monkeypatch.setattr(service.repository, "repo_compute_dashboard_summary", lambda *_args, **_kwargs: {"a": {"x": 1}, "b": {"y": 2}})
    monkeypatch.setattr(service.repository, "repo_list_evidence_items", lambda *_args, **_kwargs: [SimpleNamespace(limitations=["L1"], source_entity_type="t", source_entity_id=1, metadata_json={"k": "v"})])
    monkeypatch.setattr(service, "list_workload_bridge_records", lambda *_args, **_kwargs: [SimpleNamespace(bridge_target="finance"), SimpleNamespace(bridge_target="finance")])

    limitations = service.list_limitations(db, 1)
    health = service.get_health_summary(db, 1)
    bridge = service.get_bridge_summary(db, 1, "finance")
    brain = service.get_brain_signals_summary(db, 1)
    readiness = service.get_readiness_summary(db, 1)

    assert any(item["code"] == "L1" for item in limitations)
    assert health["total_records"] == 3
    assert bridge["records"] == 2
    assert brain["safe_draft_only"] is True
    assert len(readiness["providers"]) == 5
