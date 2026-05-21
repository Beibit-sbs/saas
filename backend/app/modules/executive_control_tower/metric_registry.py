"""Deterministic metric registry for the Executive Control Tower foundation."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from app.modules.executive_control_tower import permissions
from app.modules.executive_control_tower.schemas import (
    EvidenceLink,
    ExecutiveControlTowerMetric,
    ExecutiveControlTowerMetricGroup,
)

DATA_SOURCE = "computed_from_governance_workflows"
FAKE_METRICS = False

EXECUTIVE_OVERVIEW = "EXECUTIVE_OVERVIEW"
ASSIGNMENT_EXECUTION = "ASSIGNMENT_EXECUTION"
DOCUMENT_WORKFLOW = "DOCUMENT_WORKFLOW"
DECREE_WORKFLOW = "DECREE_WORKFLOW"
CORRESPONDENCE_WORKFLOW = "CORRESPONDENCE_WORKFLOW"
SLA_RISK_BOTTLENECK = "SLA_RISK_BOTTLENECK"
STRATEGY_KPI = "STRATEGY_KPI"
AUDIT_COMPLIANCE = "AUDIT_COMPLIANCE"
DEPARTMENT_PERFORMANCE = "DEPARTMENT_PERFORMANCE"

GROUP_METADATA: dict[str, tuple[str, str]] = {
    EXECUTIVE_OVERVIEW: (
        "Executive Overview",
        "Cross-workflow executive summary metrics for the read-only foundation.",
    ),
    ASSIGNMENT_EXECUTION: (
        "Assignment Execution",
        "Rector assignment execution metrics exposed without live mutation or orchestration.",
    ),
    DOCUMENT_WORKFLOW: (
        "Document Workflow",
        "Document workflow registry contracts backed by deterministic source mappings.",
    ),
    DECREE_WORKFLOW: (
        "Decree Workflow",
        "Decree workflow registry contracts backed by deterministic source mappings.",
    ),
    CORRESPONDENCE_WORKFLOW: (
        "Correspondence Workflow",
        "Correspondence workflow registry contracts backed by deterministic source mappings.",
    ),
    SLA_RISK_BOTTLENECK: (
        "SLA / Risk / Bottleneck",
        "Operational SLA and bottleneck contracts for read-only executive visibility.",
    ),
    STRATEGY_KPI: (
        "Strategy KPI",
        "Future-contract strategy KPI metrics reserved until a real strategy source exists.",
    ),
    AUDIT_COMPLIANCE: (
        "Audit / Compliance",
        "Audit and compliance registry contracts for read-only oversight.",
    ),
    DEPARTMENT_PERFORMANCE: (
        "Department Performance",
        "Operational department visibility metrics without punitive ranking behavior.",
    ),
}

_FOUNDATION_LIMITATIONS = [
    "Read-only backend foundation; live aggregation is deferred beyond A-033.1-RUNTIME.",
    "Unavailable live values remain null with incomplete_data=True.",
]
_FUTURE_LIMITATIONS = [
    "Future-contract metric; a real strategy source must exist before runtime values are exposed.",
    "Null values remain intentional until a deterministic source module is implemented.",
]


def _make_evidence_link(source_module: str, entity: str, table: str, reference_field: str = "id") -> EvidenceLink:
    return EvidenceLink(
        label="Source contract",
        source_module=source_module,
        source_entity=entity,
        source_table=table,
        reference_field=reference_field,
        reference_value=None,
        available=False,
        limitations=["Live evidence links are deferred in the foundation release."],
    )


def _metric(
    *,
    metric_id: str,
    metric_group: str,
    label: str,
    description: str,
    source_module: str,
    source_entities: list[str],
    source_tables: list[str],
    source_fields: list[str],
    calculation_method: str,
    formula: str,
    permission_required: str,
    unit: str | None = None,
    limitations: list[str] | None = None,
    runtime_status: str = "FOUNDATION_CONTRACT_ONLY",
    readiness: str = "CONTRACT_DEFINED",
    incomplete_data: bool = True,
) -> ExecutiveControlTowerMetric:
    metric_limitations = list(_FOUNDATION_LIMITATIONS)
    if limitations:
        metric_limitations.extend(limitations)
    evidence_links = [_make_evidence_link(source_module, source_entities[0], source_tables[0])]
    return ExecutiveControlTowerMetric(
        metric_id=metric_id,
        metric_group=metric_group,
        label=label,
        description=description,
        value=None,
        unit=unit,
        source_module=source_module,
        source_entities=source_entities,
        source_tables=source_tables,
        source_fields=source_fields,
        calculation_method=calculation_method,
        formula=formula,
        tenant_scope="tenant_id_required",
        permission_required=permission_required,
        staleness_threshold_minutes=60,
        evidence_links=evidence_links,
        data_source=DATA_SOURCE,
        fake_metrics=FAKE_METRICS,
        incomplete_data=incomplete_data,
        limitations=metric_limitations,
        failure_mode="INCOMPLETE_DATA",
        runtime_status=runtime_status,
        readiness=readiness,
    )


def _strategy_metric(
    metric_id: str,
    label: str,
    description: str,
    formula: str,
) -> ExecutiveControlTowerMetric:
    return ExecutiveControlTowerMetric(
        metric_id=metric_id,
        metric_group=STRATEGY_KPI,
        label=label,
        description=description,
        value=None,
        unit=None,
        source_module="future_strategy_module",
        source_entities=["SOURCE_ENTITY_TO_VERIFY_IN_RUNTIME_SPEC"],
        source_tables=["SOURCE_TABLE_TO_VERIFY_IN_RUNTIME_SPEC"],
        source_fields=["SOURCE_FIELD_TO_VERIFY_IN_RUNTIME_SPEC"],
        calculation_method="future_contract",
        formula=formula,
        tenant_scope="tenant_id_required",
        permission_required=permissions.STRATEGY_READ,
        staleness_threshold_minutes=None,
        evidence_links=[
            EvidenceLink(
                label="Future source contract",
                source_module="future_strategy_module",
                source_entity="SOURCE_ENTITY_TO_VERIFY_IN_RUNTIME_SPEC",
                source_table="SOURCE_TABLE_TO_VERIFY_IN_RUNTIME_SPEC",
                reference_field="SOURCE_FIELD_TO_VERIFY_IN_RUNTIME_SPEC",
                reference_value=None,
                available=False,
                limitations=["Strategy source not implemented in A-033.1-RUNTIME."],
            )
        ],
        data_source=DATA_SOURCE,
        fake_metrics=FAKE_METRICS,
        incomplete_data=True,
        limitations=list(_FUTURE_LIMITATIONS),
        failure_mode="INCOMPLETE_DATA",
        runtime_status="DEFERRED_UNTIL_STRATEGY_MODULE",
        readiness="FUTURE_CONTRACT",
    )


def _assignment_metric(
    metric_id: str,
    label: str,
    description: str,
    formula: str,
    source_fields: list[str],
    *,
    permission: str = permissions.ASSIGNMENTS_READ,
    unit: str | None = None,
    limitations: list[str] | None = None,
    source_module: str = "rector_assignment_workflow",
    source_entities: list[str] | None = None,
    source_tables: list[str] | None = None,
) -> ExecutiveControlTowerMetric:
    return _metric(
        metric_id=metric_id,
        metric_group=ASSIGNMENT_EXECUTION,
        label=label,
        description=description,
        source_module=source_module,
        source_entities=source_entities or ["RectorAssignment"],
        source_tables=source_tables or ["rector_assignments"],
        source_fields=source_fields,
        calculation_method="read_only_registry_contract",
        formula=formula,
        permission_required=permission,
        unit=unit,
        limitations=limitations,
    )


def _document_metric(metric_id: str, label: str, description: str, formula: str, source_fields: list[str], *, permission: str = permissions.DOCUMENTS_READ, source_entities: list[str] | None = None, source_tables: list[str] | None = None, limitations: list[str] | None = None, unit: str | None = None) -> ExecutiveControlTowerMetric:
    return _metric(
        metric_id=metric_id,
        metric_group=DOCUMENT_WORKFLOW,
        label=label,
        description=description,
        source_module="document_workflow_os",
        source_entities=source_entities or ["Document"],
        source_tables=source_tables or ["doc_documents"],
        source_fields=source_fields,
        calculation_method="read_only_registry_contract",
        formula=formula,
        permission_required=permission,
        limitations=limitations,
        unit=unit,
    )


def _decree_metric(metric_id: str, label: str, description: str, formula: str, source_fields: list[str], *, limitations: list[str] | None = None, unit: str | None = None) -> ExecutiveControlTowerMetric:
    return _metric(
        metric_id=metric_id,
        metric_group=DECREE_WORKFLOW,
        label=label,
        description=description,
        source_module="document_workflow_os",
        source_entities=["OrderDecree"],
        source_tables=["doc_order_decrees"],
        source_fields=source_fields,
        calculation_method="read_only_registry_contract",
        formula=formula,
        permission_required=permissions.DOCUMENTS_READ,
        limitations=limitations,
        unit=unit,
    )


def _correspondence_metric(metric_id: str, label: str, description: str, formula: str, source_fields: list[str], *, limitations: list[str] | None = None, unit: str | None = None) -> ExecutiveControlTowerMetric:
    return _metric(
        metric_id=metric_id,
        metric_group=CORRESPONDENCE_WORKFLOW,
        label=label,
        description=description,
        source_module="document_workflow_os",
        source_entities=["CorrespondenceItem"],
        source_tables=["doc_correspondence_items"],
        source_fields=source_fields,
        calculation_method="read_only_registry_contract",
        formula=formula,
        permission_required=permissions.DOCUMENTS_READ,
        limitations=limitations,
        unit=unit,
    )


def _sla_metric(metric_id: str, label: str, description: str, formula: str, source_fields: list[str], *, source_module: str = "rector_assignment_workflow", source_entities: list[str] | None = None, source_tables: list[str] | None = None, permission: str = permissions.SLA_RISK_READ, limitations: list[str] | None = None, unit: str | None = None) -> ExecutiveControlTowerMetric:
    return _metric(
        metric_id=metric_id,
        metric_group=SLA_RISK_BOTTLENECK,
        label=label,
        description=description,
        source_module=source_module,
        source_entities=source_entities or ["RectorAssignment"],
        source_tables=source_tables or ["rector_assignments"],
        source_fields=source_fields,
        calculation_method="read_only_registry_contract",
        formula=formula,
        permission_required=permission,
        limitations=limitations,
        unit=unit,
    )


def _audit_metric(metric_id: str, label: str, description: str, formula: str, source_fields: list[str], *, source_module: str = "governance_audit_contract", source_entities: list[str] | None = None, source_tables: list[str] | None = None, permission: str = permissions.AUDIT_READ, limitations: list[str] | None = None, unit: str | None = None) -> ExecutiveControlTowerMetric:
    return _metric(
        metric_id=metric_id,
        metric_group=AUDIT_COMPLIANCE,
        label=label,
        description=description,
        source_module=source_module,
        source_entities=source_entities or ["RectorAssignmentAuditEvent"],
        source_tables=source_tables or ["rector_assignment_audit_events"],
        source_fields=source_fields,
        calculation_method="read_only_registry_contract",
        formula=formula,
        permission_required=permission,
        limitations=limitations,
        unit=unit,
    )


def _department_metric(metric_id: str, label: str, description: str, formula: str, source_fields: list[str], *, source_module: str = "rector_assignment_workflow", source_entities: list[str] | None = None, source_tables: list[str] | None = None, limitations: list[str] | None = None, unit: str | None = None) -> ExecutiveControlTowerMetric:
    return _metric(
        metric_id=metric_id,
        metric_group=DEPARTMENT_PERFORMANCE,
        label=label,
        description=description,
        source_module=source_module,
        source_entities=source_entities or ["RectorAssignment"],
        source_tables=source_tables or ["rector_assignments"],
        source_fields=source_fields,
        calculation_method="read_only_registry_contract",
        formula=formula,
        permission_required=permissions.DEPARTMENT_READ,
        limitations=limitations,
        unit=unit,
    )


def _build_metric_definitions() -> tuple[ExecutiveControlTowerMetric, ...]:
    metrics: list[ExecutiveControlTowerMetric] = [
        _metric(
            metric_id="active_assignments_total",
            metric_group=EXECUTIVE_OVERVIEW,
            label="Active Assignments Total",
            description="Count of active rector assignments in tenant scope.",
            source_module="rector_assignment_workflow",
            source_entities=["RectorAssignment"],
            source_tables=["rector_assignments"],
            source_fields=["tenant_id", "status", "archived_at", "is_archived"],
            calculation_method="read_only_registry_contract",
            formula="count active rector assignments for tenant scope",
            permission_required=permissions.SUMMARY_READ,
        ),
        _metric(
            metric_id="overdue_assignments_total",
            metric_group=EXECUTIVE_OVERVIEW,
            label="Overdue Assignments Total",
            description="Count of active rector assignments with due_date before today.",
            source_module="rector_assignment_workflow",
            source_entities=["RectorAssignment"],
            source_tables=["rector_assignments"],
            source_fields=["tenant_id", "status", "due_date", "archived_at", "is_archived"],
            calculation_method="read_only_registry_contract",
            formula="count active assignments where due_date is overdue",
            permission_required=permissions.SUMMARY_READ,
        ),
        _metric(
            metric_id="documents_in_workflow_total",
            metric_group=EXECUTIVE_OVERVIEW,
            label="Documents In Workflow Total",
            description="Count of non-archived documents in workflow statuses.",
            source_module="document_workflow_os",
            source_entities=["Document"],
            source_tables=["doc_documents"],
            source_fields=["tenant_id", "status", "archived_at"],
            calculation_method="read_only_registry_contract",
            formula="count non-archived documents in workflow statuses",
            permission_required=permissions.SUMMARY_READ,
        ),
        _metric(
            metric_id="decrees_pending_signed_metadata_total",
            metric_group=EXECUTIVE_OVERVIEW,
            label="Decrees Pending Signed Metadata Total",
            description="Count of decrees awaiting signed metadata.",
            source_module="document_workflow_os",
            source_entities=["OrderDecree"],
            source_tables=["doc_order_decrees"],
            source_fields=["status", "signed_by_user_id", "signed_at"],
            calculation_method="read_only_registry_contract",
            formula="count decrees in signing-ready states with null signed metadata",
            permission_required=permissions.SUMMARY_READ,
        ),
        _metric(
            metric_id="correspondence_waiting_response_total",
            metric_group=EXECUTIVE_OVERVIEW,
            label="Correspondence Waiting Response Total",
            description="Count of correspondence items in waiting-response states.",
            source_module="document_workflow_os",
            source_entities=["CorrespondenceItem"],
            source_tables=["doc_correspondence_items"],
            source_fields=["direction", "status", "received_at", "sent_at"],
            calculation_method="read_only_registry_contract",
            formula="count correspondence items in waiting-response states",
            permission_required=permissions.SUMMARY_READ,
        ),
        _metric(
            metric_id="escalations_open_total",
            metric_group=EXECUTIVE_OVERVIEW,
            label="Escalations Open Total",
            description="Count of open rector assignment escalations.",
            source_module="rector_assignment_workflow",
            source_entities=["RectorAssignmentEscalation"],
            source_tables=["rector_assignment_escalations"],
            source_fields=["status", "triggered_at", "resolved_at", "escalation_level"],
            calculation_method="read_only_registry_contract",
            formula="count escalation rows with open status",
            permission_required=permissions.SUMMARY_READ,
        ),
        _metric(
            metric_id="executive_attention_required_total",
            metric_group=EXECUTIVE_OVERVIEW,
            label="Executive Attention Required Total",
            description="Cross-vertical bundle of items that require executive review.",
            source_module="cross_vertical_contract",
            source_entities=["RectorAssignment", "Document", "OrderDecree", "CorrespondenceItem", "RectorAssignmentEscalation"],
            source_tables=["rector_assignments", "doc_documents", "doc_order_decrees", "doc_correspondence_items", "rector_assignment_escalations"],
            source_fields=["status", "due_date", "signed_at", "received_at", "escalation_level"],
            calculation_method="read_only_registry_contract",
            formula="sum documented attention conditions across governance workflow sources",
            permission_required=permissions.SUMMARY_READ,
        ),
        _assignment_metric("assignments_by_status", "Assignments By Status", "Grouped rector assignments by status.", "group rector assignments by status", ["status"]),
        _assignment_metric("assignments_overdue_by_department", "Assignments Overdue By Department", "Overdue assignment counts by responsible unit.", "group overdue assignments by responsible_unit_id", ["responsible_unit_id", "status", "due_date"]),
        _assignment_metric("assignment_average_completion_days", "Assignment Average Completion Days", "Average time to complete rector assignments.", "average completed_at minus created_at for completed assignments", ["created_at", "completed_at", "status"], unit="days"),
        _assignment_metric("reports_submitted_total", "Reports Submitted Total", "Count of submitted assignment reports.", "count assignment reports with submitted_at in tenant scope", ["submitted_at", "status"], limitations=["Uses report metadata contracts until live aggregation is added."]),
        _assignment_metric("assignments_returned_for_revision_total", "Assignments Returned For Revision Total", "Count of assignments in returned-for-revision status.", "count assignments where status is returned for revision", ["status"]),
        _assignment_metric("assignment_evidence_attachment_rate", "Assignment Evidence Attachment Rate", "Share of assignments with non-deleted evidence records.", "assignments with evidence rows divided by relevant assignments", ["assignment_id", "is_deleted"], unit="ratio"),
        _assignment_metric("assignment_escalation_rate", "Assignment Escalation Rate", "Share of assignments that generated escalation records.", "assignments with escalation rows divided by relevant assignments", ["assignment_id", "status"], permission=permissions.SLA_RISK_READ, unit="ratio"),
        _assignment_metric("assignments_without_recent_report", "Assignments Without Recent Report", "Active assignments missing a recent submitted report.", "count active assignments with no report inside runtime threshold", ["assignment_id", "submitted_at", "status"], limitations=["Recent-report threshold remains a documented runtime follow-up."]),
        _assignment_metric("executor_workload_summary", "Executor Workload Summary", "Grouped workload summary by assignment assignee or unit.", "group active assignments by assignee linkage", ["user_id", "unit_id", "assignment_id", "status"], source_entities=["RectorAssignmentAssignee"], source_tables=["rector_assignment_assignees"], limitations=["Assignee lookup is contract-defined; live enrichment is deferred."] ),
        _assignment_metric("department_assignment_completion_rate", "Department Assignment Completion Rate", "Department-level assignment completion rate.", "completed assignments divided by total assignments per responsible unit", ["responsible_unit_id", "status", "completed_at"], permission=permissions.DEPARTMENT_READ, unit="ratio"),
        _document_metric("documents_total", "Documents Total", "Count of document rows in tenant scope.", "count document rows in tenant scope", ["tenant_id"]),
        _document_metric("documents_registered_total", "Documents Registered Total", "Count of documents with registry metadata.", "count documents with registry_number and registry_date", ["registry_number", "registry_date"]),
        _document_metric("documents_under_review_total", "Documents Under Review Total", "Count of documents under review.", "count documents in review states", ["status", "document_id", "created_at"], source_entities=["Document", "DocumentReview"], source_tables=["doc_documents", "doc_document_reviews"]),
        _document_metric("documents_returned_for_revision_total", "Documents Returned For Revision Total", "Count of documents returned for revision.", "count documents where status is returned for revision", ["status"]),
        _document_metric("documents_approved_total", "Documents Approved Total", "Count of approved documents.", "count documents where status is approved", ["status"]),
        _document_metric("documents_signed_metadata_total", "Documents Signed Metadata Total", "Count of documents with recorded signed metadata.", "count documents with runtime verified signed metadata fields", ["status", "registry_number", "registry_date", "SOURCE_FIELD_TO_VERIFY_IN_RUNTIME_SPEC"], limitations=["Signed metadata source fields are preserved as runtime verification placeholders."]),
        _document_metric("documents_archived_total", "Documents Archived Total", "Count of archived documents or archive records.", "count archived documents and linked archive records", ["archived_at", "entity_type", "entity_id"], source_entities=["Document", "ArchiveRecord"], source_tables=["doc_documents", "doc_archive_records"]),
        _document_metric("document_average_review_cycle_days", "Document Average Review Cycle Days", "Average document review cycle duration.", "average terminal review timestamp minus document created_at", ["created_at", "status", "document_id", "created_at"], source_entities=["Document", "DocumentReview"], source_tables=["doc_documents", "doc_document_reviews"], unit="days", limitations=["Terminal review timestamp remains a documented runtime follow-up."]),
        _document_metric("documents_linked_to_assignments_total", "Documents Linked To Assignments Total", "Count of documents linked to assignments.", "count distinct documents linked by direct or bridge linkage", ["linked_assignment_id", "assignment_id", "document_id"], source_entities=["Document", "DocumentAssignmentLink"], source_tables=["doc_documents", "doc_document_assignment_links"]),
        _document_metric("documents_without_assignment_link_total", "Documents Without Assignment Link Total", "Count of documents without assignment linkage.", "count documents with no direct or bridge assignment linkage", ["id", "linked_assignment_id", "document_id", "assignment_id"], source_entities=["Document", "DocumentAssignmentLink"], source_tables=["doc_documents", "doc_document_assignment_links"]),
        _decree_metric("decrees_total", "Decrees Total", "Count of decree rows in tenant scope.", "count decree rows in tenant scope", ["tenant_id"]),
        _decree_metric("decrees_in_legal_review_total", "Decrees In Legal Review Total", "Count of decrees in legal review states.", "count decrees in legal review states", ["status"]),
        _decree_metric("decrees_pending_rector_review_total", "Decrees Pending Rector Review Total", "Count of decrees pending rector review.", "count decrees pending rector review state", ["status"]),
        _decree_metric("decrees_approved_for_signing_total", "Decrees Approved For Signing Total", "Count of decrees approved for signing.", "count decrees approved for signing state", ["status"]),
        _decree_metric("decrees_signed_metadata_total", "Decrees Signed Metadata Total", "Count of decrees with signed metadata.", "count decrees where signed metadata exists", ["signed_by_user_id", "signed_at"]),
        _decree_metric("decrees_registered_total", "Decrees Registered Total", "Count of decree registry entries.", "count decree registry rows in tenant scope", ["decree_id", "registry_number", "registry_date"], limitations=["Registry metadata is contract-defined; live linkage is deferred."], unit=None),
        _decree_metric("decrees_archived_total", "Decrees Archived Total", "Count of archived decrees or archive records.", "count decrees with archive state or archive records", ["archived_at", "entity_type", "entity_id"], limitations=["Archive state is exposed read-only without retention workflow changes."]),
        _decree_metric("decree_average_legal_review_days", "Decree Average Legal Review Days", "Average decree legal review duration.", "average legal review exit timestamp minus legal review entry timestamp", ["created_at", "updated_at", "status", "SOURCE_FIELD_TO_VERIFY_IN_RUNTIME_SPEC"], unit="days", limitations=["Legal review transition timestamp remains a runtime verification placeholder."]),
        _decree_metric("decrees_linked_to_assignment_total", "Decrees Linked To Assignment Total", "Count of decrees linked directly to assignments.", "count decrees with linked_assignment_id", ["linked_assignment_id"]),
        _correspondence_metric("incoming_correspondence_total", "Incoming Correspondence Total", "Count of incoming correspondence items.", "count correspondence items where direction is incoming", ["direction"]),
        _correspondence_metric("incoming_waiting_route_total", "Incoming Waiting Route Total", "Count of incoming correspondence waiting for routing.", "count incoming correspondence waiting for route assignment", ["direction", "status", "id", "correspondence_id"], limitations=["Route-state semantics remain read-only contract metadata."]),
        _correspondence_metric("incoming_in_progress_total", "Incoming In Progress Total", "Count of incoming correspondence in active handling states.", "count incoming correspondence in active handling states", ["direction", "status"]),
        _correspondence_metric("incoming_responded_total", "Incoming Responded Total", "Count of incoming correspondence with terminal responded states.", "count incoming correspondence in responded or closed states", ["direction", "status"]),
        _correspondence_metric("outgoing_correspondence_total", "Outgoing Correspondence Total", "Count of outgoing correspondence items.", "count correspondence items where direction is outgoing", ["direction"]),
        _correspondence_metric("outgoing_under_review_total", "Outgoing Under Review Total", "Count of outgoing correspondence under review.", "count outgoing correspondence in review states", ["direction", "status"]),
        _correspondence_metric("outgoing_sent_metadata_total", "Outgoing Sent Metadata Total", "Count of outgoing correspondence with sent metadata.", "count outgoing correspondence where sent_at exists", ["direction", "sent_at"]),
        _correspondence_metric("outgoing_delivered_metadata_total", "Outgoing Delivered Metadata Total", "Count of outgoing correspondence with delivered metadata.", "count outgoing correspondence where delivered metadata exists", ["SOURCE_FIELD_TO_VERIFY_IN_RUNTIME_SPEC"], limitations=["Delivered metadata source field remains a runtime verification placeholder."]),
        _correspondence_metric("correspondence_average_route_time_days", "Correspondence Average Route Time Days", "Average time from receipt/creation to first route.", "average first route timestamp minus correspondence created_or_received timestamp", ["created_at", "received_at", "correspondence_id"], unit="days", limitations=["First-route timing is defined as a registry contract until aggregation is added."]),
        _sla_metric("sla_compliance_rate", "SLA Compliance Rate", "Share of SLA-subject assignments that remain compliant.", "compliant SLA assignments divided by all SLA-subject assignments", ["due_date", "completed_at", "status", "overdue_after_hours"], source_entities=["RectorAssignment", "RectorAssignmentSlaPolicy"], source_tables=["rector_assignments", "rector_assignment_sla_policies"], unit="ratio"),
        _sla_metric("overdue_aging_buckets", "Overdue Aging Buckets", "Bucketed overdue assignment counts.", "count overdue assignments in documented age buckets", ["due_date", "status"]),
        _sla_metric("escalations_by_level", "Escalations By Level", "Grouped open escalations by escalation level.", "group open escalations by escalation_level", ["escalation_level", "status"], source_entities=["RectorAssignmentEscalation"], source_tables=["rector_assignment_escalations"]),
        _sla_metric("unresolved_bottlenecks_total", "Unresolved Bottlenecks Total", "Count of documented unresolved bottlenecks across workflow sources.", "count items matching bottleneck rules across governance workflows", ["status", "due_date", "signed_at", "resolved_at"], source_module="cross_vertical_contract", source_entities=["RectorAssignment", "Document", "OrderDecree", "CorrespondenceItem", "RectorAssignmentEscalation"], source_tables=["rector_assignments", "doc_documents", "doc_order_decrees", "doc_correspondence_items", "rector_assignment_escalations"]),
        _sla_metric("departments_with_high_overdue_load", "Departments With High Overdue Load", "Count of departments above the overdue load visibility threshold.", "count departments exceeding configured overdue visibility threshold", ["responsible_unit_id", "due_date", "status"], permission=permissions.DEPARTMENT_READ),
        _sla_metric("assignments_overdue_more_than_7_days", "Assignments Overdue More Than 7 Days", "Count of assignments overdue by more than seven days.", "count active assignments where overdue duration is greater than seven days", ["due_date", "status"]),
        _sla_metric("documents_review_overdue_total", "Documents Review Overdue Total", "Count of documents whose review duration exceeded the documented threshold.", "count documents whose review duration exceeds runtime policy threshold", ["status", "created_at", "SOURCE_FIELD_TO_VERIFY_IN_RUNTIME_SPEC"], source_module="document_workflow_os", source_entities=["Document", "DocumentReview"], source_tables=["doc_documents", "doc_document_reviews"], limitations=["Review overdue threshold remains a documented runtime follow-up."]),
        _sla_metric("correspondence_response_overdue_total", "Correspondence Response Overdue Total", "Count of correspondence responses beyond the documented threshold.", "count correspondence items exceeding runtime response threshold", ["status", "received_at", "created_at", "SOURCE_FIELD_TO_VERIFY_IN_RUNTIME_SPEC"], source_module="document_workflow_os", source_entities=["CorrespondenceItem"], source_tables=["doc_correspondence_items"], limitations=["Response overdue threshold remains a documented runtime follow-up."]),
        _sla_metric("escalation_queue_total", "Escalation Queue Total", "Count of open escalation queue items.", "count escalation rows with open queue status", ["status"], source_entities=["RectorAssignmentEscalation"], source_tables=["rector_assignment_escalations"]),
        _sla_metric("manual_confirmation_pending_total", "Manual Confirmation Pending Total", "Count of records awaiting manual confirmation under documented rules.", "count records awaiting documented manual confirmation criteria", ["status", "SOURCE_FIELD_TO_VERIFY_IN_RUNTIME_SPEC"], source_module="cross_vertical_contract", source_entities=["RectorAssignmentEscalation", "OrderDecree", "CorrespondenceItem"], source_tables=["rector_assignment_escalations", "doc_order_decrees", "doc_correspondence_items"], limitations=["Manual confirmation criteria remain documented contracts until live aggregation is added."]),
        _strategy_metric("strategic_initiatives_total", "Strategic Initiatives Total", "Count of strategic initiatives in tenant scope.", "count initiatives in the future strategy source"),
        _strategy_metric("initiatives_linked_to_assignments_total", "Initiatives Linked To Assignments Total", "Count of strategic initiatives with explicit assignment linkage.", "count initiatives with explicit rector assignment linkage"),
        _strategy_metric("initiatives_linked_to_documents_total", "Initiatives Linked To Documents Total", "Count of strategic initiatives with explicit document linkage.", "count initiatives with explicit document linkage"),
        _strategy_metric("kpi_evidence_coverage_rate", "KPI Evidence Coverage Rate", "Share of KPI contracts with validated execution evidence.", "kpis with evidence linkage divided by total kpis"),
        _strategy_metric("kpi_stale_evidence_total", "KPI Stale Evidence Total", "Count of strategy KPI records whose evidence freshness exceeded threshold.", "count KPI evidence records exceeding freshness threshold"),
        _strategy_metric("kpi_without_execution_link_total", "KPI Without Execution Link Total", "Count of KPI contracts without assignment, document, decree, or correspondence linkage.", "count kpi contracts without execution linkage"),
        _strategy_metric("strategy_execution_bottlenecks_total", "Strategy Execution Bottlenecks Total", "Count of strategy bottlenecks backed by governance evidence.", "count strategy bottlenecks backed by linked workflow evidence"),
        _audit_metric("audit_events_total", "Audit Events Total", "Total audit event count across governance workflow sources.", "count audit events across rector assignments and documents", ["created_at", "event_type"], source_module="cross_vertical_audit", source_entities=["RectorAssignmentAuditEvent", "DocumentAuditEvent"], source_tables=["rector_assignment_audit_events", "doc_audit_events"]),
        _audit_metric("audit_events_24h_total", "Audit Events 24h Total", "Audit events observed in the last 24 hours.", "count audit events across rector assignments and documents within 24 hours", ["created_at"], source_module="cross_vertical_audit", source_entities=["RectorAssignmentAuditEvent", "DocumentAuditEvent"], source_tables=["rector_assignment_audit_events", "doc_audit_events"]),
        _audit_metric("status_history_completeness_rate", "Status History Completeness Rate", "Coverage rate for expected status history records.", "records with expected history coverage divided by records requiring history", ["assignment_id", "document_id", "created_at"], source_module="cross_vertical_history", source_entities=["RectorAssignmentStatusHistory", "DocumentStatusHistory"], source_tables=["rector_assignment_status_history", "doc_document_status_history"], unit="ratio"),
        _audit_metric("archived_records_total", "Archived Records Total", "Total archived records across governance workflow sources.", "count archived records across archive tables and archived rector assignments", ["entity_type", "entity_id", "archived_at", "is_archived"], source_module="cross_vertical_archive", source_entities=["ArchiveRecord", "RectorAssignment"], source_tables=["doc_archive_records", "rector_assignments"]),
        _audit_metric("hard_delete_events_total_expected_zero", "Hard Delete Events Total Expected Zero", "Expected-zero hard delete event contract.", "count hard delete audit events if an explicit source exists", ["SOURCE_FIELD_TO_VERIFY_IN_RUNTIME_SPEC"], source_module="future_audit_contract", source_entities=["SOURCE_ENTITY_TO_VERIFY_IN_RUNTIME_SPEC"], source_tables=["SOURCE_TABLE_TO_VERIFY_IN_RUNTIME_SPEC"], limitations=["Hard delete event source is not implemented in A-033.1-RUNTIME."]),
        _audit_metric("dashboard_guard_failures_total", "Dashboard Guard Failures Total", "Count of future runtime guard failures.", "count guard failures once executive runtime guard logging exists", ["fake_metrics", "data_source", "SOURCE_FIELD_TO_VERIFY_IN_RUNTIME_SPEC"], source_module="future_executive_runtime", source_entities=["SOURCE_ENTITY_TO_VERIFY_IN_RUNTIME_SPEC"], source_tables=["SOURCE_TABLE_TO_VERIFY_IN_RUNTIME_SPEC"], limitations=["Guard failure logging is deferred until a later runtime slice."]),
        _audit_metric("permission_denied_events_total", "Permission Denied Events Total", "Count of permission denied events for control tower routes.", "count denied access events once route audit logging exists", ["SOURCE_FIELD_TO_VERIFY_IN_RUNTIME_SPEC"], source_module="future_platform_audit", source_entities=["SOURCE_ENTITY_TO_VERIFY_IN_RUNTIME_SPEC"], source_tables=["SOURCE_TABLE_TO_VERIFY_IN_RUNTIME_SPEC"], limitations=["Route-specific denial logs are deferred until later runtime slices."]),
        _audit_metric("cross_tenant_access_blocked_total", "Cross Tenant Access Blocked Total", "Count of blocked cross-tenant access attempts.", "count blocked cross-tenant access events for the control tower", ["SOURCE_FIELD_TO_VERIFY_IN_RUNTIME_SPEC"], source_module="future_platform_audit", source_entities=["SOURCE_ENTITY_TO_VERIFY_IN_RUNTIME_SPEC"], source_tables=["SOURCE_TABLE_TO_VERIFY_IN_RUNTIME_SPEC"], limitations=["Cross-tenant blocked event logging is deferred until later runtime slices."]),
        _audit_metric("incomplete_data_metric_count", "Incomplete Data Metric Count", "Count of registry metrics currently marked incomplete.", "count registry metrics where incomplete_data is true", ["metric_id", "incomplete_data"], source_module="executive_control_tower_runtime_contract", source_entities=["MetricRegistryRuntimeView"], source_tables=["SOURCE_TABLE_TO_VERIFY_IN_RUNTIME_SPEC"], permission=permissions.METRIC_REGISTRY_READ),
        _audit_metric("stale_metric_count", "Stale Metric Count", "Count of registry metrics exceeding their staleness threshold.", "count registry metrics whose freshness threshold has expired", ["metric_id", "generated_at", "freshness_timestamp_field"], source_module="executive_control_tower_runtime_contract", source_entities=["MetricRegistryRuntimeView"], source_tables=["SOURCE_TABLE_TO_VERIFY_IN_RUNTIME_SPEC"], permission=permissions.METRIC_REGISTRY_READ),
        _department_metric("department_active_assignments_total", "Department Active Assignments Total", "Count of active assignments by department.", "count active assignments grouped by responsible unit", ["responsible_unit_id", "status"]),
        _department_metric("department_overdue_assignments_total", "Department Overdue Assignments Total", "Count of overdue assignments by department.", "count overdue assignments grouped by responsible unit", ["responsible_unit_id", "due_date", "status"]),
        _department_metric("department_documents_in_review_total", "Department Documents In Review Total", "Count of documents under review by source department.", "count documents under review grouped by source_department_id", ["source_department_id", "status"], source_module="document_workflow_os", source_entities=["Document"], source_tables=["doc_documents"]),
        _department_metric("department_correspondence_pending_total", "Department Correspondence Pending Total", "Count of pending correspondence mapped to a department.", "count pending correspondence mapped through explicit department linkage rules", ["status", "linked_document_id", "SOURCE_FIELD_TO_VERIFY_IN_RUNTIME_SPEC"], source_module="document_workflow_os", source_entities=["CorrespondenceItem", "Document"], source_tables=["doc_correspondence_items", "doc_documents"], limitations=["Department correspondence linkage remains a runtime verification placeholder."]),
        _department_metric("department_sla_compliance_rate", "Department SLA Compliance Rate", "Department-level SLA compliance rate.", "compliant SLA assignments divided by SLA-subject assignments per department", ["responsible_unit_id", "due_date", "completed_at", "status"], unit="ratio"),
        _department_metric("department_execution_bottlenecks_total", "Department Execution Bottlenecks Total", "Count of department-attributed bottlenecks across workflow sources.", "count department-attributed records matching documented bottleneck rules", ["responsible_unit_id", "source_department_id", "status", "due_date"], source_module="cross_vertical_contract", source_entities=["RectorAssignment", "Document", "CorrespondenceItem", "OrderDecree"], source_tables=["rector_assignments", "doc_documents", "doc_correspondence_items", "doc_order_decrees"]),
        _department_metric("department_audit_activity_total", "Department Audit Activity Total", "Count of department-attributed audit activity.", "count audit events attributable through linked ownership mappings", ["payload_json", "assignment_id", "entity_id", "SOURCE_FIELD_TO_VERIFY_IN_RUNTIME_SPEC"], source_module="cross_vertical_audit", source_entities=["RectorAssignmentAuditEvent", "DocumentAuditEvent"], source_tables=["rector_assignment_audit_events", "doc_audit_events"], limitations=["Department attribution remains a documented runtime follow-up."]),
    ]
    return tuple(metrics)


_METRIC_DEFINITIONS = _build_metric_definitions()
_METRIC_LOOKUP = {metric.metric_id: metric for metric in _METRIC_DEFINITIONS}
_GROUP_MEMBERSHIP: dict[str, tuple[str, ...]] = {
    EXECUTIVE_OVERVIEW: (
        "active_assignments_total",
        "overdue_assignments_total",
        "documents_in_workflow_total",
        "decrees_pending_signed_metadata_total",
        "correspondence_waiting_response_total",
        "sla_compliance_rate",
        "escalations_open_total",
        "audit_events_24h_total",
        "executive_attention_required_total",
    ),
    ASSIGNMENT_EXECUTION: (
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
    ),
    DOCUMENT_WORKFLOW: (
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
    ),
    DECREE_WORKFLOW: (
        "decrees_total",
        "decrees_in_legal_review_total",
        "decrees_pending_rector_review_total",
        "decrees_approved_for_signing_total",
        "decrees_signed_metadata_total",
        "decrees_registered_total",
        "decrees_archived_total",
        "decrees_pending_signed_metadata_total",
        "decree_average_legal_review_days",
        "decrees_linked_to_assignment_total",
    ),
    CORRESPONDENCE_WORKFLOW: (
        "incoming_correspondence_total",
        "incoming_waiting_route_total",
        "incoming_in_progress_total",
        "incoming_responded_total",
        "outgoing_correspondence_total",
        "outgoing_under_review_total",
        "outgoing_sent_metadata_total",
        "outgoing_delivered_metadata_total",
        "correspondence_average_route_time_days",
        "correspondence_waiting_response_total",
    ),
    SLA_RISK_BOTTLENECK: (
        "sla_compliance_rate",
        "overdue_aging_buckets",
        "escalations_by_level",
        "unresolved_bottlenecks_total",
        "departments_with_high_overdue_load",
        "assignments_overdue_more_than_7_days",
        "documents_review_overdue_total",
        "correspondence_response_overdue_total",
        "escalation_queue_total",
        "manual_confirmation_pending_total",
    ),
    STRATEGY_KPI: (
        "strategic_initiatives_total",
        "initiatives_linked_to_assignments_total",
        "initiatives_linked_to_documents_total",
        "kpi_evidence_coverage_rate",
        "kpi_stale_evidence_total",
        "kpi_without_execution_link_total",
        "strategy_execution_bottlenecks_total",
    ),
    AUDIT_COMPLIANCE: (
        "audit_events_total",
        "audit_events_24h_total",
        "status_history_completeness_rate",
        "archived_records_total",
        "hard_delete_events_total_expected_zero",
        "dashboard_guard_failures_total",
        "permission_denied_events_total",
        "cross_tenant_access_blocked_total",
        "incomplete_data_metric_count",
        "stale_metric_count",
    ),
    DEPARTMENT_PERFORMANCE: (
        "department_active_assignments_total",
        "department_overdue_assignments_total",
        "department_documents_in_review_total",
        "department_correspondence_pending_total",
        "department_sla_compliance_rate",
        "department_execution_bottlenecks_total",
        "department_audit_activity_total",
    ),
}


_DECREE_ONLY_METRICS = (
    _decree_metric("decrees_pending_signed_metadata_total", "Decrees Pending Signed Metadata Total", "Count of decrees awaiting signed metadata.", "count decrees in signing-ready states with null signed metadata", ["status", "signed_by_user_id", "signed_at"]),
)


if "decrees_pending_signed_metadata_total" not in _METRIC_LOOKUP:
    metric = _DECREE_ONLY_METRICS[0]
    _METRIC_LOOKUP[metric.metric_id] = metric
    _METRIC_DEFINITIONS = _METRIC_DEFINITIONS + (metric,)


def _clone_metric(metric: ExecutiveControlTowerMetric, *, group_id: str | None = None) -> ExecutiveControlTowerMetric:
    cloned = metric.model_copy(deep=True)
    if group_id is not None:
        cloned.metric_group = group_id
    return cloned


def get_metric_registry_definitions() -> list[ExecutiveControlTowerMetric]:
    return [_clone_metric(metric) for metric in _METRIC_DEFINITIONS]


def get_metric_by_id(metric_id: str) -> ExecutiveControlTowerMetric | None:
    metric = _METRIC_LOOKUP.get(str(metric_id).strip())
    if metric is None:
        return None
    return _clone_metric(metric)


def get_metric_group(group_id: str) -> ExecutiveControlTowerMetricGroup | None:
    normalized = str(group_id).strip()
    if normalized not in GROUP_METADATA or normalized not in _GROUP_MEMBERSHIP:
        return None
    label, description = GROUP_METADATA[normalized]
    metric_ids = _GROUP_MEMBERSHIP[normalized]
    metrics = [_clone_metric(_METRIC_LOOKUP[metric_id], group_id=normalized) for metric_id in metric_ids]
    return ExecutiveControlTowerMetricGroup(
        group_id=normalized,
        label=label,
        description=description,
        metrics=metrics,
        fake_metrics=FAKE_METRICS,
        data_source=DATA_SOURCE,
        incomplete_data=any(metric.incomplete_data for metric in metrics),
        limitations=list(_FOUNDATION_LIMITATIONS),
    )


def list_metric_groups() -> list[ExecutiveControlTowerMetricGroup]:
    return [group for group_id in GROUP_METADATA if (group := get_metric_group(group_id)) is not None]


def validate_metric_registry() -> dict[str, Any]:
    errors: list[str] = []
    definitions = get_metric_registry_definitions()
    metric_ids = [metric.metric_id for metric in definitions]
    if len(metric_ids) != len(set(metric_ids)):
        errors.append("metric_ids must be unique")
    for metric in definitions:
        if metric.fake_metrics is not FAKE_METRICS:
            errors.append(f"{metric.metric_id}: fake_metrics must remain false")
        if metric.data_source != DATA_SOURCE:
            errors.append(f"{metric.metric_id}: data_source must remain computed_from_governance_workflows")
        if not metric.permission_required:
            errors.append(f"{metric.metric_id}: permission_required missing")
        if not metric.source_module or not metric.source_tables or not metric.source_fields:
            errors.append(f"{metric.metric_id}: source mapping incomplete")
        if not metric.limitations:
            errors.append(f"{metric.metric_id}: limitations missing")
        if metric.runtime_status not in {"FOUNDATION_CONTRACT_ONLY", "DEFERRED_UNTIL_STRATEGY_MODULE"}:
            errors.append(f"{metric.metric_id}: runtime_status must remain read-only foundation scoped")
        if metric.metric_id in _GROUP_MEMBERSHIP[STRATEGY_KPI]:
            if metric.readiness != "FUTURE_CONTRACT" or metric.runtime_status != "DEFERRED_UNTIL_STRATEGY_MODULE" or not metric.incomplete_data:
                errors.append(f"{metric.metric_id}: strategy metric contract is not marked deferred")
    for group_id, members in _GROUP_MEMBERSHIP.items():
        for member in members:
            if member not in _METRIC_LOOKUP:
                errors.append(f"{group_id}: missing registry definition for {member}")
    return {
        "valid": not errors,
        "errors": errors,
        "total_metrics": len(definitions),
        "total_groups": len(GROUP_METADATA),
    }


def get_registry_summary() -> dict[str, Any]:
    validation = validate_metric_registry()
    return {
        "total_metrics": validation["total_metrics"],
        "total_groups": validation["total_groups"],
        "group_ids": list(GROUP_METADATA.keys()),
        "valid": validation["valid"],
        "errors": list(validation["errors"]),
    }


__all__ = [
    "DATA_SOURCE",
    "FAKE_METRICS",
    "EXECUTIVE_OVERVIEW",
    "ASSIGNMENT_EXECUTION",
    "DOCUMENT_WORKFLOW",
    "DECREE_WORKFLOW",
    "CORRESPONDENCE_WORKFLOW",
    "SLA_RISK_BOTTLENECK",
    "STRATEGY_KPI",
    "AUDIT_COMPLIANCE",
    "DEPARTMENT_PERFORMANCE",
    "GROUP_METADATA",
    "get_metric_registry_definitions",
    "get_metric_by_id",
    "get_metric_group",
    "list_metric_groups",
    "validate_metric_registry",
    "get_registry_summary",
]