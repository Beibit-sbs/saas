"""A-016.6 Wave 4 KPI backend tests.

Covers:
- All Wave 4 metric keys are present after refresh_tenant_metrics()
- Correct event-derived computation for each domain group:
  Academic Integrity / Exam Proctoring / Thesis Governance / Research Ethics / Case Resolution
- Zero-value metrics do not crash (no events = 0 values)
- Severity rules defined for all thresholded Wave 4 metric keys
- Non-thresholded Wave 4 metrics return policy_pack=null
- METRIC_TITLES defined for all Wave 4 metric keys
- EVENT_DERIVED_METRIC_LINEAGE defined for all Wave 4 metric keys
- VALID_EVENT_TYPES includes all Wave 4 event types
"""
from __future__ import annotations

from uuid import uuid4

from tests.conftest import ADMIN_HEADERS, client

from app.modules.auth.token_service import create_access_token
from app.modules.tenants import service as module_tenant_service
from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.event_ingestion.types import VALID_EVENT_TYPES
from app.platform.kpi import service as kpi_service
from app.platform.uow import UnitOfWork

# ─── Wave 4 metric key sets ───────────────────────────────────────────────────

WAVE4_ACADEMIC_INTEGRITY_KEYS = {
    "academic_integrity_risk_count",
    "academic_integrity_review_cases_count",
    "academic_integrity_high_risk_count",
    "academic_integrity_cases_pending_review",
}

WAVE4_EXAM_PROCTORING_KEYS = {
    "exam_proctoring_violations_count",
    "exam_integrity_reviews_count",
    "exam_integrity_high_risk_count",
    "exam_integrity_requires_approval_count",
}

WAVE4_THESIS_GOVERNANCE_KEYS = {
    "thesis_governance_risk_count",
    "thesis_supervisor_assignment_needed_count",
    "thesis_review_delayed_count",
    "thesis_governance_requires_approval_count",
}

WAVE4_RESEARCH_ETHICS_KEYS = {
    "research_ethics_review_cases_count",
    "research_ethics_high_risk_count",
    "research_ethics_missing_documents_count",
    "research_ethics_requires_approval_count",
}

WAVE4_CASE_RESOLUTION_KEYS = {
    "integrity_cases_open_count",
    "integrity_cases_escalated_count",
    "integrity_cases_resolved_count",
    "integrity_cases_evidence_requested_count",
    "integrity_case_resolution_sla_risk_count",
}

WAVE4_ALL_KEYS = (
    WAVE4_ACADEMIC_INTEGRITY_KEYS
    | WAVE4_EXAM_PROCTORING_KEYS
    | WAVE4_THESIS_GOVERNANCE_KEYS
    | WAVE4_RESEARCH_ETHICS_KEYS
    | WAVE4_CASE_RESOLUTION_KEYS
)

# Thresholded: have KPI_SEVERITY_RULES entries
WAVE4_THRESHOLDED_KEYS = {
    "academic_integrity_risk_count",
    "academic_integrity_high_risk_count",
    "academic_integrity_cases_pending_review",
    "exam_proctoring_violations_count",
    "exam_integrity_high_risk_count",
    "exam_integrity_requires_approval_count",
    "thesis_governance_risk_count",
    "thesis_supervisor_assignment_needed_count",
    "thesis_review_delayed_count",
    "thesis_governance_requires_approval_count",
    "research_ethics_review_cases_count",
    "research_ethics_high_risk_count",
    "research_ethics_missing_documents_count",
    "research_ethics_requires_approval_count",
    "integrity_cases_open_count",
    "integrity_cases_escalated_count",
    "integrity_case_resolution_sla_risk_count",
}

# Non-thresholded: no severity rules, policy_pack must be null
WAVE4_NON_THRESHOLDED_KEYS = WAVE4_ALL_KEYS - WAVE4_THRESHOLDED_KEYS

WAVE4_EVENT_TYPES = {
    "academic_integrity.violation.detected",
    "academic_integrity.risk_detected",
    "academic_integrity.case.opened",
    "academic_integrity.case.review_required",
    "academic_integrity.case.resolved",
    "academic_integrity.case.dismissed",
    "academic_integrity.case.evidence_requested",
    "exam.proctoring.violation_detected",
    "faculty.proctoring.violation_detected",
    "exam.proctoring.suspicious_activity_detected",
    "exam.proctoring.multiple_faces_detected",
    "exam.proctoring.face_mismatch_detected",
    "exam.proctoring.forbidden_app_detected",
    "exam.proctoring.camera_absent_detected",
    "thesis.governance.risk_detected",
    "thesis.supervisor.assignment_needed",
    "thesis.supervisor.overloaded",
    "thesis.review.delayed",
    "research_ethics.application.submitted",
    "research_ethics.review.overdue",
    "research_ethics.high_risk.detected",
    "research_ethics.missing_consent.detected",
    "research_ethics.document_missing.detected",
}

# ─── helpers ──────────────────────────────────────────────────────────────────


def _create_tenant(prefix: str) -> int:
    slug = f"{prefix}-{uuid4().hex[:8]}"
    tenant = module_tenant_service.create_tenant({"slug": slug, "name": f"{prefix} Tenant"})
    return int(tenant["id"])


def _analytics_read_headers(*, tenant_id: int) -> dict[str, str]:
    token = create_access_token(
        user_id=f"kpi.viewer.{tenant_id}@example.com",
        roles=["student"],
        auth_source="test",
        tenant_id=tenant_id,
        permissions=["analytics.data.read"],
    )
    return {"Authorization": f"Bearer {token}"}


def _emit_event(*, tenant_id: int, event_type: str, count: int = 1) -> None:
    for idx in range(count):
        event_ingestion_service.record_event(
            tenant_id=tenant_id,
            event_type=event_type,
            payload={"seq": idx + 1, "source": "test-a0166"},
        )


def _refresh_metrics(*, tenant_id: int) -> None:
    with UnitOfWork() as uow:
        kpi_service.refresh_tenant_metrics(tenant_id=tenant_id, uow=uow)


def _cards_by_key(body: dict) -> dict[str, dict]:
    return {str(item["key"]): item for item in body["kpis"]}


# ─── registration tests ───────────────────────────────────────────────────────


def test_wave4_metric_titles_defined_for_all_keys() -> None:
    """All Wave 4 metric keys must have display titles in METRIC_TITLES."""
    for key in WAVE4_ALL_KEYS:
        assert key in kpi_service.METRIC_TITLES, f"METRIC_TITLES missing entry for '{key}'"
        assert kpi_service.METRIC_TITLES[key], f"METRIC_TITLES['{key}'] must be non-empty"


def test_wave4_event_lineage_defined_for_all_keys() -> None:
    """All Wave 4 metric keys must have event lineage in EVENT_DERIVED_METRIC_LINEAGE."""
    for key in WAVE4_ALL_KEYS:
        assert key in kpi_service.EVENT_DERIVED_METRIC_LINEAGE, (
            f"EVENT_DERIVED_METRIC_LINEAGE missing entry for '{key}'"
        )
        assert len(kpi_service.EVENT_DERIVED_METRIC_LINEAGE[key]) > 0, (
            f"EVENT_DERIVED_METRIC_LINEAGE['{key}'] must list at least one event type"
        )


def test_wave4_event_types_in_valid_event_types() -> None:
    """All Wave 4 event types used by the KPI engine must be present in VALID_EVENT_TYPES."""
    for evt in WAVE4_EVENT_TYPES:
        assert evt in VALID_EVENT_TYPES, f"VALID_EVENT_TYPES missing '{evt}'"


def test_wave4_thresholded_keys_have_severity_rules() -> None:
    """All thresholded Wave 4 metric keys must have KPI_SEVERITY_RULES entries."""
    for key in WAVE4_THRESHOLDED_KEYS:
        assert key in kpi_service.KPI_SEVERITY_RULES, f"KPI_SEVERITY_RULES missing entry for '{key}'"
        rule = kpi_service.KPI_SEVERITY_RULES[key]
        assert "basis" in rule, f"KPI_SEVERITY_RULES['{key}'] must have 'basis'"
        assert "policy_pack" in rule, f"KPI_SEVERITY_RULES['{key}'] must have 'policy_pack'"
        assert "warning_gte" in rule, f"KPI_SEVERITY_RULES['{key}'] must have 'warning_gte'"
        assert "critical_gte" in rule, f"KPI_SEVERITY_RULES['{key}'] must have 'critical_gte'"


def test_wave4_non_thresholded_keys_absent_from_severity_rules() -> None:
    """Non-thresholded Wave 4 metric keys must not appear in KPI_SEVERITY_RULES."""
    for key in WAVE4_NON_THRESHOLDED_KEYS:
        assert key not in kpi_service.KPI_SEVERITY_RULES, (
            f"KPI_SEVERITY_RULES should NOT have an entry for non-thresholded metric '{key}'"
        )


# ─── zero-event baseline tests ────────────────────────────────────────────────


def test_wave4_all_keys_present_after_refresh_zero_events(reset_shared_state) -> None:
    """refresh_tenant_metrics() returns all Wave 4 keys even with no relevant events."""
    tenant_id = _create_tenant("a0166-zero")
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    keys = {item["key"] for item in response.json()["kpis"]}
    for k in WAVE4_ALL_KEYS:
        assert k in keys, f"KPI key '{k}' missing from /api/analytics/kpis response"


def test_wave4_non_thresholded_keys_policy_pack_null(reset_shared_state) -> None:
    """Non-thresholded Wave 4 metrics return policy_pack=null from the API."""
    tenant_id = _create_tenant("a0166-null-pack")
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    for key in WAVE4_NON_THRESHOLDED_KEYS:
        assert cards[key]["policy_pack"] is None, f"'{key}' expected policy_pack=null"


# ─── academic integrity metrics ───────────────────────────────────────────────


def test_wave4_academic_integrity_risk_count_on_violation_event(reset_shared_state) -> None:
    """academic_integrity_risk_count increments on academic_integrity.violation.detected events."""
    tenant_id = _create_tenant("a0166-ai-risk")
    _emit_event(tenant_id=tenant_id, event_type="academic_integrity.violation.detected", count=3)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["academic_integrity_risk_count"]["value"]) >= 3


def test_wave4_academic_integrity_risk_count_warning_severity(reset_shared_state) -> None:
    """academic_integrity_risk_count reaches warning severity when >= 1."""
    tenant_id = _create_tenant("a0166-ai-sev")
    _emit_event(tenant_id=tenant_id, event_type="academic_integrity.violation.detected", count=1)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert cards["academic_integrity_risk_count"]["severity"] in {"warning", "critical"}


def test_wave4_academic_integrity_cases_pending_review_on_review_required(reset_shared_state) -> None:
    """academic_integrity_cases_pending_review increments on case.review_required events."""
    tenant_id = _create_tenant("a0166-ai-pending")
    _emit_event(tenant_id=tenant_id, event_type="academic_integrity.case.review_required", count=2)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["academic_integrity_cases_pending_review"]["value"]) >= 2


# ─── exam proctoring metrics ──────────────────────────────────────────────────


def test_wave4_exam_proctoring_violations_count_on_violation_event(reset_shared_state) -> None:
    """exam_proctoring_violations_count increments on exam.proctoring.violation_detected events."""
    tenant_id = _create_tenant("a0166-ep-viol")
    _emit_event(tenant_id=tenant_id, event_type="exam.proctoring.violation_detected", count=4)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["exam_proctoring_violations_count"]["value"]) >= 4


def test_wave4_exam_integrity_reviews_count_on_suspicious_activity(reset_shared_state) -> None:
    """exam_integrity_reviews_count increments on exam.proctoring.suspicious_activity_detected events."""
    tenant_id = _create_tenant("a0166-ep-review")
    _emit_event(tenant_id=tenant_id, event_type="exam.proctoring.suspicious_activity_detected", count=2)
    _emit_event(tenant_id=tenant_id, event_type="exam.proctoring.multiple_faces_detected", count=1)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["exam_integrity_reviews_count"]["value"]) >= 3


def test_wave4_exam_integrity_high_risk_on_face_mismatch(reset_shared_state) -> None:
    """exam_integrity_high_risk_count increments on face_mismatch and multiple_faces events."""
    tenant_id = _create_tenant("a0166-ep-highrisk")
    _emit_event(tenant_id=tenant_id, event_type="exam.proctoring.face_mismatch_detected", count=2)
    _emit_event(tenant_id=tenant_id, event_type="exam.proctoring.multiple_faces_detected", count=1)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["exam_integrity_high_risk_count"]["value"]) >= 3


# ─── thesis governance metrics ────────────────────────────────────────────────


def test_wave4_thesis_governance_risk_count_on_governance_risk_event(reset_shared_state) -> None:
    """thesis_governance_risk_count increments on thesis.governance.risk_detected events."""
    tenant_id = _create_tenant("a0166-tg-risk")
    _emit_event(tenant_id=tenant_id, event_type="thesis.governance.risk_detected", count=3)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["thesis_governance_risk_count"]["value"]) >= 3


def test_wave4_thesis_supervisor_assignment_needed_count(reset_shared_state) -> None:
    """thesis_supervisor_assignment_needed_count increments on supervisor.assignment_needed events."""
    tenant_id = _create_tenant("a0166-tg-supervisor")
    _emit_event(tenant_id=tenant_id, event_type="thesis.supervisor.assignment_needed", count=2)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["thesis_supervisor_assignment_needed_count"]["value"]) >= 2


def test_wave4_thesis_review_delayed_count(reset_shared_state) -> None:
    """thesis_review_delayed_count increments on thesis.review.delayed events."""
    tenant_id = _create_tenant("a0166-tg-delayed")
    _emit_event(tenant_id=tenant_id, event_type="thesis.review.delayed", count=1)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["thesis_review_delayed_count"]["value"]) >= 1


# ─── research ethics metrics ──────────────────────────────────────────────────


def test_wave4_research_ethics_review_cases_on_submitted_event(reset_shared_state) -> None:
    """research_ethics_review_cases_count increments on research_ethics.application.submitted events."""
    tenant_id = _create_tenant("a0166-re-cases")
    _emit_event(tenant_id=tenant_id, event_type="research_ethics.application.submitted", count=4)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["research_ethics_review_cases_count"]["value"]) >= 4


def test_wave4_research_ethics_high_risk_count(reset_shared_state) -> None:
    """research_ethics_high_risk_count increments on high_risk.detected + missing_consent events."""
    tenant_id = _create_tenant("a0166-re-highrisk")
    _emit_event(tenant_id=tenant_id, event_type="research_ethics.high_risk.detected", count=2)
    _emit_event(tenant_id=tenant_id, event_type="research_ethics.missing_consent.detected", count=1)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["research_ethics_high_risk_count"]["value"]) >= 3


def test_wave4_research_ethics_missing_documents_count(reset_shared_state) -> None:
    """research_ethics_missing_documents_count increments on document_missing.detected events."""
    tenant_id = _create_tenant("a0166-re-docs")
    _emit_event(tenant_id=tenant_id, event_type="research_ethics.document_missing.detected", count=2)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["research_ethics_missing_documents_count"]["value"]) >= 2


# ─── case resolution metrics ──────────────────────────────────────────────────


def test_wave4_integrity_cases_open_count_on_case_opened(reset_shared_state) -> None:
    """integrity_cases_open_count increments on academic_integrity.case.opened events."""
    tenant_id = _create_tenant("a0166-cr-open")
    _emit_event(tenant_id=tenant_id, event_type="academic_integrity.case.opened", count=5)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["integrity_cases_open_count"]["value"]) >= 5


def test_wave4_integrity_cases_resolved_count_on_case_resolved(reset_shared_state) -> None:
    """integrity_cases_resolved_count increments on academic_integrity.case.resolved events."""
    tenant_id = _create_tenant("a0166-cr-resolved")
    _emit_event(tenant_id=tenant_id, event_type="academic_integrity.case.resolved", count=3)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["integrity_cases_resolved_count"]["value"]) >= 3


def test_wave4_integrity_cases_evidence_requested_count(reset_shared_state) -> None:
    """integrity_cases_evidence_requested_count increments on evidence_requested events."""
    tenant_id = _create_tenant("a0166-cr-evidence")
    _emit_event(tenant_id=tenant_id, event_type="academic_integrity.case.evidence_requested", count=2)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert int(cards["integrity_cases_evidence_requested_count"]["value"]) >= 2


def test_wave4_integrity_case_sla_risk_count_warning_severity(reset_shared_state) -> None:
    """integrity_case_resolution_sla_risk_count reaches warning severity when >= 1."""
    tenant_id = _create_tenant("a0166-cr-sla")
    _emit_event(tenant_id=tenant_id, event_type="academic_integrity.case.review_required", count=1)
    _refresh_metrics(tenant_id=tenant_id)

    response = client.get("/api/analytics/kpis", headers=_analytics_read_headers(tenant_id=tenant_id))
    assert response.status_code == 200, response.text
    cards = _cards_by_key(response.json())
    assert cards["integrity_case_resolution_sla_risk_count"]["severity"] in {"warning", "critical"}
