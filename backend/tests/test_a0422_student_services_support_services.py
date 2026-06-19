from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

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
        "create_hardship_support_request_from_finance_handoff",
        "evaluate_hardship_readiness",
        "list_finance_hardship_reviewer_queue",
        "intake_finance_hardship_evidence_gap",
        "record_finance_hardship_human_review_outcome_note",
        "create_finance_hardship_finance_office_referral",
        "list_finance_hardship_finance_office_referral_queue",
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


def test_finance_handoff_creates_hardship_readiness_without_decision() -> None:
    db = _db()
    service_request = SimpleNamespace(id=11, tenant_id=1)
    hardship = SimpleNamespace(
        id=22,
        tenant_id=1,
        request_id=11,
        status="readiness_evaluated",
        readiness_status="ready_for_human_review",
        missing_evidence_json=[],
        recommended_next_step="queue_human_review",
    )
    request = service.schemas.FinanceHardshipHandoffCreateRequest(
        student_id="S-1001",
        receivables_metadata_id=7,
        evidence_refs=["student_statement", "balance_statement"],
    )
    with (
        patch("app.modules.student_services_support.service.repository.create_service_request", return_value=service_request) as create_request,
        patch("app.modules.student_services_support.service.repository.create_hardship_request", return_value=hardship) as create_hardship,
        patch("app.modules.student_services_support.service.repository.create_service_request_event"),
    ):
        result = service.create_hardship_support_request_from_finance_handoff(db, 1, "actor-1", request)
    assert result.item.request_id == 11
    assert result.item.readiness_status == "ready_for_human_review"
    request_kwargs = create_request.call_args.kwargs
    assert request_kwargs["request_type"] == "hardship"
    assert request_kwargs["metadata_json"]["receivables_metadata_id"] == 7
    hardship_kwargs = create_hardship.call_args.kwargs
    assert hardship_kwargs["autonomous_decision_enabled"] is False
    assert "no_billing_balance_mutation" in hardship_kwargs["limitations_json"]


def test_dashboard_summary_exposes_finance_hardship_handoff_visibility() -> None:
    db = _db()
    with (
        patch(
            "app.modules.student_services_support.service.repository.count_by_status",
            side_effect=[
                {"submitted": 2},
                {"escalated": 1},
                {"readiness_evaluated": 3},
                {"ready_for_human_review": 1},
                {"routed": 1},
            ],
        ),
        patch(
            "app.modules.student_services_support.service.repository.count_hardship_readiness_by_source_flow",
            return_value={"ready_for_human_review": 2, "blocked_missing_required_evidence": 1},
        ),
        patch("app.modules.student_services_support.service.repository.create_dashboard_snapshot") as create_snapshot,
    ):
        result = service.compute_student_support_dashboard_summary(db, 1, "actor-1")
    visibility = result.finance_hardship_handoff_visibility
    assert visibility.total == 3
    assert visibility.review_queue_count == 2
    assert visibility.missing_evidence_count == 1
    assert visibility.no_automatic_aid_decision is True
    assert visibility.no_billing_balance_mutation is True
    snapshot_summary = create_snapshot.call_args.kwargs["summary_json"]
    assert snapshot_summary["finance_hardship_handoff_visibility"]["source_flow"] == "student_finance_receivables_handoff"


def test_finance_hardship_reviewer_queue_exposes_evidence_gaps_without_decisions() -> None:
    db = _db()
    hardship = SimpleNamespace(
        id=22,
        request_id=11,
        status="readiness_evaluated",
        readiness_status="blocked_missing_required_evidence",
        missing_evidence_json=["balance_statement"],
        recommended_next_step="collect_missing_evidence",
        metadata_json={
            "source_module": "finance_procurement_asset",
            "source_flow": "student_finance_receivables_handoff",
            "receivables_metadata_id": 7,
        },
        created_at=None,
        updated_at=None,
    )
    service_request = SimpleNamespace(
        id=11,
        student_id="S-1001",
        support_priority="high",
        status="submitted",
    )
    with patch(
        "app.modules.student_services_support.service.repository.list_hardship_reviewer_queue_by_source_flow",
        return_value=[(hardship, service_request)],
    ) as list_queue:
        result = service.list_finance_hardship_reviewer_queue(db, 1, "actor-1")
    item = result.items[0]
    assert item.student_id == "S-1001"
    assert item.receivables_metadata_id == 7
    assert item.missing_evidence == ["balance_statement"]
    assert item.no_automatic_aid_decision is True
    assert item.no_billing_balance_mutation is True
    assert list_queue.call_args.args[2] == "student_finance_receivables_handoff"


def test_finance_hardship_evidence_gap_intake_updates_readiness_without_finance_action() -> None:
    db = _db()
    hardship = SimpleNamespace(
        id=22,
        tenant_id=1,
        request_id=11,
        status="readiness_evaluated",
        readiness_status="blocked_missing_required_evidence",
        missing_evidence_json=["balance_statement"],
        recommended_next_step="collect_missing_evidence",
        metadata_json={
            "source_module": "finance_procurement_asset",
            "source_flow": "student_finance_receivables_handoff",
            "receivables_metadata_id": 7,
        },
        created_at=None,
        updated_at=None,
    )
    updated = SimpleNamespace(
        **{
            **hardship.__dict__,
            "readiness_status": "ready_for_human_review",
            "missing_evidence_json": [],
            "recommended_next_step": "queue_human_review",
        }
    )
    request = service.schemas.FinanceHardshipEvidenceGapIntakeRequest(
        evidence_type="balance_statement",
        evidence_ref="doc-7",
        satisfies_gap="balance_statement",
        source_available=True,
    )
    with (
        patch("app.modules.student_services_support.service.repository.get_hardship_request", return_value=hardship),
        patch("app.modules.student_services_support.service.repository.update_hardship_request", return_value=updated) as update_hardship,
        patch("app.modules.student_services_support.service.repository.create_service_request_event") as create_event,
    ):
        result = service.intake_finance_hardship_evidence_gap(db, 1, "actor-1", 22, request)
    assert result.item.readiness_status == "ready_for_human_review"
    assert result.remaining_missing_evidence == []
    assert result.evidence_metadata["satisfies_gap"] == "balance_statement"
    assert result.no_automatic_aid_decision is True
    assert result.no_billing_balance_mutation is True
    update_kwargs = update_hardship.call_args.kwargs
    assert update_kwargs["missing_evidence_json"] == []
    assert update_kwargs["metadata_json"]["last_evidence_gap_intake"]["evidence_ref"] == "doc-7"
    assert create_event.call_args.kwargs["event_type"] == "hardship.finance_handoff_evidence_gap_intake"


def test_finance_hardship_human_review_outcome_note_is_non_executing() -> None:
    db = _db()
    hardship = SimpleNamespace(
        id=22,
        tenant_id=1,
        request_id=11,
        status="readiness_evaluated",
        readiness_status="ready_for_human_review",
        missing_evidence_json=[],
        recommended_next_step="queue_human_review",
        metadata_json={
            "source_module": "finance_procurement_asset",
            "source_flow": "student_finance_receivables_handoff",
            "receivables_metadata_id": 7,
        },
        created_at=None,
        updated_at=None,
    )
    updated = SimpleNamespace(
        **{
            **hardship.__dict__,
            "status": "human_review_outcome_recorded",
        }
    )
    request = service.schemas.FinanceHardshipHumanReviewOutcomeNoteRequest(
        outcome_label="support_plan_recommended",
        reviewer_recommendation="manual_finance_review",
        note="Human reviewer recommends manual finance review.",
    )
    with (
        patch("app.modules.student_services_support.service.repository.get_hardship_request", return_value=hardship),
        patch("app.modules.student_services_support.service.repository.update_hardship_request", return_value=updated) as update_hardship,
        patch("app.modules.student_services_support.service.repository.create_service_request_event") as create_event,
    ):
        result = service.record_finance_hardship_human_review_outcome_note(db, 1, "actor-1", 22, request)
    assert result.item.status == "human_review_outcome_recorded"
    assert result.outcome_label == "support_plan_recommended"
    assert result.no_automatic_aid_decision is True
    assert result.no_billing_balance_mutation is True
    update_kwargs = update_hardship.call_args.kwargs
    assert update_kwargs["metadata_json"]["last_human_review_outcome_note"]["reviewer_recommendation"] == "manual_finance_review"
    assert update_kwargs["metadata_json"]["last_human_review_outcome_note"]["no_automatic_aid_decision"] is True
    assert create_event.call_args.kwargs["event_type"] == "hardship.finance_handoff_human_review_outcome_note_recorded"


def test_finance_hardship_finance_office_referral_is_metadata_only() -> None:
    db = _db()
    hardship = SimpleNamespace(
        id=22,
        tenant_id=1,
        request_id=11,
        status="human_review_outcome_recorded",
        readiness_status="ready_for_human_review",
        missing_evidence_json=[],
        recommended_next_step="queue_human_review",
        metadata_json={
            "source_module": "finance_procurement_asset",
            "source_flow": "student_finance_receivables_handoff",
            "receivables_metadata_id": 7,
        },
        created_at=None,
        updated_at=None,
    )
    updated = SimpleNamespace(
        **{
            **hardship.__dict__,
            "status": "finance_office_referral_recorded",
        }
    )
    request = service.schemas.FinanceHardshipFinanceOfficeReferralRequest(
        referral_target="student_finance_office",
        referral_reason="manual hardship review follow-up",
        referral_priority="high",
        note="Finance office referral metadata only.",
    )
    with (
        patch("app.modules.student_services_support.service.repository.get_hardship_request", return_value=hardship),
        patch("app.modules.student_services_support.service.repository.update_hardship_request", return_value=updated) as update_hardship,
        patch("app.modules.student_services_support.service.repository.create_service_request_event") as create_event,
    ):
        result = service.create_finance_hardship_finance_office_referral(db, 1, "actor-1", 22, request)
    assert result.item.status == "finance_office_referral_recorded"
    assert result.referral_target == "student_finance_office"
    assert result.referral_priority == "high"
    assert result.no_automatic_aid_decision is True
    assert result.no_billing_balance_mutation is True
    assert result.no_payment_execution is True
    update_kwargs = update_hardship.call_args.kwargs
    referral = update_kwargs["metadata_json"]["last_finance_office_referral"]
    assert referral["target_module"] == "finance_procurement_asset"
    assert referral["no_payment_execution"] is True
    assert create_event.call_args.kwargs["event_type"] == "hardship.finance_office_referral_recorded"


# --- A-055.HSP-R1: hardship status-transition guard (adversarial-review remediation) ---

def _finance_hardship(status: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=22,
        tenant_id=1,
        request_id=11,
        status=status,
        readiness_status="ready_for_human_review",
        missing_evidence_json=[],
        recommended_next_step="queue_human_review",
        metadata_json={"source_flow": "student_finance_receivables_handoff", "receivables_metadata_id": 7},
        created_at=None,
        updated_at=None,
    )


def test_finance_office_referral_rejected_when_human_review_skipped() -> None:
    # Out-of-order: referral directly on a readiness_evaluated hardship must be rejected (human-review gate).
    db = _db()
    request = service.schemas.FinanceHardshipFinanceOfficeReferralRequest(
        referral_target="student_finance_office", referral_reason="r", referral_priority="high", note="n"
    )
    with patch(
        "app.modules.student_services_support.service.repository.get_hardship_request",
        return_value=_finance_hardship("readiness_evaluated"),
    ), patch("app.modules.student_services_support.service.repository.update_hardship_request") as upd:
        with pytest.raises(service.DomainValidationError) as exc:
            service.create_finance_hardship_finance_office_referral(db, 1, "actor-1", 22, request)
    assert "invalid_hardship_status_transition" in str(exc.value)
    upd.assert_not_called()  # nothing persisted on a rejected transition


def test_human_review_outcome_note_rejected_on_terminal_hardship() -> None:
    # Re-mutating a terminal (finance_office_referral_recorded) hardship must be rejected.
    db = _db()
    request = service.schemas.FinanceHardshipHumanReviewOutcomeNoteRequest(
        outcome_label="manual_review_recorded", reviewer_recommendation="manual_finance_review", note="n"
    )
    with patch(
        "app.modules.student_services_support.service.repository.get_hardship_request",
        return_value=_finance_hardship("finance_office_referral_recorded"),
    ), patch("app.modules.student_services_support.service.repository.update_hardship_request") as upd:
        with pytest.raises(service.DomainValidationError):
            service.record_finance_hardship_human_review_outcome_note(db, 1, "actor-1", 22, request)
    upd.assert_not_called()


def test_evidence_gap_intake_rejected_after_referral() -> None:
    # Evidence-gap intake must be forbidden once the hardship is terminal (referral recorded).
    db = _db()
    request = service.schemas.FinanceHardshipEvidenceGapIntakeRequest(
        satisfies_gap="balance_statement", evidence_type="document_metadata", evidence_ref="ref", source_available=False
    )
    with patch(
        "app.modules.student_services_support.service.repository.get_hardship_request",
        return_value=_finance_hardship("finance_office_referral_recorded"),
    ), patch("app.modules.student_services_support.service.repository.update_hardship_request") as upd:
        with pytest.raises(service.DomainValidationError):
            service.intake_finance_hardship_evidence_gap(db, 1, "actor-1", 22, request)
    upd.assert_not_called()


def test_finance_hardship_finance_office_referral_queue_is_visibility_only() -> None:
    db = _db()
    hardship = SimpleNamespace(
        id=22,
        request_id=11,
        status="finance_office_referral_recorded",
        readiness_status="ready_for_human_review",
        missing_evidence_json=[],
        recommended_next_step="queue_human_review",
        metadata_json={
            "source_module": "finance_procurement_asset",
            "source_flow": "student_finance_receivables_handoff",
            "receivables_metadata_id": 7,
            "last_finance_office_referral": {
                "referral_target": "student_finance_office",
                "referral_reason": "manual hardship review follow-up",
                "referral_priority": "high",
                "note": "Finance office referral metadata only.",
                "referred_by_user_id": "actor-1",
                "source_module": "student_services_support",
                "target_module": "finance_procurement_asset",
                "no_payment_execution": True,
            },
        },
        created_at=None,
        updated_at=None,
    )
    service_request = SimpleNamespace(
        id=11,
        student_id="S-1001",
        support_priority="high",
        status="submitted",
    )
    with patch(
        "app.modules.student_services_support.service.repository.list_hardship_reviewer_queue_by_source_flow",
        return_value=[(hardship, service_request)],
    ) as list_queue:
        result = service.list_finance_hardship_finance_office_referral_queue(db, 1, "actor-1")
    item = result.items[0]
    assert item.student_id == "S-1001"
    assert item.referral_target == "student_finance_office"
    assert item.referral_priority == "high"
    assert item.referral_reason == "manual hardship review follow-up"
    assert item.no_automatic_aid_decision is True
    assert item.no_billing_balance_mutation is True
    assert item.no_payment_execution is True
    assert list_queue.call_args.args[2] == "student_finance_receivables_handoff"


def test_finance_hardship_human_review_note_fails_closed_for_other_tenant_hardship() -> None:
    # A-056.G1.3 tenant fail-closed: repository.get_hardship_request is tenant-scoped, so a
    # hardship_id that does not belong to the caller's tenant returns None and the write is
    # rejected ("not found in tenant scope") before any mutation — no cross-tenant write.
    db = _db()
    request = service.schemas.FinanceHardshipHumanReviewOutcomeNoteRequest(
        outcome_label="reviewed_supportive",
        note="human reviewer note",
    )
    with (
        patch(
            "app.modules.student_services_support.service.repository.get_hardship_request",
            return_value=None,
        ) as get_hs,
        patch(
            "app.modules.student_services_support.service.repository.update_hardship_request",
        ) as update_hs,
    ):
        with pytest.raises(service.DomainValidationError, match="not found in tenant scope"):
            service.record_finance_hardship_human_review_outcome_note(
                db, 1, "officer@example.com", 4242, request
            )
    get_hs.assert_called_once()
    update_hs.assert_not_called()
