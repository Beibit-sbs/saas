from __future__ import annotations

from uuid import uuid4

import app.modules.access_control.service as access_svc
import app.modules.visitor_management.service as visitor_svc
from app.modules.brain_core.service import BrainCoreService
from app.modules.brain_core.classifiers.risk_classifier import RiskClassifier
from app.modules.brain_core.reasoning.rules_engine import RulesEngine
from app.modules.tenants import service as tenant_svc
from app.modules.university_core.tenant_entity_api import list_entities_for_tenant
from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.kpi import service as kpi_service
from app.platform.uow import UnitOfWork


FORBIDDEN_TOKENS = (
    "hardware",
    "door",
    "physical",
    "lockout",
    "ban",
    "blacklist",
    "disciplinary",
    "punish",
)


def _create_tenant(prefix: str) -> int:
    slug = f"{prefix}-{uuid4().hex[:8]}"
    row = tenant_svc.create_tenant({"slug": slug, "name": f"{prefix} tenant"})
    return int(row["id"])


def _register_approve_checkin(*, tenant_id: int, badge: str) -> dict[str, object]:
    visit = visitor_svc.register_visitor(
        tenant_id,
        name="Visitor A0197",
        host_id="host-0197",
        visit_date="2026-05-09",
    )
    visit_id = visit["visit_id"]
    visitor_svc.approve_visit(tenant_id, visit_id=visit_id)
    return visitor_svc.check_in_visitor(
        tenant_id,
        visit_id=visit_id,
        badge_number=badge,
    )


def _refresh_values(*, tenant_id: int) -> dict[str, int]:
    with UnitOfWork() as uow:
        rows = kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)
    return {str(item["metric_key"]): int(item["metric_value"]) for item in rows}


def _refresh_dashboard(*, tenant_id: int) -> dict[str, object]:
    with UnitOfWork() as uow:
        return kpi_service.refresh_tenant_dashboard_snapshot(tenant_id=tenant_id, uow=uow)


def _assert_non_destructive_actions(actions: list[object]) -> None:
    for action in actions:
        lower = str(action).lower()
        assert not any(token in lower for token in FORBIDDEN_TOKENS)


def test_approved_visitor_checkin_to_access_evidence_contract(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0197-flow1")

    checked_in = _register_approve_checkin(tenant_id=tenant_id, badge="B-A0197-01")
    card = access_svc.issue_card(
        tenant_id,
        holder_id=str(checked_in["badge"]),
        zones=["MAIN-GATE"],
        actor="ops.a0197",
    )
    card_id = card["card_id"]
    access_result = access_svc.attempt_access(
        tenant_id,
        card_id=card_id,
        zone="MAIN-GATE",
        actor="ops.a0197",
    )

    assert checked_in["status"] == "CHECKED_IN"
    assert access_result["granted"] is True

    logs = access_svc.list_access_logs(tenant_id)
    assert any(str(row.get("result") or "") == "GRANTED" for row in logs)

    events = event_ingestion_service.list_events_for_tenant(tenant_id, limit=200)
    event_types = {str(item.get("event_type") or "") for item in events}
    assert "visitor.checked_in" in event_types
    assert not any("door" in ev for ev in event_types)
    assert not any("hardware" in ev for ev in event_types)


def test_unauthorized_visitor_attempt_routes_to_security_incident_brain(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0197-flow2")

    evidence = visitor_svc.record_unauthorized_attempt(
        tenant_id,
        visitor_name="Unknown Visitor",
        zone="LAB-9",
        access_point_id="AP-9",
        reason="missing approval",
    )
    assert evidence["event"] == "UNAUTHORIZED_ATTEMPT"

    classifier = RiskClassifier()
    classification = classifier.classify(
        {
            "event_type": "visitor.unauthorized_attempt",
            "tenant_id": tenant_id,
            "payload": {"visitor_name": "Unknown Visitor", "access_point_id": "AP-9"},
        },
        {},
    )
    assert classification["reasoning_path"] == "security_incident_high"

    decision = RulesEngine().evaluate(classification, {})
    assert decision["decision_type"] in {"security_incident_review", "security_incident_escalation"}
    assert bool(decision.get("requires_approval")) is True
    _assert_non_destructive_actions(list(decision.get("recommended_actions", [])))

    result = BrainCoreService().process_signal(
        {
            "event_type": "visitor.unauthorized_attempt",
            "tenant_id": tenant_id,
            "payload": {"visitor_name": "Unknown Visitor", "access_point_id": "AP-9"},
            "source_entity_type": "visit_log",
            "source_entity_id": f"una-{uuid4().hex}",
        }
    )
    assert result["status"] in {"processed", "approval_pending", "dispatched", "deduplicated"}
    if result["status"] != "deduplicated":
        resolved = result.get("decision") or {}
        assert resolved.get("decision_type") in {"security_incident_review", "security_incident_escalation"}


def test_access_denied_routes_to_security_review_without_lockout(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0197-flow3")

    checked_in = _register_approve_checkin(tenant_id=tenant_id, badge="B-A0197-03")
    card = access_svc.issue_card(
        tenant_id,
        holder_id=str(checked_in["badge"]),
        zones=["LIBRARY"],
        actor="ops.a0197",
    )
    card_id = card["card_id"]

    denied = access_svc.attempt_access(
        tenant_id,
        card_id=card_id,
        zone="MAIN-GATE",
        actor="ops.a0197",
    )
    assert denied["granted"] is False
    assert denied["reason"] == "zone_not_permitted"

    # Non-destructive policy: deny does not auto-revoke/suspend/lockout card.
    active_cards = access_svc.list_cards(tenant_id, status="ACTIVE")
    assert any(row.get("id") == card_id for row in active_cards)

    brain = BrainCoreService().process_signal(
        {
            "event_type": "access.denied",
            "tenant_id": tenant_id,
            "payload": {"card_id": card_id, "zone": "MAIN-GATE"},
            "source_entity_type": "access_log",
            "source_entity_id": f"den-{uuid4().hex}",
        }
    )
    assert brain["status"] in {"processed", "approval_pending", "dispatched", "deduplicated"}
    if brain["status"] != "deduplicated":
        decision = brain.get("decision") or {}
        assert decision.get("decision_type") in {"security_incident_review", "security_incident_escalation"}
        _assert_non_destructive_actions(list(decision.get("recommended_actions", [])))


def test_security_kpi_aggregation_from_visitor_access_incident_events(reset_shared_state) -> None:
    tenant_id = _create_tenant("a0197-flow4")

    _register_approve_checkin(tenant_id=tenant_id, badge="B-A0197-04")
    visitor_svc.record_unauthorized_attempt(
        tenant_id,
        visitor_name="Unknown B",
        zone="LAB-1",
        access_point_id="AP-1",
        reason="badge mismatch",
    )

    card = access_svc.issue_card(tenant_id, holder_id="holder-a0197-4", zones=["ZONE-A"], actor="ops.a0197")
    access_svc.attempt_access(tenant_id, card_id=card["card_id"], zone="ZONE-B", actor="ops.a0197")

    # KPI aggregation consumes event_ingestion summary; ensure denied evidence is present there.
    event_ingestion_service.record_event(
        tenant_id=tenant_id,
        event_type="access.denied",
        payload={"card_id": card["card_id"], "zone": "ZONE-B", "source": "a0197"},
    )

    event_ingestion_service.record_event(
        tenant_id=tenant_id,
        event_type="security.incident.opened",
        payload={"severity": "high", "incident_id": f"inc-{uuid4().hex[:8]}"},
    )
    event_ingestion_service.record_event(
        tenant_id=tenant_id,
        event_type="security.incident.escalated",
        payload={"severity": "high", "incident_id": f"inc-{uuid4().hex[:8]}"},
    )

    values = _refresh_values(tenant_id=tenant_id)
    assert values["visitors_checked_in_count"] >= 1
    assert values["visitor_unauthorized_attempts_count"] >= 1
    assert values["access_denied_count"] >= 1
    assert values["security_incidents_open_count"] >= 1
    assert values["security_incidents_escalated_count"] >= 1

    dashboard = _refresh_dashboard(tenant_id=tenant_id)
    cards = dashboard.get("snapshot_json", {}).get("cards", []) if isinstance(dashboard, dict) else []
    metric_keys = {str(row.get("metric_key") or "") for row in cards}
    assert "visitor_unauthorized_attempts_count" in metric_keys
    assert "access_denied_count" in metric_keys
    assert "security_incidents_open_count" in metric_keys
    assert "security_incidents_escalated_count" in metric_keys


def test_tenant_spoof_payload_cannot_override_authoritative_tenant(reset_shared_state) -> None:
    tenant_a = _create_tenant("a0197-ta")
    tenant_b = _create_tenant("a0197-tb")

    visitor_svc.record_unauthorized_attempt(
        tenant_a,
        visitor_name="Spoof Candidate",
        zone="A-ZONE",
        access_point_id="AP-A",
        reason="spoof-test",
    )

    logs_a = list_entities_for_tenant("visit_logs", tenant_a)
    logs_b = list_entities_for_tenant("visit_logs", tenant_b)
    assert len(logs_a) >= 1
    assert len(logs_b) == 0

    result = BrainCoreService().process_signal(
        {
            "event_type": "visitor.unauthorized_attempt",
            "tenant_id": tenant_a,
            "payload": {
                "tenant_id": tenant_b,
                "visitor_name": "Spoof Candidate",
                "access_point_id": "AP-A",
            },
            "source_entity_type": "visit_log",
            "source_entity_id": f"spoof-{uuid4().hex}",
        }
    )
    decision = result.get("decision") or {}
    if decision:
        assert int(decision.get("tenant_id", tenant_a)) == tenant_a

    _refresh_values(tenant_id=tenant_a)
    _refresh_values(tenant_id=tenant_b)
    with UnitOfWork() as uow:
        kpis_a = kpi_service.get_tenant_product_kpis(tenant_id=tenant_a, uow=uow)
        kpis_b = kpi_service.get_tenant_product_kpis(tenant_id=tenant_b, uow=uow)
    assert int(kpis_a["tenant_id"]) == tenant_a
    assert int(kpis_b["tenant_id"]) == tenant_b


def test_no_destructive_security_automation_contract(reset_shared_state) -> None:
    engine = RulesEngine()

    for path, severity in [
        ("security_incident_critical", "critical"),
        ("security_incident_high", "high"),
        ("security_incident_medium", "medium"),
        ("security_incident_low", "low"),
    ]:
        decision = engine.evaluate({"reasoning_path": path, "severity": severity}, {})
        actions = list(decision.get("recommended_actions", []))
        _assert_non_destructive_actions(actions)

        # Critical/high flows must be review/escalation with human approval semantics.
        if severity in {"critical", "high"}:
            assert decision["decision_type"] in {"security_incident_review", "security_incident_escalation"}
            assert bool(decision.get("requires_approval")) is True
