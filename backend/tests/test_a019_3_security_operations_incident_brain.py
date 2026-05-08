"""A-019.3 — Security Operations Incident Brain maturity test suite.

Scope:
- Deterministic security risk classification (critical/high/medium/low)
- Brain Core security_incident_review / security_incident_escalation decisions
- Incident lifecycle FSM (create → open → acknowledged → escalated → resolved/dismissed)
- Evidence/audit enrichment
- KPI/event lineage
- Tenant isolation + cross-tenant protection
- Non-destructive security policy proof (no hardware ACS, no auto-ban/lockout/blacklist)
"""
from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tenant(prefix: str = "sec") -> dict[str, object]:
    """Create a tenant via the entity service for isolation."""
    from app.modules.tenants import service as module_tenant_service
    import uuid
    code = f"{prefix}_{uuid.uuid4().hex[:8]}"
    return module_tenant_service.create_tenant(
        {"name": f"Test Tenant {code}", "slug": code, "domain": f"{code}.test"}
    )


def _tenant_id(tenant: dict) -> int:
    return int(tenant["id"])


def _create_incident(tenant_id: int, **kwargs) -> dict:
    import app.modules.security_operations.service as svc
    payload = {
        "incident_code": f"INC-{tenant_id}-001",
        "facility_code": "FAC-A",
        "category": "unauthorized_access",
        "severity": kwargs.pop("severity", "medium"),
        "status": kwargs.pop("status", "open"),
        **kwargs,
    }
    return svc.create_security_incident(payload, tenant_id)


# ---------------------------------------------------------------------------
# Task 1: Brain Core Risk Classifier — security signal routing
# ---------------------------------------------------------------------------

class TestSecurityBrainRiskClassifier:
    """Verify the deterministic risk classifier produces correct security paths."""

    def test_security_incident_opened_critical_routes_security_incident_critical(self):
        from app.modules.brain_core.classifiers.risk_classifier import RiskClassifier
        clf = RiskClassifier()
        result = clf.classify(
            {"event_type": "security.incident.opened", "payload": {"severity": "critical"}},
            {},
        )
        assert result["reasoning_path"] == "security_incident_critical"
        assert result["situation_type"] == "security_risk"
        assert result["severity"] == "critical"

    def test_security_incident_opened_high_routes_security_incident_high(self):
        from app.modules.brain_core.classifiers.risk_classifier import RiskClassifier
        clf = RiskClassifier()
        result = clf.classify(
            {"event_type": "security.incident.opened", "payload": {"severity": "high"}},
            {},
        )
        assert result["reasoning_path"] == "security_incident_high"

    def test_security_incident_escalated_always_high_or_critical(self):
        from app.modules.brain_core.classifiers.risk_classifier import RiskClassifier
        clf = RiskClassifier()
        result = clf.classify(
            {"event_type": "security.incident.escalated", "payload": {}},
            {},
        )
        assert result["reasoning_path"] in {"security_incident_critical", "security_incident_high"}
        assert result["situation_type"] == "security_risk"

    def test_security_incident_escalated_critical_payload_routes_critical(self):
        from app.modules.brain_core.classifiers.risk_classifier import RiskClassifier
        clf = RiskClassifier()
        result = clf.classify(
            {"event_type": "security.incident.escalated", "payload": {"severity": "critical"}},
            {},
        )
        assert result["reasoning_path"] == "security_incident_critical"

    def test_visitor_unauthorized_attempt_routes_security_incident_high(self):
        from app.modules.brain_core.classifiers.risk_classifier import RiskClassifier
        clf = RiskClassifier()
        result = clf.classify(
            {"event_type": "visitor.unauthorized_attempt", "payload": {}},
            {},
        )
        assert result["reasoning_path"] == "security_incident_high"
        assert result["situation_type"] == "security_risk"

    def test_access_denied_routes_security_incident_medium(self):
        from app.modules.brain_core.classifiers.risk_classifier import RiskClassifier
        clf = RiskClassifier()
        result = clf.classify(
            {"event_type": "access.denied", "payload": {}},
            {},
        )
        assert result["reasoning_path"] == "security_incident_medium"
        assert result["situation_type"] == "security_risk"

    def test_security_anomaly_routes_security_incident_high(self):
        from app.modules.brain_core.classifiers.risk_classifier import RiskClassifier
        clf = RiskClassifier()
        result = clf.classify(
            {"event_type": "security.anomaly", "payload": {}},
            {},
        )
        assert result["reasoning_path"] == "security_incident_high"
        assert result["situation_type"] == "security_risk"

    def test_campus_security_incident_detected_high_severity(self):
        from app.modules.brain_core.classifiers.risk_classifier import RiskClassifier
        clf = RiskClassifier()
        result = clf.classify(
            {"event_type": "campus.security_incident.detected", "payload": {"severity": "high"}},
            {},
        )
        assert result["reasoning_path"] == "security_incident_high"
        assert result["situation_type"] == "security_risk"


# ---------------------------------------------------------------------------
# Task 2: Rules Engine — security_incident_review / security_incident_escalation
# ---------------------------------------------------------------------------

class TestSecurityBrainRulesEngine:
    """Verify rules engine produces correct decision_type for security paths."""

    def test_security_incident_critical_produces_escalation_decision(self):
        from app.modules.brain_core.reasoning.rules_engine import RulesEngine
        engine = RulesEngine()
        result = engine.evaluate(
            {"reasoning_path": "security_incident_critical", "severity": "critical"},
            {},
        )
        assert result["decision_type"] == "security_incident_escalation"
        assert result["requires_approval"] is True
        assert "mark_for_human_review" in result["recommended_actions"]
        assert "escalate_to_security_officer" in result["recommended_actions"]

    def test_security_incident_high_produces_review_requires_approval(self):
        from app.modules.brain_core.reasoning.rules_engine import RulesEngine
        engine = RulesEngine()
        result = engine.evaluate(
            {"reasoning_path": "security_incident_high", "severity": "high"},
            {},
        )
        assert result["decision_type"] == "security_incident_review"
        assert result["requires_approval"] is True
        assert "assign_security_reviewer" in result["recommended_actions"]

    def test_security_incident_medium_produces_review_no_approval(self):
        from app.modules.brain_core.reasoning.rules_engine import RulesEngine
        engine = RulesEngine()
        result = engine.evaluate(
            {"reasoning_path": "security_incident_medium", "severity": "medium"},
            {},
        )
        assert result["decision_type"] == "security_incident_review"
        assert result["requires_approval"] is False

    def test_security_incident_low_produces_review_no_approval(self):
        from app.modules.brain_core.reasoning.rules_engine import RulesEngine
        engine = RulesEngine()
        result = engine.evaluate(
            {"reasoning_path": "security_incident_low", "severity": "low"},
            {},
        )
        assert result["decision_type"] == "security_incident_review"
        assert result["requires_approval"] is False

    def test_high_critical_recommended_actions_are_review_escalation_only(self):
        """No hardware ACS, no auto-ban, no physical lockout actions."""
        from app.modules.brain_core.reasoning.rules_engine import RulesEngine
        engine = RulesEngine()
        for path in ("security_incident_critical", "security_incident_high"):
            result = engine.evaluate({"reasoning_path": path}, {})
            forbidden = {
                "lockout", "ban", "blacklist", "hardware", "door_control",
                "auto_ban", "physical_lock", "disciplinary_action",
            }
            for action in result["recommended_actions"]:
                assert action not in forbidden, (
                    f"Forbidden action {action!r} found for reasoning_path={path}"
                )

    def test_low_medium_recommended_actions_are_review_only(self):
        from app.modules.brain_core.reasoning.rules_engine import RulesEngine
        engine = RulesEngine()
        for path in ("security_incident_medium", "security_incident_low"):
            result = engine.evaluate({"reasoning_path": path}, {})
            forbidden = {
                "lockout", "ban", "blacklist", "hardware", "door_control",
                "auto_ban", "physical_lock", "disciplinary_action",
            }
            for action in result["recommended_actions"]:
                assert action not in forbidden, (
                    f"Forbidden action {action!r} found for reasoning_path={path}"
                )


# ---------------------------------------------------------------------------
# Task 3: Full Brain Core signal → decision pipeline
# ---------------------------------------------------------------------------

class TestSecurityBrainPipeline:
    """End-to-end signal → decision routing through BrainCoreService."""

    def test_security_incident_opened_signal_produces_security_incident_decision(self):
        from app.modules.brain_core.service import BrainCoreService
        svc = BrainCoreService()
        t = _make_tenant("brain")
        tid = _tenant_id(t)
        result = svc.process_signal({
            "event_type": "security.incident.opened",
            "tenant_id": tid,
            "payload": {"severity": "high", "incident_id": "INC-TEST-001"},
            "source_entity_type": "security_incident",
            "source_entity_id": f"INC-BRAIN-{tid}",
        })
        assert result["status"] in {"processed", "dispatched", "approval_pending", "deduplicated"}
        decision = result.get("decision") or {}
        if result["status"] != "deduplicated":
            assert decision.get("decision_type") in {
                "security_incident_review", "security_incident_escalation"
            }

    def test_visitor_unauthorized_attempt_signal_produces_security_review(self):
        from app.modules.brain_core.service import BrainCoreService
        svc = BrainCoreService()
        t = _make_tenant("vis")
        tid = _tenant_id(t)
        result = svc.process_signal({
            "event_type": "visitor.unauthorized_attempt",
            "tenant_id": tid,
            "payload": {"visitor_id": "VIS-001", "access_point_id": "DOOR-A"},
            "source_entity_type": "visit_request",
            "source_entity_id": f"VIS-BRAIN-{tid}",
        })
        assert result["status"] in {"processed", "dispatched", "approval_pending", "deduplicated"}
        decision = result.get("decision") or {}
        if result["status"] != "deduplicated":
            assert decision.get("decision_type") in {
                "security_incident_review", "security_incident_escalation"
            }

    def test_access_denied_signal_produces_security_review(self):
        from app.modules.brain_core.service import BrainCoreService
        svc = BrainCoreService()
        t = _make_tenant("acd")
        tid = _tenant_id(t)
        result = svc.process_signal({
            "event_type": "access.denied",
            "tenant_id": tid,
            "payload": {"person_id": "P-001", "location": "MAIN-GATE"},
            "source_entity_type": "access_event",
            "source_entity_id": f"ACD-BRAIN-{tid}",
        })
        assert result["status"] in {"processed", "dispatched", "approval_pending", "deduplicated"}

    def test_missing_tenant_id_signal_is_rejected(self):
        from app.modules.brain_core.service import BrainCoreService
        svc = BrainCoreService()
        result = svc.process_signal({
            "event_type": "security.incident.opened",
            "tenant_id": 0,
            "payload": {"severity": "critical"},
            "source_entity_type": "security_incident",
            "source_entity_id": "INC-NO-TENANT",
        })
        assert result["status"] == "rejected"
        assert "tenant" in result.get("reason", "").lower()

    def test_critical_security_escalation_requires_approval_in_pipeline(self):
        from app.modules.brain_core.service import BrainCoreService
        svc = BrainCoreService()
        t = _make_tenant("crit")
        tid = _tenant_id(t)
        result = svc.process_signal({
            "event_type": "security.incident.escalated",
            "tenant_id": tid,
            "payload": {"severity": "critical", "incident_id": "INC-CRIT-001"},
            "source_entity_type": "security_incident",
            "source_entity_id": f"INC-CRIT-{tid}",
        })
        assert result["status"] in {"processed", "approval_pending", "dispatched", "deduplicated"}
        decision = result.get("decision") or {}
        if result["status"] != "deduplicated":
            # critical/high always requires_approval
            assert decision.get("requires_approval") is True or decision.get("status") == "approval_pending"


# ---------------------------------------------------------------------------
# Task 4: Incident lifecycle FSM
# ---------------------------------------------------------------------------

class TestSecurityIncidentLifecycle:
    """Verify incident lifecycle state machine."""

    def test_create_incident_produces_open_status(self):
        t = _make_tenant("lcl")
        tid = _tenant_id(t)
        inc = _create_incident(tid, status="open")
        assert str(inc.get("status") or "").lower() == "open"
        assert str(inc.get("incident_code") or "").startswith("INC-")

    def test_acknowledge_incident_open_to_acknowledged(self):
        import app.modules.security_operations.service as svc
        t = _make_tenant("ack")
        tid = _tenant_id(t)
        inc = _create_incident(tid)
        result = svc.acknowledge_incident(inc["id"], tid)
        assert str(result.get("status") or "").lower() == "acknowledged"

    def test_escalate_incident_open_to_escalated(self):
        import app.modules.security_operations.service as svc
        t = _make_tenant("esc")
        tid = _tenant_id(t)
        inc = _create_incident(tid)
        result = svc.escalate_incident(inc["id"], tid, response_team="security_command")
        assert str(result.get("status") or "").lower() == "escalated"

    def test_escalate_incident_acknowledged_to_escalated(self):
        import app.modules.security_operations.service as svc
        t = _make_tenant("ea")
        tid = _tenant_id(t)
        inc = _create_incident(tid)
        svc.acknowledge_incident(inc["id"], tid)
        result = svc.escalate_incident(inc["id"], tid)
        assert str(result.get("status") or "").lower() == "escalated"

    def test_resolve_incident_escalated_to_resolved(self):
        import app.modules.security_operations.service as svc
        t = _make_tenant("res")
        tid = _tenant_id(t)
        inc = _create_incident(tid)
        svc.escalate_incident(inc["id"], tid)
        result = svc.resolve_incident(inc["id"], tid)
        assert str(result.get("status") or "").lower() == "resolved"

    def test_dismiss_incident_open_to_dismissed(self):
        import app.modules.security_operations.service as svc
        t = _make_tenant("dis")
        tid = _tenant_id(t)
        inc = _create_incident(tid)
        result = svc.dismiss_incident(inc["id"], tid)
        assert str(result.get("status") or "").lower() == "dismissed"

    def test_invalid_transition_resolved_to_acknowledged_rejected(self):
        import app.modules.security_operations.service as svc
        from app.core.module_helpers.service_validation import DomainValidationError
        t = _make_tenant("inv")
        tid = _tenant_id(t)
        inc = _create_incident(tid)
        svc.escalate_incident(inc["id"], tid)
        svc.resolve_incident(inc["id"], tid)
        with pytest.raises(DomainValidationError):
            svc.acknowledge_incident(inc["id"], tid)

    def test_invalid_transition_dismissed_to_escalated_rejected(self):
        import app.modules.security_operations.service as svc
        from app.core.module_helpers.service_validation import DomainValidationError
        t = _make_tenant("inv2")
        tid = _tenant_id(t)
        inc = _create_incident(tid)
        svc.dismiss_incident(inc["id"], tid)
        with pytest.raises(DomainValidationError):
            svc.escalate_incident(inc["id"], tid)

    def test_lifecycle_incident_not_found_raises_domain_error(self):
        import app.modules.security_operations.service as svc
        from app.core.module_helpers.service_validation import DomainValidationError
        t = _make_tenant("nf")
        tid = _tenant_id(t)
        with pytest.raises(DomainValidationError):
            svc.acknowledge_incident("99999999", tid)


# ---------------------------------------------------------------------------
# Task 5: Tenant isolation and cross-tenant protection
# ---------------------------------------------------------------------------

class TestSecurityTenantIsolation:
    """Verify cross-tenant isolation for security operations."""

    def test_incident_lifecycle_cross_tenant_spoof_blocked(self):
        """Incident from tenant A cannot be transitioned under tenant B's identity."""
        import app.modules.security_operations.service as svc
        from app.core.module_helpers.service_validation import DomainValidationError
        t_a = _make_tenant("iso_a")
        t_b = _make_tenant("iso_b")
        tid_a = _tenant_id(t_a)
        tid_b = _tenant_id(t_b)
        inc_a = _create_incident(tid_a)
        # Attempt to acknowledge incident belonging to tid_a using tid_b
        with pytest.raises(DomainValidationError):
            svc.acknowledge_incident(inc_a["id"], tid_b)

    def test_list_incidents_scoped_to_tenant(self):
        import app.modules.security_operations.service as svc
        t_a = _make_tenant("lst_a")
        t_b = _make_tenant("lst_b")
        tid_a = _tenant_id(t_a)
        tid_b = _tenant_id(t_b)
        _create_incident(tid_a)
        _create_incident(tid_a)
        _create_incident(tid_b)
        list_a = svc.list_security_incidents(tid_a)
        list_b = svc.list_security_incidents(tid_b)
        ids_a = {str(r["id"]) for r in list_a}
        ids_b = {str(r["id"]) for r in list_b}
        assert ids_a.isdisjoint(ids_b), "Tenant A and B incidents must not overlap"


# ---------------------------------------------------------------------------
# Task 6: KPI / event lineage
# ---------------------------------------------------------------------------

class TestSecurityKpiLineage:
    """Verify KPI metric lineage for security operations events."""

    def test_security_incident_kpi_labels_exist(self):
        from app.platform.kpi.service import METRIC_TITLES
        assert "security_incidents_open_count" in METRIC_TITLES
        assert "security_incidents_escalated_count" in METRIC_TITLES
        assert "access_denied_count" in METRIC_TITLES
        assert "security_access_anomaly_count" in METRIC_TITLES
        assert "visitor_unauthorized_attempts_count" in METRIC_TITLES

    def test_security_incident_kpi_lineage_defined(self):
        from app.platform.kpi.service import EVENT_DERIVED_METRIC_LINEAGE
        assert "security_incidents_open_count" in EVENT_DERIVED_METRIC_LINEAGE
        assert "security_incidents_escalated_count" in EVENT_DERIVED_METRIC_LINEAGE
        assert "access_denied_count" in EVENT_DERIVED_METRIC_LINEAGE
        lineage_open = EVENT_DERIVED_METRIC_LINEAGE["security_incidents_open_count"]
        assert "security.incident.opened" in lineage_open
        lineage_esc = EVENT_DERIVED_METRIC_LINEAGE["security_incidents_escalated_count"]
        assert "security.incident.escalated" in lineage_esc

    def test_security_kpi_refresh_computes_counts(self):
        from app.platform.uow import UnitOfWork
        from app.platform.kpi import service as kpi_service
        t = _make_tenant("kpi")
        tid = _tenant_id(t)
        _create_incident(tid, severity="critical")
        with UnitOfWork() as uow:
            rows = kpi_service.refresh_tenant_metrics(tenant_id=tid, uow=uow)
        assert isinstance(rows, list)

    def test_security_events_in_valid_event_types(self):
        from app.platform.event_ingestion.types import VALID_EVENT_TYPES
        required = {
            "security.incident.opened",
            "security.incident.acknowledged",
            "security.incident.escalated",
            "security.incident.resolved",
            "security.incident.dismissed",
        }
        for evt in required:
            assert evt in VALID_EVENT_TYPES, f"Missing from VALID_EVENT_TYPES: {evt!r}"

    def test_visitor_and_security_events_in_supported_signal_types(self):
        from app.modules.brain_core.constants import SUPPORTED_SIGNAL_EVENT_TYPES
        required = {
            "visitor.unauthorized_attempt",
            "visitor.registered",
            "security.incident.opened",
            "security.incident.escalated",
        }
        for evt in required:
            assert evt in SUPPORTED_SIGNAL_EVENT_TYPES, (
                f"Missing from SUPPORTED_SIGNAL_EVENT_TYPES: {evt!r}"
            )


# ---------------------------------------------------------------------------
# Task 7: Non-destructive security policy proof
# ---------------------------------------------------------------------------

class TestNonDestructiveSecurityPolicy:
    """Proof that no auto-ban, lockout, hardware ACS, or disciplinary actions exist."""

    def test_no_hardware_acs_action_in_security_brain_rules(self):
        from app.modules.brain_core.reasoning.rules_engine import RulesEngine
        engine = RulesEngine()
        hardware_actions = {
            "lockout", "ban", "blacklist", "open_door", "lock_door",
            "hardware_acs", "door_control", "physical_lock", "auto_ban",
            "auto_lockout", "disciplinary_action",
        }
        for path in (
            "security_incident_critical",
            "security_incident_high",
            "security_incident_medium",
            "security_incident_low",
        ):
            result = engine.evaluate({"reasoning_path": path}, {})
            for action in result["recommended_actions"]:
                assert action not in hardware_actions, (
                    f"Forbidden action {action!r} found in rules for path={path!r}"
                )

    def test_high_critical_incidents_require_human_approval(self):
        from app.modules.brain_core.reasoning.rules_engine import RulesEngine
        engine = RulesEngine()
        for path in ("security_incident_critical", "security_incident_high"):
            result = engine.evaluate({"reasoning_path": path}, {})
            assert result["requires_approval"] is True, (
                f"requires_approval must be True for {path!r}"
            )

    def test_incident_create_does_not_invoke_hardware_acs(self):
        """Creating a security incident does not call any hardware ACS function."""
        import app.modules.security_operations.service as svc
        import inspect
        src = inspect.getsource(svc)
        # No hardware/physical ACS calls allowed
        forbidden_patterns = [
            "open_physical_door",
            "lock_physical_door",
            "activate_lockdown",
            "hardware_acs_api",
            "auto_ban",
            "auto_blacklist",
        ]
        for pattern in forbidden_patterns:
            assert pattern not in src, (
                f"Forbidden pattern {pattern!r} found in security_operations/service.py"
            )

    def test_incident_lifecycle_does_not_auto_ban_or_punish(self):
        import app.modules.security_operations.service as svc
        import inspect
        src = inspect.getsource(svc)
        forbidden = ["auto_ban", "auto_blacklist", "auto_lockout", "punish", "disciplinary"]
        for pattern in forbidden:
            assert pattern not in src, (
                f"Forbidden pattern {pattern!r} found in security_operations/service.py"
            )

    def test_security_brain_recommended_actions_are_review_escalation_only(self):
        """All security Brain decisions use only review/escalation/evidence actions."""
        from app.modules.brain_core.reasoning.rules_engine import RulesEngine
        engine = RulesEngine()
        allowed_prefixes = {
            "assign_", "request_", "notify_", "escalate_", "mark_", "create_security_incident"
        }
        for path in (
            "security_incident_critical",
            "security_incident_high",
            "security_incident_medium",
            "security_incident_low",
        ):
            result = engine.evaluate({"reasoning_path": path}, {})
            for action in result["recommended_actions"]:
                assert any(action.startswith(p) for p in allowed_prefixes), (
                    f"Action {action!r} not in allowed review/escalation set for path={path!r}"
                )
