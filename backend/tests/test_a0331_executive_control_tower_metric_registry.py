from __future__ import annotations

from pathlib import Path

import pytest

from app.core.module_helpers.service_validation import TenantRequiredError, TenantResourceNotFoundError
from app.core.tenant import get_current_tenant
from app.modules.executive_control_tower import permissions as ect_permissions
from app.modules.executive_control_tower import router as router_module
from app.modules.executive_control_tower import service
from app.modules.executive_control_tower.metric_registry import (
    ASSIGNMENT_EXECUTION,
    AUDIT_COMPLIANCE,
    CORRESPONDENCE_WORKFLOW,
    DATA_SOURCE,
    DEPARTMENT_PERFORMANCE,
    DECREE_WORKFLOW,
    DOCUMENT_WORKFLOW,
    EXECUTIVE_OVERVIEW,
    FAKE_METRICS,
    GROUP_METADATA,
    SLA_RISK_BOTTLENECK,
    STRATEGY_KPI,
    get_metric_by_id,
    get_metric_group,
    get_metric_registry_definitions,
    get_registry_summary,
    list_metric_groups,
    validate_metric_registry,
)


MODULE_DIR = Path(__file__).resolve().parents[1] / "app" / "modules" / "executive_control_tower"
MAIN_FILE = Path(__file__).resolve().parents[1] / "app" / "main.py"

REQUIRED_GROUPS = {
    EXECUTIVE_OVERVIEW,
    ASSIGNMENT_EXECUTION,
    DOCUMENT_WORKFLOW,
    DECREE_WORKFLOW,
    CORRESPONDENCE_WORKFLOW,
    SLA_RISK_BOTTLENECK,
    STRATEGY_KPI,
    AUDIT_COMPLIANCE,
    DEPARTMENT_PERFORMANCE,
}

EXPECTED_METRIC_IDS = {
    "active_assignments_total",
    "overdue_assignments_total",
    "documents_in_workflow_total",
    "decrees_pending_signed_metadata_total",
    "correspondence_waiting_response_total",
    "sla_compliance_rate",
    "escalations_open_total",
    "audit_events_24h_total",
    "executive_attention_required_total",
    "assignments_by_status",
    "assignments_overdue_by_department",
    "assignment_average_completion_days",
    "reports_submitted_total",
    "assignments_returned_for_revision_total",
    "assignment_evidence_attachment_rate",
    "assignment_escalation_rate",
    "assignments_without_recent_report",
    "executor_workload_summary",
    "department_assignment_completion_rate",
    "documents_total",
    "documents_registered_total",
    "documents_under_review_total",
    "documents_returned_for_revision_total",
    "documents_approved_total",
    "documents_signed_metadata_total",
    "documents_archived_total",
    "document_average_review_cycle_days",
    "documents_linked_to_assignments_total",
    "documents_without_assignment_link_total",
    "decrees_total",
    "decrees_in_legal_review_total",
    "decrees_pending_rector_review_total",
    "decrees_approved_for_signing_total",
    "decrees_signed_metadata_total",
    "decrees_registered_total",
    "decrees_archived_total",
    "decree_average_legal_review_days",
    "decrees_linked_to_assignment_total",
    "incoming_correspondence_total",
    "incoming_waiting_route_total",
    "incoming_in_progress_total",
    "incoming_responded_total",
    "outgoing_correspondence_total",
    "outgoing_under_review_total",
    "outgoing_sent_metadata_total",
    "outgoing_delivered_metadata_total",
    "correspondence_average_route_time_days",
    "overdue_aging_buckets",
    "escalations_by_level",
    "unresolved_bottlenecks_total",
    "departments_with_high_overdue_load",
    "assignments_overdue_more_than_7_days",
    "documents_review_overdue_total",
    "correspondence_response_overdue_total",
    "escalation_queue_total",
    "manual_confirmation_pending_total",
    "strategic_initiatives_total",
    "initiatives_linked_to_assignments_total",
    "initiatives_linked_to_documents_total",
    "kpi_evidence_coverage_rate",
    "kpi_stale_evidence_total",
    "kpi_without_execution_link_total",
    "strategy_execution_bottlenecks_total",
    "audit_events_total",
    "status_history_completeness_rate",
    "archived_records_total",
    "hard_delete_events_total_expected_zero",
    "dashboard_guard_failures_total",
    "permission_denied_events_total",
    "cross_tenant_access_blocked_total",
    "incomplete_data_metric_count",
    "stale_metric_count",
    "department_active_assignments_total",
    "department_overdue_assignments_total",
    "department_documents_in_review_total",
    "department_correspondence_pending_total",
    "department_sla_compliance_rate",
    "department_execution_bottlenecks_total",
    "department_audit_activity_total",
}

STRATEGY_METRIC_IDS = {
    "strategic_initiatives_total",
    "initiatives_linked_to_assignments_total",
    "initiatives_linked_to_documents_total",
    "kpi_evidence_coverage_rate",
    "kpi_stale_evidence_total",
    "kpi_without_execution_link_total",
    "strategy_execution_bottlenecks_total",
}


def _definitions():
    return get_metric_registry_definitions()


def _route_table():
    return [route for route in router_module.router.routes if getattr(route, "path", "").startswith("/api/admin/executive-control-tower")]


def _module_texts() -> dict[str, str]:
    return {path.name: path.read_text() for path in MODULE_DIR.glob("*.py")}


def test_import_sanity() -> None:
    assert router_module.router.prefix == "/api/admin/executive-control-tower"
    assert ect_permissions.READ in ect_permissions.EXECUTIVE_CONTROL_TOWER_PERMISSIONS


def test_metric_registry_completeness() -> None:
    definitions = _definitions()
    registry_ids = {metric.metric_id for metric in definitions}
    assert registry_ids == EXPECTED_METRIC_IDS
    assert len(definitions) == 79
    summary = get_registry_summary()
    assert summary["total_metrics"] == 79
    assert summary["total_groups"] == 9


def test_metric_id_uniqueness() -> None:
    definitions = _definitions()
    metric_ids = [metric.metric_id for metric in definitions]
    assert len(metric_ids) == len(set(metric_ids))


@pytest.mark.parametrize("group_id", sorted(REQUIRED_GROUPS))
def test_metric_groups_exist(group_id: str) -> None:
    group = get_metric_group(group_id)
    assert group is not None
    assert group.group_id == group_id
    assert group.metrics


def test_group_registry_matches_group_metadata() -> None:
    groups = list_metric_groups()
    assert {group.group_id for group in groups} == set(GROUP_METADATA)


@pytest.mark.parametrize("metric", _definitions(), ids=lambda metric: metric.metric_id)
def test_metric_registry_invariants(metric) -> None:
    assert metric.metric_id in EXPECTED_METRIC_IDS
    assert metric.fake_metrics is FAKE_METRICS
    assert metric.data_source == DATA_SOURCE
    assert metric.permission_required
    assert metric.source_module
    assert metric.source_tables
    assert metric.source_fields
    assert metric.limitations
    assert metric.value is None
    assert metric.runtime_status in {"FOUNDATION_CONTRACT_ONLY", "DEFERRED_UNTIL_STRATEGY_MODULE"}


@pytest.mark.parametrize("metric_id", sorted(STRATEGY_METRIC_IDS))
def test_strategy_metrics_are_future_contracts(metric_id: str) -> None:
    metric = get_metric_by_id(metric_id)
    assert metric is not None
    assert metric.readiness == "FUTURE_CONTRACT"
    assert metric.runtime_status == "DEFERRED_UNTIL_STRATEGY_MODULE"
    assert metric.incomplete_data is True
    assert metric.value is None


@pytest.mark.parametrize("tenant_id", [None, 0, -1])
def test_service_invalid_tenant_fail_closed(tenant_id: int | None) -> None:
    with pytest.raises(TenantRequiredError):
        service.get_metric_registry_summary(tenant_id)  # type: ignore[arg-type]


def test_service_valid_tenant_returns_registry() -> None:
    response = service.get_metric_registry_summary(tenant_id=7)
    assert response.total_metrics == 79
    assert response.fake_metrics is False
    assert response.data_source == DATA_SOURCE
    assert response.incomplete_data is True
    assert len(response.groups) == 9


def test_service_metric_detail_valid_id() -> None:
    response = service.get_metric_detail(tenant_id=7, metric_id="audit_events_total")
    assert response.metric.metric_id == "audit_events_total"
    assert response.fake_metrics is False
    assert response.incomplete_data is True


def test_service_metric_detail_unknown_id_fails_cleanly() -> None:
    with pytest.raises(TenantResourceNotFoundError):
        service.get_metric_detail(tenant_id=7, metric_id="unknown_metric")


@pytest.mark.parametrize(
    "builder",
    [
        service.get_executive_summary,
        service.get_assignment_execution_summary,
        service.get_document_workflow_summary,
        service.get_decree_workflow_summary,
        service.get_correspondence_workflow_summary,
        service.get_sla_risk_summary,
        service.get_strategy_kpi_summary,
        service.get_audit_compliance_summary,
        service.get_department_performance_summary,
    ],
    ids=[
        "summary",
        "assignments",
        "documents",
        "decrees",
        "correspondence",
        "sla-risk",
        "strategy-kpis",
        "audit-compliance",
        "department-performance",
    ],
)
def test_summary_endpoints_return_foundation_metadata(builder) -> None:
    response = builder(tenant_id=11)
    assert response.fake_metrics is False
    assert response.data_source == DATA_SOURCE
    assert response.incomplete_data is True
    assert response.generated_at.tzinfo is not None
    assert response.limitations


def test_health_response_reports_registry_state() -> None:
    response = service.get_health(tenant_id=5)
    assert response.registry_valid is True
    assert response.total_groups == 9
    assert response.total_metrics == 79
    assert response.fake_metrics is False


def test_registry_validation_passes() -> None:
    result = validate_metric_registry()
    assert result["valid"] is True
    assert result["errors"] == []


def test_router_has_exactly_twelve_get_routes() -> None:
    routes = _route_table()
    assert len(routes) == 12
    assert {tuple(sorted(route.methods)) for route in routes} == {("GET",)}


@pytest.mark.parametrize("route", _route_table(), ids=lambda route: route.path)
def test_router_routes_are_get_only(route) -> None:
    assert route.methods == {"GET"}


@pytest.mark.parametrize("route", _route_table(), ids=lambda route: route.path)
def test_router_routes_have_permission_dependency(route) -> None:
    dependencies = [dependency.call for dependency in route.dependant.dependencies]
    assert any(getattr(call, "__module__", "") == "app.modules.rbac.security" and getattr(call, "__name__", "") == "dependency" for call in dependencies)


@pytest.mark.parametrize("route", _route_table(), ids=lambda route: route.path)
def test_router_routes_have_tenant_dependency(route) -> None:
    dependencies = [dependency.call for dependency in route.dependant.dependencies]
    assert any(call is get_current_tenant for call in dependencies)


def test_main_registers_router() -> None:
    source = MAIN_FILE.read_text()
    assert "from app.modules.executive_control_tower.router import router as executive_control_tower_router" in source
    assert "app.include_router(executive_control_tower_router)" in source


def test_no_provider_or_external_dispatch_strings_in_module() -> None:
    texts = _module_texts()
    forbidden = (
        "requests.post",
        "httpx.post",
        "send_email",
        "send_sms",
        "smtp",
        "twilio",
        "BackgroundTasks",
        "create_task(",
    )
    combined = "\n".join(texts.values())
    for token in forbidden:
        assert token not in combined


def test_no_mutation_markers_in_module() -> None:
    texts = _module_texts()
    combined = "\n".join(texts.values())
    forbidden = ("@router.post", "@router.patch", "@router.put", "@router.delete", ".add(", ".delete(", "session.delete", "INSERT ", "UPDATE ", "DELETE FROM")
    for token in forbidden:
        assert token not in combined


def test_no_production_claims_in_module() -> None:
    combined = "\n".join(_module_texts().values())
    forbidden = ("production-ready", "L5", "L6")
    for token in forbidden:
        assert token not in combined