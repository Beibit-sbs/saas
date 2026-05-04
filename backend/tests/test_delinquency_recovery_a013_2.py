from __future__ import annotations

from uuid import uuid4
from unittest.mock import MagicMock, patch

from app.modules.brain_core.action_bridge import _make_create_collections_case_handler
from app.modules.brain_core.service import BrainCoreService
from app.modules.delinquency_collections.schemas import DelinquencyRecordCreateSchema, DelinquencyRecordSchema


def _make_service() -> BrainCoreService:
    svc = BrainCoreService.__new__(BrainCoreService)
    svc._observability = MagicMock()
    svc._signals = []
    svc._decisions = []
    svc._explanations = {}
    svc._context_builder = MagicMock()
    svc._classifier = MagicMock()
    svc._knowledge = MagicMock()
    svc._policy_resolver = MagicMock()
    svc._reasoning = MagicMock()
    svc._planner = MagicMock()
    svc._policy_guard = MagicMock()
    svc._dispatcher = MagicMock()
    svc._explanation = MagicMock()
    svc._outcome_tracker = MagicMock()
    svc._quality_tracker = MagicMock()
    svc._policy_tuner = MagicMock()
    return svc


def test_create_collections_handler_ensures_existing_record_idempotently(monkeypatch) -> None:
    existing = DelinquencyRecordSchema(
        id=77,
        tenant_id="7",
        student_id="ST-777",
        invoice_code="INV-777",
        amount_due=250.0,
        days_overdue=12,
        escalation_stage="stage_1",
        status="open",
    )

    list_mock = MagicMock(return_value=[existing])
    create_mock = MagicMock()

    monkeypatch.setattr("app.modules.delinquency_collections.service.list_delinquency_records", list_mock)
    monkeypatch.setattr("app.modules.delinquency_collections.service.create_delinquency_record", create_mock)

    handler = _make_create_collections_case_handler()
    result = handler(
        tenant_id=7,
        decision_id="dec-777",
        payload={
            "student_id": "ST-777",
            "invoice_code": "INV-777",
            "balance_due": 250.0,
            "delinquency_days": 12,
        },
    )

    assert result["status"] == "ensured"
    assert result["idempotent_replay"] is True
    assert result["item"]["record_id"] == 77
    create_mock.assert_not_called()


def test_create_collections_handler_creates_record_via_delinquency_service(monkeypatch) -> None:
    created = DelinquencyRecordSchema(
        id=88,
        tenant_id="9",
        student_id="ST-900",
        invoice_code="INV-900",
        amount_due=190.5,
        days_overdue=46,
        escalation_stage="stage_1",
        status="open",
    )

    list_mock = MagicMock(return_value=[])
    create_mock = MagicMock(return_value=created)

    monkeypatch.setattr("app.modules.delinquency_collections.service.list_delinquency_records", list_mock)
    monkeypatch.setattr("app.modules.delinquency_collections.service.create_delinquency_record", create_mock)

    handler = _make_create_collections_case_handler()
    result = handler(
        tenant_id=9,
        decision_id="dec-900",
        payload={
            "student_id": "ST-900",
            "invoice_id": "INV-900",
            "amount_cents": 19050,
            "overdue_days": 46,
            "tenant_id": 999,
        },
    )

    assert result["status"] == "created"
    assert result["item"]["record_id"] == 88
    assert result["item"]["source"] == "delinquency_collections_module"

    create_mock.assert_called_once()
    args = create_mock.call_args.args
    assert args[0] == 9
    assert isinstance(args[1], DelinquencyRecordCreateSchema)
    assert args[1].student_id == "ST-900"
    assert args[1].invoice_code == "INV-900"
    assert args[1].amount_due == 190.5
    assert args[1].days_overdue == 46
    assert args[2] == "brain_core"


def test_create_collections_handler_fails_without_student_id(monkeypatch) -> None:
    monkeypatch.setattr("app.modules.delinquency_collections.service.list_delinquency_records", MagicMock(return_value=[]))
    monkeypatch.setattr("app.modules.delinquency_collections.service.create_delinquency_record", MagicMock())

    handler = _make_create_collections_case_handler()
    result = handler(
        tenant_id=5,
        decision_id="dec-5",
        payload={"invoice_id": "INV-5", "amount_cents": 5000, "overdue_days": 10},
    )

    assert result["status"] == "failed"
    assert "student_id" in result["reason"]


def test_process_signal_payment_overdue_dispatches_collections_case() -> None:
    from app.modules.brain_core.policy.tenant_policy import TenantPolicyProfile

    svc = _make_service()
    svc._context_builder.build_context.return_value = {}
    svc._classifier.classify.return_value = {
        "situation_type": "financial_risk",
        "severity": "high",
        "urgency": "high",
        "reasoning_path": "payment_overdue_high",
    }
    svc._knowledge.retrieve.return_value = {}
    svc._policy_resolver.get_profile.return_value = TenantPolicyProfile(
        tenant_id=11,
        autonomy_level=2,
        require_approval_for_critical=True,
        default_approval_role="finance_office",
        enable_ai_reasoning=False,
    )
    svc._reasoning.decide.return_value = {
        "decision_type": "risk",
        "priority": "high",
        "recommended_actions": ["create_collections_case"],
        "requires_approval": False,
        "confidence_score": 0.9,
        "severity_score": 0.9,
        "urgency_score": 0.9,
        "ai_reasoning_enabled": False,
        "ai_reasoning_trace": [],
    }
    svc._planner.build_plan.return_value = [
        {
            "name": "create_collections_case",
            "action_type": "workflow_task",
            "requires_approval": False,
            "payload": {
                "student_id": "ST-11",
                "invoice_id": "INV-11",
                "balance_due": 321.0,
                "delinquency_days": 60,
            },
        }
    ]
    svc._policy_guard.validate.return_value = MagicMock(
        approved=True,
        requires_approval=False,
        reason="policy_passed",
        approval_role=None,
    )
    svc._dispatcher.dispatch.return_value = [
        {"action": "create_collections_case", "status": "created", "item": {"record_id": 5001}}
    ]
    svc._explanation.build.return_value = {"summary": "collections case created"}

    signal = {
        "event_type": "finance.payment_overdue.detected",
        "tenant_id": 11,
        "source_entity_type": "billing_delinquency",
        "source_entity_id": "DLQ-11",
        "payload": {
            "student_id": "ST-11",
            "invoice_id": "INV-11",
            "delinquency_days": 60,
            "balance_due": 321.0,
        },
    }

    with (
        patch.object(svc, "_check_duplicate_signal", return_value=None),
        patch.object(svc, "_try_persist_signal_to_db"),
        patch.object(svc, "_try_persist_decision_to_db"),
        patch.object(svc, "_emit_decision_notification"),
    ):
        result = svc.process_signal(dict(signal))

    assert result["status"] == "processed"
    dispatched_actions = svc._dispatcher.dispatch.call_args.kwargs["actions"]
    assert any(item["name"] == "create_collections_case" for item in dispatched_actions)


def test_duplicate_payment_overdue_signal_is_deduplicated() -> None:
    svc = _make_service()
    signal = {
        "event_type": "finance.payment_overdue.detected",
        "tenant_id": 21,
        "source_entity_type": "billing_delinquency",
        "source_entity_id": "DLQ-21",
        "payload": {"student_id": "ST-21", "invoice_id": "INV-21"},
    }

    with patch.object(svc, "_check_duplicate_signal", return_value=uuid4()):
        result = svc.process_signal(dict(signal))

    assert result["status"] == "deduplicated"
    svc._dispatcher.dispatch.assert_not_called()


def test_payment_overdue_missing_tenant_fails_closed() -> None:
    svc = _make_service()
    result = svc.process_signal(
        {
            "event_type": "finance.payment_overdue.detected",
            "tenant_id": 0,
            "source_entity_type": "billing_delinquency",
            "source_entity_id": "DLQ-0",
            "payload": {"student_id": "ST-0", "invoice_id": "INV-0"},
        }
    )

    assert result["status"] == "rejected"
    assert result["reason"] == "missing_tenant_context"


def test_payment_overdue_cross_tenant_payload_cannot_override_dispatch_tenant() -> None:
    from app.modules.brain_core.policy.tenant_policy import TenantPolicyProfile

    svc = _make_service()
    svc._context_builder.build_context.return_value = {}
    svc._classifier.classify.return_value = {
        "situation_type": "financial_risk",
        "severity": "medium",
        "urgency": "medium",
        "reasoning_path": "payment_overdue_medium",
    }
    svc._knowledge.retrieve.return_value = {}
    svc._policy_resolver.get_profile.return_value = TenantPolicyProfile(
        tenant_id=22,
        autonomy_level=2,
        require_approval_for_critical=True,
        default_approval_role="finance_office",
        enable_ai_reasoning=False,
    )
    svc._reasoning.decide.return_value = {
        "decision_type": "risk",
        "priority": "high",
        "recommended_actions": ["create_collections_case"],
        "requires_approval": False,
        "confidence_score": 0.9,
        "severity_score": 0.7,
        "urgency_score": 0.7,
        "ai_reasoning_enabled": False,
        "ai_reasoning_trace": [],
    }
    svc._planner.build_plan.return_value = [
        {
            "name": "create_collections_case",
            "action_type": "workflow_task",
            "requires_approval": False,
            "payload": {
                "student_id": "ST-22",
                "invoice_id": "INV-22",
                "tenant_id": 999,
            },
        }
    ]
    svc._policy_guard.validate.return_value = MagicMock(
        approved=True,
        requires_approval=False,
        reason="policy_passed",
        approval_role=None,
    )
    svc._dispatcher.dispatch.return_value = [{"action": "create_collections_case", "status": "created"}]
    svc._explanation.build.return_value = {"summary": "ok"}

    signal = {
        "event_type": "finance.payment_overdue.detected",
        "tenant_id": 22,
        "source_entity_type": "billing_delinquency",
        "source_entity_id": "DLQ-22",
        "payload": {
            "student_id": "ST-22",
            "invoice_id": "INV-22",
            "tenant_id": 999,
        },
    }

    with (
        patch.object(svc, "_check_duplicate_signal", return_value=None),
        patch.object(svc, "_try_persist_signal_to_db"),
        patch.object(svc, "_try_persist_decision_to_db"),
        patch.object(svc, "_emit_decision_notification"),
    ):
        svc.process_signal(dict(signal))

    assert svc._dispatcher.dispatch.call_args.kwargs["tenant_id"] == 22
