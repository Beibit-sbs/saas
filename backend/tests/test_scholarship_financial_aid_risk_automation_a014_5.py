from __future__ import annotations

from app.modules.brain_core.registry import SignalRegistry
from app.modules.brain_core.service import BrainCoreService


def test_scholarship_award_at_risk_event_registered_for_brain() -> None:
    assert SignalRegistry.is_supported("scholarship.award.at_risk_detected") is True


def test_scholarship_award_at_risk_creates_support_case_and_preserves_evidence() -> None:
    service = BrainCoreService()
    signal = {
        "signal_id": "sig-sch-1",
        "tenant_id": 915,
        "correlation_id": "corr-sch-1",
        "event_type": "scholarship.award.at_risk_detected",
        "subject": {"student_id": "STU-SCH-1"},
        "payload": {
            "student_id": "STU-SCH-1",
            "award_id": "AWD-15",
            "award_code": "AWD-15",
            "current_gpa": 2.0,
            "gpa_threshold": 2.5,
            "status": "active",
            "risk_level": "high",
            "reason": "gpa_below_threshold",
            "evidence": {
                "current_gpa": 2.0,
                "gpa_threshold": 2.5,
            },
            "source_entity_type": "scholarship_award",
            "source_entity_id": "AWD-15",
        },
        "metadata": {},
    }

    processed = service.process_signal(signal)

    assert processed["status"] == "processed"
    assert processed["decision"]["status"] == "approval_pending"
    assert processed["dispatch_results"] == []

    support_action = next(
        item for item in processed["action_plan"] if item["name"] == "create_student_support_case"
    )
    assert support_action["payload"]["student_id"] == "STU-SCH-1"
    assert support_action["payload"]["award_id"] == "AWD-15"
    assert support_action["payload"]["source_entity_type"] == "scholarship_award"
    assert support_action["payload"]["source_entity_id"] == "AWD-15"
    assert support_action["payload"]["event_type"] == "scholarship.award.at_risk_detected"

    approved = service.approve_decision(processed["decision"]["decision_id"], actor="aid-office@tenant")
    assert approved["status"] == "approved"
    assert approved["decision"]["status"] == "dispatched"
    assert any(item["action"] == "create_student_support_case" for item in approved["dispatch_results"])


def test_scholarship_award_at_risk_duplicate_signal_is_deduplicated() -> None:
    service = BrainCoreService()
    signal = {
        "tenant_id": 916,
        "event_type": "scholarship.award.at_risk_detected",
        "source_entity_type": "scholarship_award",
        "source_entity_id": "AWD-16",
        "payload": {
            "student_id": "STU-SCH-2",
            "award_id": "AWD-16",
            "current_gpa": 1.9,
            "gpa_threshold": 2.5,
            "source_entity_type": "scholarship_award",
            "source_entity_id": "AWD-16",
        },
    }

    first = service.process_signal(dict(signal))
    second = service.process_signal(dict(signal))

    assert first["status"] == "processed"
    assert first["decision"]["status"] == "approval_pending"
    assert second["status"] == "deduplicated"


def test_scholarship_award_at_risk_missing_student_is_fail_closed() -> None:
    service = BrainCoreService()

    result = service.process_signal(
        {
            "tenant_id": 917,
            "event_type": "scholarship.award.at_risk_detected",
            "payload": {
                "award_id": "AWD-17",
                "current_gpa": 1.8,
                "gpa_threshold": 2.5,
                "source_entity_type": "scholarship_award",
                "source_entity_id": "AWD-17",
            },
        }
    )

    assert result["status"] == "rejected"
    assert result["reason"] == "missing_student_context"


def test_scholarship_award_at_risk_is_tenant_isolated_for_dedup() -> None:
    service = BrainCoreService()
    base_signal = {
        "event_type": "scholarship.award.at_risk_detected",
        "source_entity_type": "scholarship_award",
        "source_entity_id": "AWD-18",
        "payload": {
            "student_id": "STU-SCH-3",
            "award_id": "AWD-18",
            "current_gpa": 2.1,
            "gpa_threshold": 2.5,
            "source_entity_type": "scholarship_award",
            "source_entity_id": "AWD-18",
        },
    }

    first = service.process_signal({**base_signal, "tenant_id": 918})
    second = service.process_signal({**base_signal, "tenant_id": 919})

    assert first["status"] == "processed"
    assert second["status"] == "processed"


def test_financial_aid_warning_duplicate_signal_preserves_evidence() -> None:
    service = BrainCoreService()
    signal = {
        "tenant_id": 920,
        "event_type": "financial_aid.warning.detected",
        "source_entity_type": "financial_aid_record",
        "source_entity_id": "FA-920",
        "payload": {
            "student_id": "STU-FA-1",
            "record_id": "FA-920",
            "application_id": "APP-920",
            "from_status": "pending",
            "to_status": "rejected",
            "risk_level": "high",
            "reason": "eligibility_rejected",
            "evidence": {"from_status": "pending", "to_status": "rejected"},
            "source_entity_type": "financial_aid_record",
            "source_entity_id": "FA-920",
        },
    }

    first = service.process_signal(dict(signal))
    second = service.process_signal(dict(signal))

    assert first["status"] == "processed"
    assert first["decision"]["status"] == "approval_pending"
    assert first["dispatch_results"] == []

    support_action = next(
        item for item in first["action_plan"] if item["name"] == "create_student_support_case"
    )
    assert support_action["payload"]["application_id"] == "APP-920"
    assert support_action["payload"]["source_entity_id"] == "FA-920"

    approved = service.approve_decision(first["decision"]["decision_id"], actor="aid-office@tenant")
    assert approved["status"] == "approved"
    assert any(item["action"] == "create_student_support_case" for item in approved["dispatch_results"])

    assert second["status"] == "deduplicated"