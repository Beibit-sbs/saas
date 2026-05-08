"""A-019.4 — Visitor Access Workflow Integration tests.

Goal:
- Prove end-to-end software-only integration across visitor_management,
  access_control, and security_operations Brain routing.
- Enforce non-destructive policy (no hardware ACS, no physical door control,
  no auto-ban/blacklist/disciplinary actions).
"""
from __future__ import annotations

from uuid import uuid4

import pytest

import app.modules.access_control.service as access_svc
import app.modules.visitor_management.service as visitor_svc
from app.modules.brain_core.classifiers.risk_classifier import RiskClassifier
from app.modules.brain_core.reasoning.rules_engine import RulesEngine
from app.modules.brain_core.service import BrainCoreService
from app.modules.tenants import service as tenant_svc
from app.modules.university_core.tenant_entity_api import list_entities_for_tenant
from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.kpi import service as kpi_service
from app.platform.uow import UnitOfWork


def _create_tenant(prefix: str = "a0194") -> int:
    slug = f"{prefix}-{uuid4().hex[:8]}"
    tenant = tenant_svc.create_tenant({"slug": slug, "name": f"{prefix} tenant"})
    return int(tenant["id"])


def _register_and_approve_checkin(tenant_id: int, badge: str = "B-100") -> dict[str, object]:
    visit = visitor_svc.register_visitor(
        tenant_id,
        name="Visitor A",
        host_id="host-01",
        visit_date="2026-05-08",
    )
    visitor_svc.approve_visit(tenant_id, visit_id=visit["visit_id"])
    checked_in = visitor_svc.check_in_visitor(tenant_id, visit_id=visit["visit_id"], badge_number=badge)
    return checked_in


class TestA0194WorkflowIntegration:
    def test_approved_visitor_checkin_emits_evidence_without_physical_door_action(self, reset_shared_state):
        tenant_id = _create_tenant("chk")
        checked_in = _register_and_approve_checkin(tenant_id, badge="B-201")

        assert checked_in["status"] == "CHECKED_IN"
        assert checked_in["badge"] == "B-201"

        events = event_ingestion_service.list_events_for_tenant(tenant_id, limit=200)
        event_types = {str(e.get("event_type") or "") for e in events}
        assert "visitor.checked_in" in event_types
        # Software-only policy: no physical/hardware door events.
        assert not any("door" in et for et in event_types)

    def test_checked_in_visitor_access_grant_is_software_only_evidence(self, reset_shared_state):
        tenant_id = _create_tenant("grt")
        checked_in = _register_and_approve_checkin(tenant_id, badge="B-202")

        card = access_svc.issue_card(
            tenant_id,
            holder_id=str(checked_in["badge"]),
            zones=["MAIN-GATE"],
            actor="ops.user",
        )
        result = access_svc.attempt_access(
            tenant_id,
            card_id=card["card_id"],
            zone="MAIN-GATE",
            actor="ops.user",
        )
        assert result["granted"] is True

        logs = access_svc.list_access_logs(tenant_id)
        assert any(str(row.get("result") or "") == "GRANTED" for row in logs)

    def test_unauthorized_attempt_creates_visitor_evidence(self, reset_shared_state):
        tenant_id = _create_tenant("una")
        result = visitor_svc.record_unauthorized_attempt(
            tenant_id,
            visitor_name="Unknown X",
            zone="LAB-1",
            access_point_id="DOOR-L1",
            reason="no_approval",
        )
        assert result["event"] == "UNAUTHORIZED_ATTEMPT"

        logs = list_entities_for_tenant("visit_logs", tenant_id)
        assert any(str(row.get("event") or "") == "UNAUTHORIZED_ATTEMPT" for row in logs)

    def test_unauthorized_attempt_routes_to_security_incident_review(self, reset_shared_state):
        tenant_id = _create_tenant("brain1")
        svc = BrainCoreService()

        result = svc.process_signal(
            {
                "event_type": "visitor.unauthorized_attempt",
                "tenant_id": tenant_id,
                "payload": {"visitor_id": "V-1", "access_point_id": "DOOR-A"},
                "source_entity_type": "visit_request",
                "source_entity_id": f"VIS-{tenant_id}",
            }
        )

        assert result["status"] in {"processed", "approval_pending", "dispatched", "deduplicated"}
        decision = result.get("decision") or {}
        if result["status"] != "deduplicated":
            assert decision.get("decision_type") in {
                "security_incident_review",
                "security_incident_escalation",
            }

    def test_access_denied_routes_to_security_incident_review(self, reset_shared_state):
        tenant_id = _create_tenant("brain2")
        svc = BrainCoreService()

        result = svc.process_signal(
            {
                "event_type": "access.denied",
                "tenant_id": tenant_id,
                "payload": {"person_id": "P-1", "location": "MAIN-GATE"},
                "source_entity_type": "access_event",
                "source_entity_id": f"ACD-{tenant_id}",
            }
        )

        assert result["status"] in {"processed", "approval_pending", "dispatched", "deduplicated"}
        decision = result.get("decision") or {}
        if result["status"] != "deduplicated":
            assert decision.get("decision_type") in {
                "security_incident_review",
                "security_incident_escalation",
            }

    def test_high_critical_security_path_requires_review_or_approval(self, reset_shared_state):
        tenant_id = _create_tenant("crit")
        svc = BrainCoreService()

        result = svc.process_signal(
            {
                "event_type": "security.incident.escalated",
                "tenant_id": tenant_id,
                "payload": {"severity": "critical", "incident_id": "INC-CRIT-1"},
                "source_entity_type": "security_incident",
                "source_entity_id": f"INC-{tenant_id}",
            }
        )

        assert result["status"] in {"processed", "approval_pending", "dispatched", "deduplicated"}
        decision = result.get("decision") or {}
        if result["status"] != "deduplicated":
            assert decision.get("requires_approval") is True or decision.get("status") == "approval_pending"

    def test_low_medium_paths_do_not_produce_destructive_actions(self, reset_shared_state):
        clf = RiskClassifier()
        eng = RulesEngine()

        classification = clf.classify({"event_type": "access.denied", "payload": {}}, {})
        decision = eng.evaluate(classification, {})

        forbidden_tokens = {
            "hardware",
            "door",
            "lock",
            "lockout",
            "ban",
            "blacklist",
            "disciplinary",
            "punish",
        }
        actions = [str(a) for a in decision.get("recommended_actions", [])]
        for action in actions:
            lower = action.lower()
            assert not any(token in lower for token in forbidden_tokens)

    def test_cross_tenant_spoof_payload_cannot_override_authoritative_tenant(self, reset_shared_state):
        t1 = _create_tenant("t1")
        t2 = _create_tenant("t2")
        svc = BrainCoreService()

        result = svc.process_signal(
            {
                "event_type": "visitor.unauthorized_attempt",
                "tenant_id": t1,
                "payload": {
                    "tenant_id": t2,
                    "visitor_id": "V-SPOOF",
                    "access_point_id": "DOOR-X",
                },
                "source_entity_type": "visit_request",
                "source_entity_id": "VIS-SPOOF-1",
            }
        )

        decision = result.get("decision") or {}
        if decision:
            assert int(decision.get("tenant_id", t1)) == t1

    def test_no_hardware_acs_action_invoked_in_security_brain_rules(self, reset_shared_state):
        eng = RulesEngine()
        decision = eng.evaluate({"reasoning_path": "security_incident_high", "severity": "high"}, {})

        forbidden = {
            "open_physical_door",
            "lock_physical_door",
            "hardware_acs",
            "auto_lockout",
            "auto_ban",
            "auto_blacklist",
            "disciplinary_action",
        }
        actions = {str(a) for a in decision.get("recommended_actions", [])}
        assert actions.isdisjoint(forbidden)

    def test_no_auto_lockout_ban_blacklist_or_disciplinary_action(self, reset_shared_state):
        eng = RulesEngine()
        for path in (
            "security_incident_critical",
            "security_incident_high",
            "security_incident_medium",
            "security_incident_low",
        ):
            decision = eng.evaluate({"reasoning_path": path}, {})
            forbidden_tokens = (
                "lockout",
                "ban",
                "blacklist",
                "disciplinary",
            )
            for action in decision.get("recommended_actions", []):
                al = str(action).lower()
                assert not any(tok in al for tok in forbidden_tokens)

    def test_kpi_readiness_for_visitor_access_security_events(self, reset_shared_state):
        tenant_id = _create_tenant("kpi")

        event_ingestion_service.record_event(tenant_id=tenant_id, event_type="visitor.checked_in", payload={})
        event_ingestion_service.record_event(
            tenant_id=tenant_id,
            event_type="visitor.unauthorized_attempt",
            payload={"zone": "LAB-1"},
        )
        event_ingestion_service.record_event(tenant_id=tenant_id, event_type="access.denied", payload={})
        event_ingestion_service.record_event(
            tenant_id=tenant_id,
            event_type="security.incident.opened",
            payload={"severity": "high"},
        )

        with UnitOfWork() as uow:
            rows = kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)

        values = {str(r.get("metric_key")): r.get("metric_value") for r in rows}
        assert values.get("visitors_checked_in_count", 0) >= 1
        assert values.get("visitor_unauthorized_attempts_count", 0) >= 1
        assert values.get("access_denied_count", 0) >= 1
        assert values.get("security_incidents_open_count", 0) >= 1
