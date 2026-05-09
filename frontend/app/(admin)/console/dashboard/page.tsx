"use client";

import { useMemo } from "react";
import { Button } from "@/shared/ui/button";
import { EmptyState } from "@/shared/ui/empty-state";
import { ErrorState } from "@/shared/ui/error-state";
import { PageHeader } from "@/shared/ui/page-header";
import { Skeleton } from "@/shared/ui/skeleton";
import { AccessDenied } from "@/shared/ui/permission-gate";
import { formatDate, formatRelative } from "@/shared/utils/format";
import { PERMISSIONS } from "@/shared/config/permissions";
import { LayoutDashboard, RefreshCw, CalendarDays, BarChart3, FileText, GraduationCap, BookOpen, ClipboardCheck } from "lucide-react";
import { KpiCard } from "@/modules/platform/kpi/kpi-card";
import { Wave1KpiBar } from "@/modules/platform/kpi/wave1-kpi-bar";
import { useRectorDashboard, useRectorKpiDrilldown } from "@/modules/platform/kpi/use-dashboard";
import { AutomationOverviewWidget } from "@/modules/platform/automation/automation-overview-widget";
import Link from "next/link";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { useAdminAuth } from "@/shared/auth/context";
import { useLanguage } from "@/app/components/LanguageProvider";

type ExecutiveKpiSectionConfig = {
  testId: string;
  title: string;
  description: string;
  metricKeys: string[];
  labels: Record<string, string>;
  advisoryTitle?: string;
  advisoryText?: string;
};

type GovernanceReportSectionConfig = {
  sectionId: string;
  title: string;
  description: string;
  metricKeys: string[];
  sourceDomains: string[];
  dataQualityNote: string;
};

type DashboardCardSnapshot = {
  metric_key: string;
  title: string;
  value: number;
  trend_7d: unknown[];
  metadata_json: Record<string, unknown>;
};

type RiskHeatmapDomainConfig = {
  domainId: string;
  title: string;
  description: string;
  metricKeys: string[];
  criticalMetricKeys: string[];
  riskMetricKeys: string[];
  watchMetricKeys: string[];
  reviewMetricKeys: string[];
  sourceDomains: string[];
  dataQualityNote: string;
  optional?: boolean;
};

type GovernanceAlertDomainConfig = {
  domainId: string;
  domainTitle: string;
  title: string;
  description: string;
  metricKeys: string[];
  criticalMetricKeys: string[];
  highMetricKeys: string[];
  mediumMetricKeys: string[];
  reviewMetricKeys: string[];
  watchMetricKeys: string[];
  resolvedMetricKeys?: string[];
  sourceDomains: string[];
  recommendedHumanAction: string;
  dataQualityNote: string;
  optional?: boolean;
};

type GovernanceReviewAlert = {
  alertId: string;
  domainId: string;
  domainTitle: string;
  title: string;
  severity: "low" | "medium" | "high" | "critical" | "unavailable";
  reviewStatus: "review_required" | "watch" | "evidence_only" | "unavailable" | "resolved";
  evidenceSummary: string;
  sourceMetrics: string[];
  sourceDomains: string[];
  recommendedHumanAction: string;
  dataQualityNote: string;
  tenantScoped: true;
  readonly: true;
};

type KpiEvidenceSource = {
  metricKey: string;
  label: string;
  valueLabel: string;
  sourceDomain: string;
  interpretation: string;
  available: boolean;
};

type KpiEvidenceDrilldown = {
  drilldownId: string;
  title: string;
  domainId: string;
  domainTitle: string;
  sourceMetrics: string[];
  sourceDomains: string[];
  evidenceSummary: string;
  explanation: string;
  riskLevel: "low" | "medium" | "high" | "critical" | "unavailable";
  reviewRequired: boolean;
  dataQualityNote: string;
  readonly: true;
  tenantScoped: true;
  evidenceSources: KpiEvidenceSource[];
};

type KpiEvidenceDrilldownConfig = {
  domainId: string;
  domainTitle: string;
  title: string;
  metricKeys: string[];
  criticalMetricKeys: string[];
  highMetricKeys: string[];
  mediumMetricKeys: string[];
  reviewMetricKeys: string[];
  sourceDomains: string[];
  explanation: string;
  dataQualityNote: string;
  optional?: boolean;
};

type GovernanceCommandCenterSection = {
  sectionId: string;
  title: string;
};

const EXECUTIVE_KPI_SECTIONS: ExecutiveKpiSectionConfig[] = [
  {
    testId: "wave3-finance-kpi-section",
    title: "Finance and Operations Health",
    description: "Budget, procurement, and inventory indicators are displayed as evidence for rector-level governance review.",
    metricKeys: [
      "budget_overrun_risk_count",
      "budget_review_actions_count",
      "active_finance_risk_signals_count",
      "finance_operations_actionability_count",
      "asset_conversion_gap_count",
      "inventory_low_stock_items_count",
      "critical_supply_risk_count",
      "supply_risk_actions_count",
    ],
    labels: {
      budget_overrun_risk_count: "Budget Overrun Risk",
      budget_review_actions_count: "Budget Review Actions",
      active_finance_risk_signals_count: "Finance Risk Signals",
      finance_operations_actionability_count: "Finance Actionability",
      asset_conversion_gap_count: "Asset Conversion Gap",
      inventory_low_stock_items_count: "Low Stock Items",
      critical_supply_risk_count: "Critical Supply Risk",
      supply_risk_actions_count: "Supply Risk Actions",
    },
  },
  {
    testId: "wave4-academic-integrity-kpi-section",
    title: "Academic Integrity and Governance",
    description: "Integrity, exam governance, thesis review, and ethics compliance remain read-only command inputs.",
    metricKeys: [
      "academic_integrity_risk_count",
      "academic_integrity_review_cases_count",
      "academic_integrity_high_risk_count",
      "academic_integrity_cases_pending_review",
      "exam_proctoring_violations_count",
      "exam_integrity_reviews_count",
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
      "integrity_cases_resolved_count",
      "integrity_cases_evidence_requested_count",
      "integrity_case_resolution_sla_risk_count",
    ],
    labels: {
      academic_integrity_risk_count: "Integrity Risk",
      academic_integrity_review_cases_count: "Review Cases",
      academic_integrity_high_risk_count: "High Risk",
      academic_integrity_cases_pending_review: "Pending Review",
      exam_proctoring_violations_count: "Proctoring Violations",
      exam_integrity_reviews_count: "Exam Reviews",
      exam_integrity_high_risk_count: "Exam High Risk",
      exam_integrity_requires_approval_count: "Exam Approval Needed",
      thesis_governance_risk_count: "Thesis Risk",
      thesis_supervisor_assignment_needed_count: "Supervisor Needed",
      thesis_review_delayed_count: "Review Delayed",
      thesis_governance_requires_approval_count: "Thesis Approval Needed",
      research_ethics_review_cases_count: "Ethics Review Cases",
      research_ethics_high_risk_count: "Ethics High Risk",
      research_ethics_missing_documents_count: "Missing Documents",
      research_ethics_requires_approval_count: "Ethics Approval Needed",
      integrity_cases_open_count: "Cases Open",
      integrity_cases_escalated_count: "Cases Escalated",
      integrity_cases_resolved_count: "Cases Resolved",
      integrity_cases_evidence_requested_count: "Evidence Requested",
      integrity_case_resolution_sla_risk_count: "SLA Risk",
    },
  },
  {
    testId: "a0185-campus-operations-kpi-section",
    title: "Campus Operations and Security",
    description: "Campus activity and security posture are surfaced for manual rector oversight and escalation decisions.",
    metricKeys: [
      "scheduling_conflicts_count",
      "room_conflict_count",
      "access_denied_count",
      "unauthorized_attempts_count",
      "active_access_cards_count",
      "suspended_access_cards_count",
      "security_access_anomaly_count",
      "events_published_count",
      "events_started_count",
      "events_completed_count",
      "events_cancelled_count",
      "events_registration_full_count",
      "visitor_requests_pending_count",
      "visitors_checked_in_count",
      "visitor_unauthorized_attempts_count",
      "visitor_visits_completed_count",
      "visitor_visits_cancelled_count",
      "security_incidents_open_count",
      "security_incidents_escalated_count",
      "security_incidents_resolved_count",
      "security_incident_review_required_count",
      "security_high_risk_incidents_count",
    ],
    labels: {
      scheduling_conflicts_count: "Scheduling Conflicts",
      room_conflict_count: "Room Conflicts",
      access_denied_count: "Access Denied",
      unauthorized_attempts_count: "Unauthorized Attempts",
      active_access_cards_count: "Active Access Cards",
      suspended_access_cards_count: "Suspended Access Cards",
      security_access_anomaly_count: "Security Anomalies",
      events_published_count: "Events Published",
      events_started_count: "Events Started",
      events_completed_count: "Events Completed",
      events_cancelled_count: "Events Cancelled",
      events_registration_full_count: "Registration Full",
      visitor_requests_pending_count: "Visitor Requests Pending",
      visitors_checked_in_count: "Visitors Checked-In",
      visitor_unauthorized_attempts_count: "Visitor Unauthorized Attempts",
      visitor_visits_completed_count: "Visitor Visits Completed",
      visitor_visits_cancelled_count: "Visitor Visits Cancelled",
      security_incidents_open_count: "Security Incidents Open",
      security_incidents_escalated_count: "Security Incidents Escalated",
      security_incidents_resolved_count: "Security Incidents Resolved",
      security_incident_review_required_count: "Security Review Required",
      security_high_risk_incidents_count: "Security High-Risk Incidents",
    },
  },
  {
    testId: "a0206-room-allocation-intelligence-section",
    title: "Scheduling and Room Allocation Intelligence",
    description: "Capacity and allocation indicators are decision-support only and never auto-execute scheduling changes.",
    advisoryTitle: "Room Allocation / Scheduling Intelligence",
    advisoryText:
      "Recommendation and Review required insights are evidence-only. Evidence is provided for human approval when risk exists. No automatic assignment. No auto-apply.",
    metricKeys: [
      "room_allocation_recommendations_count",
      "room_allocation_review_required_count",
      "room_allocation_no_viable_candidate_count",
      "room_allocation_candidate_evaluated_count",
      "room_capacity_mismatch_count",
      "room_equipment_mismatch_count",
      "room_computer_shortage_count",
      "room_type_mismatch_count",
      "scheduling_conflicts_count",
      "room_conflict_count",
      "capacity_risk_sections_count",
    ],
    labels: {
      room_allocation_recommendations_count: "Recommendation",
      room_allocation_review_required_count: "Review required",
      room_allocation_no_viable_candidate_count: "No viable candidate",
      room_allocation_candidate_evaluated_count: "Candidate evaluated",
      room_capacity_mismatch_count: "Capacity mismatch",
      room_equipment_mismatch_count: "Equipment mismatch",
      room_computer_shortage_count: "Computer shortage",
      room_type_mismatch_count: "Room type mismatch",
      scheduling_conflicts_count: "Scheduling conflicts",
      room_conflict_count: "Room conflicts",
      capacity_risk_sections_count: "Capacity-risk sections",
    },
  },
  {
    testId: "a0225-timetable-change-kpi-section",
    title: "Human-Approved Timetable Workflow",
    description: "Proposal, simulation, and approval queue indicators are shown as read-only evidence for human timetable decisions.",
    advisoryTitle: "Timetable Change KPI / Dashboard",
    advisoryText:
      "Read-only, tenant-scoped, evidence-backed workflow visibility for rector governance. No automatic timetable mutation. No auto-apply.",
    metricKeys: [
      "timetable_change_proposals_count",
      "timetable_change_pending_review_count",
      "timetable_change_approved_count",
      "timetable_change_rejected_count",
      "timetable_change_revision_requested_count",
      "timetable_simulations_count",
      "timetable_simulations_review_required_count",
      "timetable_simulation_conflicts_created_count",
      "timetable_simulation_conflicts_resolved_count",
      "timetable_approval_queue_count",
      "timetable_approval_pending_count",
      "timetable_approval_approved_count",
      "timetable_approval_rejected_count",
      "timetable_approval_revision_requested_count",
      "timetable_approval_high_risk_count",
    ],
    labels: {
      timetable_change_proposals_count: "Proposals",
      timetable_change_pending_review_count: "Pending review",
      timetable_change_approved_count: "Approved",
      timetable_change_rejected_count: "Declined",
      timetable_change_revision_requested_count: "Revision requested",
      timetable_simulations_count: "Simulations",
      timetable_simulations_review_required_count: "Simulation review required",
      timetable_simulation_conflicts_created_count: "Simulation conflicts created",
      timetable_simulation_conflicts_resolved_count: "Simulation conflicts resolved",
      timetable_approval_queue_count: "Approval queue",
      timetable_approval_pending_count: "Approval pending",
      timetable_approval_approved_count: "Approval approved",
      timetable_approval_rejected_count: "Approval declined",
      timetable_approval_revision_requested_count: "Approval revision requested",
      timetable_approval_high_risk_count: "Approval high-risk",
    },
  },
  {
    testId: "a017-consolidation-kpi-section",
    title: "Cross-Wave Governance Snapshot",
    description: "Financial, billing, integrity, and ethics signals are consolidated for executive cross-domain review.",
    metricKeys: [
      "budget_overrun_risk_count",
      "budget_overrun_amount_at_risk",
      "budget_health_score",
      "total_active_subscriptions",
      "delinquency_cases_active",
      "overdue_amount_at_risk",
      "delinquency_recovery_rate",
      "academic_integrity_review_cases_count",
      "exam_proctoring_violations_count",
      "exam_integrity_reviews_count",
      "exam_integrity_requires_approval_count",
      "research_ethics_review_cases_count",
      "research_ethics_requires_approval_count",
    ],
    labels: {
      budget_overrun_risk_count: "Budget Overrun Risk",
      budget_overrun_amount_at_risk: "Budget Amount At Risk",
      budget_health_score: "Budget Health Score",
      total_active_subscriptions: "Active Subscriptions",
      delinquency_cases_active: "Active Delinquency Cases",
      overdue_amount_at_risk: "Overdue Amount At Risk",
      delinquency_recovery_rate: "Delinquency Recovery Rate",
      academic_integrity_review_cases_count: "Integrity Review Cases",
      exam_proctoring_violations_count: "Proctoring Violations",
      exam_integrity_reviews_count: "Exam Integrity Reviews",
      exam_integrity_requires_approval_count: "Exam Approval Needed",
      research_ethics_review_cases_count: "Research Ethics Cases",
      research_ethics_requires_approval_count: "Ethics Approval Needed",
    },
  },
];

const GOVERNANCE_REPORT_SECTIONS: GovernanceReportSectionConfig[] = [
  {
    sectionId: "institution-governance-summary",
    title: "Institution Governance Summary",
    description: "Executive roll-up of institution-wide evidence and readiness indicators.",
    metricKeys: [
      "total_students",
      "total_enrollments",
      "total_grades_submitted",
      "high_risk_students_count",
      "critical_risk_students_count",
      "budget_overrun_risk_count",
    ],
    sourceDomains: ["Academic", "Student", "Finance"],
    dataQualityNote: "Uses existing rector snapshot metrics only. Missing metrics remain Not available.",
  },
  {
    sectionId: "academic-governance",
    title: "Academic Governance",
    description: "Integrity, thesis, exam, and ethics evidence for executive review.",
    metricKeys: [
      "academic_integrity_review_cases_count",
      "academic_integrity_high_risk_count",
      "exam_proctoring_violations_count",
      "exam_integrity_reviews_count",
      "thesis_governance_risk_count",
      "research_ethics_review_cases_count",
    ],
    sourceDomains: ["Academic Integrity", "Thesis", "Research Ethics"],
    dataQualityNote: "Read-only governance summary derived from current dashboard evidence.",
  },
  {
    sectionId: "student-risk-intervention",
    title: "Student / Risk / Intervention Summary",
    description: "Student-risk signals and intervention activity, if present in the current tenant snapshot.",
    metricKeys: [
      "high_risk_students_count",
      "critical_risk_students_count",
      "intervention_auto_created_count",
      "intervention_resolution_rate",
      "sweep_coverage_rate",
      "composite_risk_average",
    ],
    sourceDomains: ["Student Risk", "Interventions"],
    dataQualityNote: "No fabricated student or intervention totals are generated here.",
  },
  {
    sectionId: "finance-procurement-assets",
    title: "Finance / Procurement / Asset Governance",
    description: "Budget, procurement, delivery, and asset conversion evidence for ministry-ready reporting.",
    metricKeys: [
      "budget_overrun_risk_count",
      "budget_overrun_amount_at_risk",
      "procurement_requests_pending_approval",
      "procurement_approval_automation_count",
      "asset_conversion_gap_count",
      "finance_operations_health_score",
      "procurement_health_score",
    ],
    sourceDomains: ["Finance", "Procurement", "Assets"],
    dataQualityNote: "Approval and health indicators are evidence-backed and require human review.",
  },
  {
    sectionId: "campus-scheduling-room-allocation",
    title: "Campus / Room Allocation / Scheduling Governance",
    description: "Scheduling and room-allocation evidence carried forward from the A-020 command center.",
    metricKeys: [
      "scheduling_conflicts_count",
      "room_conflict_count",
      "room_allocation_recommendations_count",
      "room_allocation_review_required_count",
      "room_allocation_no_viable_candidate_count",
      "capacity_risk_sections_count",
      "room_capacity_mismatch_count",
    ],
    sourceDomains: ["Scheduling", "Room Allocation"],
    dataQualityNote: "Advisory only; no automatic assignment or schedule mutation.",
  },
  {
    sectionId: "security-visitor-operations",
    title: "Security / Visitor Operations Governance",
    description: "Security and visitor oversight indicators surfaced for manual review only.",
    metricKeys: [
      "access_denied_count",
      "unauthorized_attempts_count",
      "security_incidents_open_count",
      "security_incidents_escalated_count",
      "security_incident_review_required_count",
      "security_high_risk_incidents_count",
      "visitor_requests_pending_count",
    ],
    sourceDomains: ["Security Operations", "Visitor Management"],
    dataQualityNote: "No lockout, ban, or other destructive security action is triggered from this shell.",
  },
  {
    sectionId: "research-accreditation-quality",
    title: "Research / Accreditation / Quality Governance",
    description: "Research ethics and related quality evidence; accreditation fields remain available when supported by the tenant snapshot.",
    metricKeys: [
      "research_ethics_review_cases_count",
      "research_ethics_requires_approval_count",
      "thesis_governance_risk_count",
      "thesis_governance_requires_approval_count",
      "academic_integrity_cases_resolved_count",
    ],
    sourceDomains: ["Research Ethics", "Quality", "Accreditation"],
    dataQualityNote: "Accreditation-ready packaging is report-oriented only; no external certification occurs here.",
  },
  {
    sectionId: "brain-review-required",
    title: "Brain / Review Required Summary",
    description: "Review-required and approval-needed evidence aggregated into a rector-readable summary.",
    metricKeys: [
      "academic_integrity_cases_pending_review",
      "exam_integrity_requires_approval_count",
      "thesis_governance_requires_approval_count",
      "research_ethics_requires_approval_count",
      "room_allocation_review_required_count",
      "security_incident_review_required_count",
      "budget_review_actions_count",
    ],
    sourceDomains: ["Brain Core", "Review Queue"],
    dataQualityNote: "Review-required signals are surfaced as evidence, not acted on automatically.",
  },
  {
    sectionId: "evidence-gate-readiness",
    title: "Evidence / Gate Readiness Summary",
    description: "Operational evidence and readiness markers used to explain whether the report is complete enough for human review.",
    metricKeys: [
      "analytics_events_ingested_total",
      "analytics_kpi_reads_total",
      "analytics_reads_total",
      "analytics_kpi_reads_share_pct",
      "total_failed_jobs",
      "total_failed_notifications",
    ],
    sourceDomains: ["Platform Analytics", "Operations"],
    dataQualityNote: "This shell is export-ready in contract only; it does not submit externally.",
  },
  {
    sectionId: "known-conditions-data-quality",
    title: "Known Conditions / Data Quality Notes",
    description: "Contextual notes that explain when report values are limited, missing, or intentionally suppressed.",
    metricKeys: [],
    sourceDomains: ["Data Quality", "Environment"],
    dataQualityNote: "Missing metrics show as Not available. Suppressed or unavailable evidence is preserved rather than fabricated.",
  },
];

const CROSS_DOMAIN_RISK_HEATMAP: RiskHeatmapDomainConfig[] = [
  {
    domainId: "academic-governance",
    title: "Academic Governance",
    description: "Integrity, exam governance, thesis, and ethics risk signals.",
    metricKeys: [
      "academic_integrity_high_risk_count",
      "academic_integrity_cases_pending_review",
      "exam_integrity_high_risk_count",
      "exam_integrity_requires_approval_count",
      "thesis_governance_risk_count",
      "thesis_governance_requires_approval_count",
      "research_ethics_high_risk_count",
      "research_ethics_requires_approval_count",
    ],
    criticalMetricKeys: ["academic_integrity_high_risk_count", "exam_integrity_high_risk_count", "research_ethics_high_risk_count"],
    riskMetricKeys: ["thesis_governance_risk_count", "academic_integrity_review_cases_count", "exam_integrity_reviews_count"],
    watchMetricKeys: ["integrity_case_resolution_sla_risk_count", "research_ethics_review_cases_count"],
    reviewMetricKeys: ["academic_integrity_cases_pending_review", "exam_integrity_requires_approval_count", "thesis_governance_requires_approval_count", "research_ethics_requires_approval_count"],
    sourceDomains: ["Academic Integrity", "Exam Governance", "Thesis", "Research Ethics"],
    dataQualityNote: "Uses current tenant KPI evidence only.",
  },
  {
    domainId: "finance-procurement-assets",
    title: "Finance / Procurement / Assets",
    description: "Budget, procurement, delinquency, and asset-conversion pressure.",
    metricKeys: [
      "budget_overrun_risk_count",
      "active_finance_risk_signals_count",
      "delinquency_cases_active",
      "asset_conversion_gap_count",
      "procurement_requests_pending_approval",
      "budget_review_actions_count",
    ],
    criticalMetricKeys: ["budget_overrun_risk_count", "delinquency_cases_active"],
    riskMetricKeys: ["active_finance_risk_signals_count", "asset_conversion_gap_count"],
    watchMetricKeys: ["procurement_requests_pending_approval"],
    reviewMetricKeys: ["budget_review_actions_count"],
    sourceDomains: ["Finance", "Procurement", "Assets"],
    dataQualityNote: "Evidence-backed only; approvals remain human-managed.",
  },
  {
    domainId: "campus-operations",
    title: "Campus Operations",
    description: "Operational pressure from scheduling, events, and capacity risk.",
    metricKeys: [
      "scheduling_conflicts_count",
      "room_conflict_count",
      "capacity_risk_sections_count",
      "events_cancelled_count",
      "events_registration_full_count",
    ],
    criticalMetricKeys: ["capacity_risk_sections_count"],
    riskMetricKeys: ["scheduling_conflicts_count", "room_conflict_count"],
    watchMetricKeys: ["events_cancelled_count", "events_registration_full_count"],
    reviewMetricKeys: [],
    sourceDomains: ["Scheduling", "Events", "Operations"],
    dataQualityNote: "Campus operations are displayed as read-only governance evidence.",
  },
  {
    domainId: "visitor-security-operations",
    title: "Visitor / Security Operations",
    description: "Security and visitor oversight indicators requiring human supervision.",
    metricKeys: [
      "security_high_risk_incidents_count",
      "security_incident_review_required_count",
      "security_incidents_escalated_count",
      "security_incidents_open_count",
      "access_denied_count",
      "unauthorized_attempts_count",
      "visitor_requests_pending_count",
      "visitor_unauthorized_attempts_count",
    ],
    criticalMetricKeys: ["security_high_risk_incidents_count"],
    riskMetricKeys: ["security_incidents_escalated_count", "security_incidents_open_count", "unauthorized_attempts_count"],
    watchMetricKeys: ["access_denied_count", "visitor_requests_pending_count", "visitor_unauthorized_attempts_count"],
    reviewMetricKeys: ["security_incident_review_required_count"],
    sourceDomains: ["Security Operations", "Visitor Management", "Access Control"],
    dataQualityNote: "No lockout or ban is executed from this dashboard view.",
  },
  {
    domainId: "room-allocation-scheduling-intelligence",
    title: "Room Allocation / Scheduling Intelligence",
    description: "Allocation and mismatch signals for review-required scheduling governance.",
    metricKeys: [
      "room_allocation_review_required_count",
      "room_allocation_no_viable_candidate_count",
      "room_capacity_mismatch_count",
      "room_equipment_mismatch_count",
      "room_type_mismatch_count",
      "room_computer_shortage_count",
      "room_allocation_recommendations_count",
    ],
    criticalMetricKeys: ["room_allocation_no_viable_candidate_count"],
    riskMetricKeys: ["room_capacity_mismatch_count", "room_equipment_mismatch_count", "room_type_mismatch_count", "room_computer_shortage_count"],
    watchMetricKeys: ["room_allocation_recommendations_count"],
    reviewMetricKeys: ["room_allocation_review_required_count"],
    sourceDomains: ["Room Allocation", "Scheduling Intelligence"],
    dataQualityNote: "Recommendations are advisory only and require human review.",
  },
  {
    domainId: "student-risk-interventions",
    title: "Student Risk / Interventions",
    description: "Student-risk and intervention pressure indicators where available.",
    metricKeys: [
      "critical_risk_students_count",
      "high_risk_students_count",
      "intervention_auto_created_count",
      "sweep_coverage_rate",
      "intervention_resolution_rate",
    ],
    criticalMetricKeys: ["critical_risk_students_count"],
    riskMetricKeys: ["high_risk_students_count", "intervention_auto_created_count"],
    watchMetricKeys: ["sweep_coverage_rate"],
    reviewMetricKeys: [],
    sourceDomains: ["Student Success", "Interventions"],
    dataQualityNote: "Optional domain; unavailable if tenant does not emit student-risk metrics.",
    optional: true,
  },
  {
    domainId: "research-accreditation-quality",
    title: "Research / Accreditation / Quality",
    description: "Ethics and quality governance risk indicators where supported.",
    metricKeys: [
      "research_ethics_high_risk_count",
      "research_ethics_review_cases_count",
      "research_ethics_requires_approval_count",
      "thesis_governance_risk_count",
    ],
    criticalMetricKeys: ["research_ethics_high_risk_count"],
    riskMetricKeys: ["thesis_governance_risk_count"],
    watchMetricKeys: ["research_ethics_review_cases_count"],
    reviewMetricKeys: ["research_ethics_requires_approval_count"],
    sourceDomains: ["Research Ethics", "Accreditation", "Quality"],
    dataQualityNote: "Optional domain; supported when corresponding governance evidence is present.",
    optional: true,
  },
  {
    domainId: "brain-review-required-actionability",
    title: "Brain / Review Required / Actionability",
    description: "Review-required queue and actionability pressure from cross-domain governance signals.",
    metricKeys: [
      "academic_integrity_cases_pending_review",
      "exam_integrity_requires_approval_count",
      "thesis_governance_requires_approval_count",
      "research_ethics_requires_approval_count",
      "security_incident_review_required_count",
      "budget_review_actions_count",
      "finance_operations_actionability_count",
    ],
    criticalMetricKeys: [],
    riskMetricKeys: ["finance_operations_actionability_count"],
    watchMetricKeys: [],
    reviewMetricKeys: [
      "academic_integrity_cases_pending_review",
      "exam_integrity_requires_approval_count",
      "thesis_governance_requires_approval_count",
      "research_ethics_requires_approval_count",
      "security_incident_review_required_count",
      "budget_review_actions_count",
    ],
    sourceDomains: ["Brain Core", "Review Queue", "Governance"],
    dataQualityNote: "Review-required indicators are evidence-backed and require human decisions.",
  },
];

const GOVERNANCE_ALERT_QUEUE_DOMAINS: GovernanceAlertDomainConfig[] = [
  {
    domainId: "academic-governance",
    domainTitle: "Academic Governance",
    title: "Academic governance review pressure",
    description: "Integrity, exam, thesis, and ethics evidence requiring rector-level review.",
    metricKeys: [
      "academic_integrity_high_risk_count",
      "academic_integrity_cases_pending_review",
      "exam_integrity_high_risk_count",
      "exam_integrity_requires_approval_count",
      "thesis_governance_risk_count",
      "thesis_governance_requires_approval_count",
      "research_ethics_high_risk_count",
      "research_ethics_requires_approval_count",
      "integrity_cases_resolved_count",
    ],
    criticalMetricKeys: ["academic_integrity_high_risk_count", "exam_integrity_high_risk_count", "research_ethics_high_risk_count"],
    highMetricKeys: ["thesis_governance_risk_count"],
    mediumMetricKeys: ["academic_integrity_cases_pending_review", "exam_integrity_requires_approval_count", "thesis_governance_requires_approval_count", "research_ethics_requires_approval_count"],
    reviewMetricKeys: ["academic_integrity_cases_pending_review", "exam_integrity_requires_approval_count", "thesis_governance_requires_approval_count", "research_ethics_requires_approval_count"],
    watchMetricKeys: [],
    resolvedMetricKeys: ["integrity_cases_resolved_count"],
    sourceDomains: ["Academic Integrity", "Exam Governance", "Thesis", "Research Ethics"],
    recommendedHumanAction: "Review integrity and governance evidence, then assign an academic review owner.",
    dataQualityNote: "Uses tenant KPI evidence only; unresolved metrics are surfaced for human review.",
  },
  {
    domainId: "finance-procurement-assets",
    domainTitle: "Finance / Procurement / Assets",
    title: "Finance and procurement review pressure",
    description: "Budget variance, procurement backlog, and asset-conversion risk indicators.",
    metricKeys: [
      "budget_overrun_risk_count",
      "active_finance_risk_signals_count",
      "asset_conversion_gap_count",
      "procurement_requests_pending_approval",
      "budget_review_actions_count",
      "finance_operations_actionability_count",
    ],
    criticalMetricKeys: ["budget_overrun_risk_count"],
    highMetricKeys: ["active_finance_risk_signals_count", "asset_conversion_gap_count"],
    mediumMetricKeys: ["budget_review_actions_count", "finance_operations_actionability_count"],
    reviewMetricKeys: ["budget_review_actions_count"],
    watchMetricKeys: ["procurement_requests_pending_approval"],
    sourceDomains: ["Finance", "Procurement", "Assets"],
    recommendedHumanAction: "Validate financial risk evidence and route procurement/asset exceptions to responsible reviewers.",
    dataQualityNote: "Approval actions are never auto-executed; this queue is evidence-only.",
  },
  {
    domainId: "campus-operations",
    domainTitle: "Campus Operations",
    title: "Campus operations anomalies",
    description: "Scheduling and campus-operations anomalies requiring oversight.",
    metricKeys: [
      "scheduling_conflicts_count",
      "room_conflict_count",
      "capacity_risk_sections_count",
      "events_cancelled_count",
      "events_registration_full_count",
    ],
    criticalMetricKeys: ["capacity_risk_sections_count"],
    highMetricKeys: ["scheduling_conflicts_count", "room_conflict_count"],
    mediumMetricKeys: [],
    reviewMetricKeys: [],
    watchMetricKeys: ["events_cancelled_count", "events_registration_full_count"],
    sourceDomains: ["Scheduling", "Events", "Operations"],
    recommendedHumanAction: "Review campus operations conflicts and prioritize manual remediation.",
    dataQualityNote: "Operational pressures are shown as review evidence only.",
  },
  {
    domainId: "security-visitor-operations",
    domainTitle: "Security / Visitor Operations",
    title: "Security and visitor review queue",
    description: "Security incidents and visitor anomalies requiring human review.",
    metricKeys: [
      "security_high_risk_incidents_count",
      "security_incident_review_required_count",
      "security_incidents_escalated_count",
      "access_denied_count",
      "visitor_unauthorized_attempts_count",
      "security_incidents_resolved_count",
    ],
    criticalMetricKeys: ["security_high_risk_incidents_count"],
    highMetricKeys: ["security_incidents_escalated_count"],
    mediumMetricKeys: ["security_incident_review_required_count"],
    reviewMetricKeys: ["security_incident_review_required_count", "visitor_unauthorized_attempts_count"],
    watchMetricKeys: ["access_denied_count"],
    resolvedMetricKeys: ["security_incidents_resolved_count"],
    sourceDomains: ["Security Operations", "Visitor Management", "Access Control"],
    recommendedHumanAction: "Perform security incident review and confirm visitor/access evidence with operations leadership.",
    dataQualityNote: "No lockout or ban is triggered from this queue.",
  },
  {
    domainId: "room-allocation-scheduling-intelligence",
    domainTitle: "Room Allocation / Scheduling Intelligence",
    title: "Room allocation review-required signals",
    description: "Allocation mismatches and no-viable-candidate evidence requiring scheduling review.",
    metricKeys: [
      "room_allocation_review_required_count",
      "room_allocation_no_viable_candidate_count",
      "room_capacity_mismatch_count",
      "room_equipment_mismatch_count",
      "room_type_mismatch_count",
      "room_computer_shortage_count",
      "room_conflict_count",
    ],
    criticalMetricKeys: ["room_allocation_no_viable_candidate_count"],
    highMetricKeys: ["room_capacity_mismatch_count", "room_conflict_count"],
    mediumMetricKeys: ["room_equipment_mismatch_count", "room_type_mismatch_count", "room_computer_shortage_count"],
    reviewMetricKeys: ["room_allocation_review_required_count"],
    watchMetricKeys: [],
    sourceDomains: ["Room Allocation", "Scheduling"],
    recommendedHumanAction: "Review room-allocation evidence and approve manual scheduling decisions.",
    dataQualityNote: "Read-only recommendations only; no automatic room assignment or schedule mutation.",
  },
  {
    domainId: "brain-review-required",
    domainTitle: "Brain / Review Required",
    title: "Cross-domain brain review queue",
    description: "Brain-driven review-required signals aggregated across governance domains.",
    metricKeys: [
      "academic_integrity_cases_pending_review",
      "exam_integrity_requires_approval_count",
      "thesis_governance_requires_approval_count",
      "research_ethics_requires_approval_count",
      "security_incident_review_required_count",
      "budget_review_actions_count",
      "finance_operations_actionability_count",
    ],
    criticalMetricKeys: [],
    highMetricKeys: ["finance_operations_actionability_count"],
    mediumMetricKeys: [
      "academic_integrity_cases_pending_review",
      "exam_integrity_requires_approval_count",
      "thesis_governance_requires_approval_count",
      "research_ethics_requires_approval_count",
      "security_incident_review_required_count",
      "budget_review_actions_count",
    ],
    reviewMetricKeys: [
      "academic_integrity_cases_pending_review",
      "exam_integrity_requires_approval_count",
      "thesis_governance_requires_approval_count",
      "research_ethics_requires_approval_count",
      "security_incident_review_required_count",
      "budget_review_actions_count",
    ],
    watchMetricKeys: [],
    sourceDomains: ["Brain Core", "Governance Review", "Actionability"],
    recommendedHumanAction: "Triage review-required backlog and assign human owners by domain.",
    dataQualityNote: "Queue entries are evidence-backed and require explicit human closure.",
  },
  {
    domainId: "student-risk-interventions",
    domainTitle: "Student Risk / Interventions",
    title: "Student intervention pressure",
    description: "Student-risk and intervention load indicators, when available.",
    metricKeys: [
      "critical_risk_students_count",
      "high_risk_students_count",
      "intervention_auto_created_count",
      "intervention_resolution_rate",
    ],
    criticalMetricKeys: ["critical_risk_students_count"],
    highMetricKeys: ["high_risk_students_count"],
    mediumMetricKeys: ["intervention_auto_created_count"],
    reviewMetricKeys: [],
    watchMetricKeys: ["intervention_resolution_rate"],
    sourceDomains: ["Student Success", "Interventions"],
    recommendedHumanAction: "Prioritize high-risk student cohorts and validate intervention outcomes.",
    dataQualityNote: "Optional domain; unavailable if tenant does not emit intervention KPIs.",
    optional: true,
  },
  {
    domainId: "research-accreditation-quality",
    domainTitle: "Research / Accreditation / Quality",
    title: "Research and quality review pressure",
    description: "Research ethics and quality governance indicators, when available.",
    metricKeys: [
      "research_ethics_high_risk_count",
      "research_ethics_review_cases_count",
      "research_ethics_requires_approval_count",
      "thesis_governance_risk_count",
    ],
    criticalMetricKeys: ["research_ethics_high_risk_count"],
    highMetricKeys: ["thesis_governance_risk_count"],
    mediumMetricKeys: ["research_ethics_requires_approval_count"],
    reviewMetricKeys: ["research_ethics_requires_approval_count"],
    watchMetricKeys: ["research_ethics_review_cases_count"],
    sourceDomains: ["Research Ethics", "Accreditation", "Quality"],
    recommendedHumanAction: "Validate ethics/quality evidence and route for committee review.",
    dataQualityNote: "Optional domain; shown as unavailable when tenant evidence is missing.",
    optional: true,
  },
];

const KPI_EVIDENCE_DRILLDOWN_CONFIG: KpiEvidenceDrilldownConfig[] = [
  {
    domainId: "academic-governance",
    domainTitle: "Academic Governance",
    title: "Academic governance evidence contract",
    metricKeys: [
      "academic_integrity_high_risk_count",
      "academic_integrity_cases_pending_review",
      "exam_integrity_requires_approval_count",
      "thesis_governance_requires_approval_count",
      "research_ethics_requires_approval_count",
    ],
    criticalMetricKeys: ["academic_integrity_high_risk_count"],
    highMetricKeys: ["exam_integrity_requires_approval_count"],
    mediumMetricKeys: ["thesis_governance_requires_approval_count", "research_ethics_requires_approval_count"],
    reviewMetricKeys: ["academic_integrity_cases_pending_review", "exam_integrity_requires_approval_count", "thesis_governance_requires_approval_count", "research_ethics_requires_approval_count"],
    sourceDomains: ["Academic Integrity", "Exam Governance", "Thesis", "Research Ethics"],
    explanation: "Academic governance signals require human review and are evidence-backed; no automatic disciplinary action is executed.",
    dataQualityNote: "Missing integrity/governance metrics are shown as unavailable instead of inferred.",
  },
  {
    domainId: "finance-procurement-assets",
    domainTitle: "Finance / Procurement / Assets",
    title: "Finance and procurement evidence contract",
    metricKeys: [
      "budget_overrun_risk_count",
      "budget_review_actions_count",
      "active_finance_risk_signals_count",
      "asset_conversion_gap_count",
      "procurement_requests_pending_approval",
    ],
    criticalMetricKeys: ["budget_overrun_risk_count"],
    highMetricKeys: ["active_finance_risk_signals_count", "asset_conversion_gap_count"],
    mediumMetricKeys: ["budget_review_actions_count"],
    reviewMetricKeys: ["budget_review_actions_count"],
    sourceDomains: ["Finance", "Procurement", "Assets"],
    explanation: "Finance and procurement signals are governance review indicators only; no automatic approval is executed.",
    dataQualityNote: "Source lineage remains limited to available tenant KPI metrics.",
  },
  {
    domainId: "campus-operations",
    domainTitle: "Campus Operations",
    title: "Campus operations evidence contract",
    metricKeys: [
      "scheduling_conflicts_count",
      "room_conflict_count",
      "capacity_risk_sections_count",
      "events_cancelled_count",
    ],
    criticalMetricKeys: ["capacity_risk_sections_count"],
    highMetricKeys: ["scheduling_conflicts_count", "room_conflict_count"],
    mediumMetricKeys: ["events_cancelled_count"],
    reviewMetricKeys: [],
    sourceDomains: ["Scheduling", "Events", "Operations"],
    explanation: "Campus operations signals summarize operational pressure and require operator review.",
    dataQualityNote: "Operational evidence is read-only and may be partial depending on tenant instrumentation.",
  },
  {
    domainId: "security-visitor-operations",
    domainTitle: "Security / Visitor Operations",
    title: "Security and visitor evidence contract",
    metricKeys: [
      "security_incident_review_required_count",
      "security_high_risk_incidents_count",
      "visitor_unauthorized_attempts_count",
      "access_denied_count",
    ],
    criticalMetricKeys: ["security_high_risk_incidents_count"],
    highMetricKeys: ["security_incident_review_required_count"],
    mediumMetricKeys: ["visitor_unauthorized_attempts_count", "access_denied_count"],
    reviewMetricKeys: ["security_incident_review_required_count", "visitor_unauthorized_attempts_count"],
    sourceDomains: ["Security Operations", "Visitor Management", "Access Control"],
    explanation: "Security signals are review/escalation evidence only; no automatic lockout or ban is executed.",
    dataQualityNote: "Unavailable security metrics are surfaced explicitly with no synthetic fallback.",
  },
  {
    domainId: "room-allocation-scheduling-intelligence",
    domainTitle: "Room Allocation / Scheduling Intelligence",
    title: "Room allocation evidence contract",
    metricKeys: [
      "room_allocation_review_required_count",
      "room_allocation_no_viable_candidate_count",
      "room_allocation_recommendations_count",
      "room_capacity_mismatch_count",
      "room_conflict_count",
    ],
    criticalMetricKeys: ["room_allocation_no_viable_candidate_count"],
    highMetricKeys: ["room_capacity_mismatch_count", "room_conflict_count"],
    mediumMetricKeys: ["room_allocation_review_required_count"],
    reviewMetricKeys: ["room_allocation_review_required_count"],
    sourceDomains: ["Room Allocation", "Scheduling"],
    explanation: "Room allocation recommendation evidence is advisory-only and requires human review for risk cases.",
    dataQualityNote: "No automatic room assignment or schedule mutation is available from this surface.",
  },
  {
    domainId: "brain-review-required",
    domainTitle: "Brain / Review Required",
    title: "Brain review-required evidence contract",
    metricKeys: [
      "academic_integrity_cases_pending_review",
      "exam_integrity_requires_approval_count",
      "thesis_governance_requires_approval_count",
      "research_ethics_requires_approval_count",
      "security_incident_review_required_count",
      "budget_review_actions_count",
    ],
    criticalMetricKeys: [],
    highMetricKeys: ["security_incident_review_required_count"],
    mediumMetricKeys: [
      "academic_integrity_cases_pending_review",
      "exam_integrity_requires_approval_count",
      "thesis_governance_requires_approval_count",
      "research_ethics_requires_approval_count",
      "budget_review_actions_count",
    ],
    reviewMetricKeys: [
      "academic_integrity_cases_pending_review",
      "exam_integrity_requires_approval_count",
      "thesis_governance_requires_approval_count",
      "research_ethics_requires_approval_count",
      "security_incident_review_required_count",
      "budget_review_actions_count",
    ],
    sourceDomains: ["Brain Core", "Governance Review"],
    explanation: "Brain signals are advisory and evidence-backed; decision authority remains with humans.",
    dataQualityNote: "Review-required entries always require explicit human closure.",
  },
  {
    domainId: "student-risk-interventions",
    domainTitle: "Student Risk / Interventions",
    title: "Student intervention evidence contract",
    metricKeys: ["critical_risk_students_count", "high_risk_students_count", "intervention_auto_created_count"],
    criticalMetricKeys: ["critical_risk_students_count"],
    highMetricKeys: ["high_risk_students_count"],
    mediumMetricKeys: ["intervention_auto_created_count"],
    reviewMetricKeys: [],
    sourceDomains: ["Student Success", "Interventions"],
    explanation: "Student-risk evidence supports human intervention prioritization.",
    dataQualityNote: "Optional domain; may be unavailable in tenants without intervention telemetry.",
    optional: true,
  },
  {
    domainId: "research-accreditation-quality",
    domainTitle: "Research / Accreditation / Quality",
    title: "Research and quality evidence contract",
    metricKeys: ["research_ethics_high_risk_count", "research_ethics_review_cases_count", "research_ethics_requires_approval_count", "thesis_governance_risk_count"],
    criticalMetricKeys: ["research_ethics_high_risk_count"],
    highMetricKeys: ["thesis_governance_risk_count"],
    mediumMetricKeys: ["research_ethics_requires_approval_count", "research_ethics_review_cases_count"],
    reviewMetricKeys: ["research_ethics_requires_approval_count"],
    sourceDomains: ["Research Ethics", "Accreditation", "Quality"],
    explanation: "Research and quality evidence highlights review pressure and remains advisory-only.",
    dataQualityNote: "Optional domain; unavailable state is explicit when metrics are missing.",
    optional: true,
  },
];

const GOVERNANCE_COMMAND_CENTER_SECTIONS: GovernanceCommandCenterSection[] = [
  { sectionId: "executive-overview", title: "Executive Health / Command Center Overview" },
  { sectionId: "ministry-reporting-shell", title: "Ministry-Ready Governance Reporting Shell" },
  { sectionId: "cross-domain-risk-heatmap", title: "Cross-domain Risk Heatmap" },
  { sectionId: "governance-alert-review-queue", title: "Governance Alert / Review Queue" },
  { sectionId: "kpi-evidence-drilldown", title: "KPI Evidence Drilldown Contract" },
  { sectionId: "domain-intelligence", title: "Domain Intelligence Sections (Room Allocation / Security / Campus / Finance / Academic)" },
];

function ExecutiveKpiSection({ section }: { section: ExecutiveKpiSectionConfig }) {
  return (
    <section data-testid={section.testId} className="space-y-3">
      <div className="rounded-md border bg-muted/20 p-3">
        <p className="text-sm font-medium">{section.title}</p>
        <p className="text-xs text-muted-foreground mt-1">{section.description}</p>
      </div>
      {section.advisoryTitle && section.advisoryText && (
        <div className="rounded-md border bg-muted/20 p-3">
          <p className="text-sm font-medium">{section.advisoryTitle}</p>
          <p className="text-xs text-muted-foreground mt-1">{section.advisoryText}</p>
        </div>
      )}
      <Wave1KpiBar metricKeys={section.metricKeys} labels={section.labels} />
    </section>
  );
}

function GovernanceReportShell({
  data,
  tenantId,
  generatedLabel,
}: {
  data: { cards: DashboardCardSnapshot[] } | undefined;
  tenantId: number;
  generatedLabel: string;
}) {
  const cardByMetricKey = useMemo(() => {
    const entries = (data?.cards ?? []).map((card) => [card.metric_key, card] as const);
    return new Map(entries);
  }, [data?.cards]);

  const getMetricValue = (metricKey: string) => {
    const card = cardByMetricKey.get(metricKey);
    return card ? Number(card.value).toLocaleString() : "Not available";
  };

  const hasAnyEvidence = (metricKeys: string[]) => metricKeys.some((metricKey) => cardByMetricKey.has(metricKey));

  return (
    <section className="space-y-4" data-testid="ministry-governance-report-shell">
      <div className="rounded-lg border bg-card p-4">
        <p className="text-sm font-semibold">Ministry / Governance Reporting</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Read-only, tenant-scoped, evidence-backed reporting shell for rector/ministry review. Not submitted externally.
          All approvals and actions remain human-managed; no disciplinary action, schedule mutation, or procurement action is triggered here.
        </p>
        <p className="mt-2 text-xs text-muted-foreground">
          Tenant {tenantId} • Last updated {generatedLabel} • Export-ready contract only
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        {GOVERNANCE_REPORT_SECTIONS.map((section) => {
          const hasEvidence = hasAnyEvidence(section.metricKeys);
          const displayMetricKeys = section.metricKeys.slice(0, 4);
          const evidenceLabel = hasEvidence ? "Evidence-backed" : "Not available";

          return (
            <article key={section.sectionId} data-testid={`governance-report-section-${section.sectionId}`} className="rounded-lg border bg-card p-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="text-sm font-semibold">{section.title}</h3>
                  <p className="mt-1 text-xs text-muted-foreground">{section.description}</p>
                </div>
                <span className="rounded-full bg-muted px-2 py-1 text-[11px] font-medium text-muted-foreground">
                  {evidenceLabel}
                </span>
              </div>

              <div className="mt-3 space-y-2 text-xs text-muted-foreground">
                <p>Source domains: {section.sourceDomains.join(" / ")}</p>
                <p>Read-only: yes</p>
                <p>Tenant-scoped: yes</p>
                <p>{section.dataQualityNote}</p>
              </div>

              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                {displayMetricKeys.length > 0 ? (
                  displayMetricKeys.map((metricKey) => {
                    const card = cardByMetricKey.get(metricKey);
                    const label = card?.title ?? metricKey;
                    return (
                      <div key={metricKey} className="rounded-md border bg-muted/20 p-3">
                        <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</p>
                        <p className="mt-1 text-sm font-medium">{getMetricValue(metricKey)}</p>
                      </div>
                    );
                  })
                ) : (
                  <div className="rounded-md border bg-muted/20 p-3 sm:col-span-2">
                    <p className="text-sm font-medium">No direct KPI bindings yet</p>
                    <p className="mt-1 text-xs text-muted-foreground">This section is reserved for narrative notes only.</p>
                  </div>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function CrossDomainRiskHeatmap({
  data,
  tenantId,
}: {
  data: { cards: DashboardCardSnapshot[] } | undefined;
  tenantId: number;
}) {
  const cardByMetricKey = useMemo(() => {
    const entries = (data?.cards ?? []).map((card) => [card.metric_key, card] as const);
    return new Map(entries);
  }, [data?.cards]);

  const readMetricValue = (metricKey: string) => {
    const card = cardByMetricKey.get(metricKey);
    if (!card) return null;
    const value = Number(card.value);
    return Number.isFinite(value) ? value : null;
  };

  const hasPositiveValue = (metricKeys: string[]) => metricKeys.some((metricKey) => {
    const value = readMetricValue(metricKey);
    return value !== null && value > 0;
  });

  const domains = CROSS_DOMAIN_RISK_HEATMAP.map((domain) => {
    const availableMetricKeys = domain.metricKeys.filter((metricKey) => cardByMetricKey.has(metricKey));
    const hasEvidence = availableMetricKeys.length > 0;

    let riskLevel: "healthy" | "watch" | "risk" | "critical" | "unavailable" = "healthy";
    if (!hasEvidence) {
      riskLevel = "unavailable";
    } else if (hasPositiveValue(domain.criticalMetricKeys)) {
      riskLevel = "critical";
    } else if (hasPositiveValue(domain.riskMetricKeys)) {
      riskLevel = "risk";
    } else if (hasPositiveValue(domain.reviewMetricKeys) || hasPositiveValue(domain.watchMetricKeys)) {
      riskLevel = "watch";
    }

    const reviewRequired = hasPositiveValue(domain.reviewMetricKeys);
    const evidenceItems = availableMetricKeys
      .filter((metricKey) => {
        const value = readMetricValue(metricKey);
        return value !== null && value > 0;
      })
      .slice(0, 3)
      .map((metricKey) => {
        const card = cardByMetricKey.get(metricKey);
        return {
          label: card?.title ?? metricKey,
          value: readMetricValue(metricKey) ?? 0,
        };
      });

    return {
      ...domain,
      hasEvidence,
      availableMetricKeys,
      riskLevel,
      reviewRequired,
      evidenceItems,
    };
  });

  const riskLevelClassName: Record<string, string> = {
    critical: "bg-red-100 text-red-700",
    risk: "bg-amber-100 text-amber-700",
    watch: "bg-blue-100 text-blue-700",
    healthy: "bg-emerald-100 text-emerald-700",
    unavailable: "bg-muted text-muted-foreground",
  };

  return (
    <section className="space-y-4" data-testid="cross-domain-risk-heatmap">
      <div className="rounded-lg border bg-card p-4">
        <p className="text-sm font-semibold">Cross-domain Risk Heatmap</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Read-only, evidence-backed cross-domain risk summary for tenant-scoped governance review.
          Risk levels indicate operational pressure and review needs requiring human review.
        </p>
        <p className="mt-2 text-xs text-muted-foreground">Tenant {tenantId} context only • No external submission • No automatic action execution</p>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        {domains.map((domain) => (
          <article key={domain.domainId} data-testid={`risk-heatmap-domain-${domain.domainId}`} className="rounded-lg border bg-card p-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-sm font-semibold">{domain.title}</h3>
                <p className="mt-1 text-xs text-muted-foreground">{domain.description}</p>
              </div>
              <span className={`rounded-full px-2 py-1 text-[11px] font-medium ${riskLevelClassName[domain.riskLevel]}`}>
                {domain.riskLevel}
              </span>
            </div>

            <div className="mt-3 space-y-1 text-xs text-muted-foreground">
              <p>Source domains: {domain.sourceDomains.join(" / ")}</p>
              <p>Evidence-backed: {domain.hasEvidence ? "yes" : "unavailable"}</p>
              <p>Review required: {domain.reviewRequired ? "yes" : "no"}</p>
              <p>Read-only governance surface: yes</p>
              {domain.optional && <p>Optional domain support: enabled when tenant metrics are available</p>}
            </div>

            <div className="mt-3 rounded-md border bg-muted/20 p-3">
              {domain.evidenceItems.length > 0 ? (
                <ul className="space-y-1 text-xs text-muted-foreground">
                  {domain.evidenceItems.map((item) => (
                    <li key={item.label}>
                      {item.label}: {item.value.toLocaleString()}
                    </li>
                  ))}
                </ul>
              ) : domain.hasEvidence ? (
                <p className="text-xs text-muted-foreground">No elevated risk signal in currently available metrics.</p>
              ) : (
                <p className="text-xs text-muted-foreground">Domain evidence is unavailable in current tenant snapshot.</p>
              )}
            </div>

            <p className="mt-3 text-xs text-muted-foreground">Data quality note: {domain.dataQualityNote}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function GovernanceAlertReviewQueue({
  data,
  tenantId,
}: {
  data: { cards: DashboardCardSnapshot[] } | undefined;
  tenantId: number;
}) {
  const cardByMetricKey = useMemo(() => {
    const entries = (data?.cards ?? []).map((card) => [card.metric_key, card] as const);
    return new Map(entries);
  }, [data?.cards]);

  const readMetricValue = (metricKey: string) => {
    const card = cardByMetricKey.get(metricKey);
    if (!card) return null;
    const value = Number(card.value);
    return Number.isFinite(value) ? value : null;
  };

  const hasPositiveValue = (metricKeys: string[]) => metricKeys.some((metricKey) => {
    const value = readMetricValue(metricKey);
    return value !== null && value > 0;
  });

  const positiveMetricSummaries = (metricKeys: string[]) => metricKeys
    .filter((metricKey) => {
      const value = readMetricValue(metricKey);
      return value !== null && value > 0;
    })
    .slice(0, 3)
    .map((metricKey) => {
      const card = cardByMetricKey.get(metricKey);
      return `${card?.title ?? metricKey}: ${(readMetricValue(metricKey) ?? 0).toLocaleString()}`;
    });

  const alerts: GovernanceReviewAlert[] = GOVERNANCE_ALERT_QUEUE_DOMAINS.map((domain) => {
    const availableMetricKeys = domain.metricKeys.filter((metricKey) => cardByMetricKey.has(metricKey));
    const hasEvidence = availableMetricKeys.length > 0;

    let severity: GovernanceReviewAlert["severity"] = "low";
    if (!hasEvidence) {
      severity = "unavailable";
    } else if (hasPositiveValue(domain.criticalMetricKeys)) {
      severity = "critical";
    } else if (hasPositiveValue(domain.highMetricKeys)) {
      severity = "high";
    } else if (hasPositiveValue(domain.mediumMetricKeys) || hasPositiveValue(domain.reviewMetricKeys)) {
      severity = "medium";
    }

    let reviewStatus: GovernanceReviewAlert["reviewStatus"] = "evidence_only";
    if (!hasEvidence) {
      reviewStatus = "unavailable";
    } else if (hasPositiveValue(domain.reviewMetricKeys) || hasPositiveValue(domain.criticalMetricKeys) || hasPositiveValue(domain.highMetricKeys)) {
      reviewStatus = "review_required";
    } else if (hasPositiveValue(domain.watchMetricKeys)) {
      reviewStatus = "watch";
    } else if (domain.resolvedMetricKeys && hasPositiveValue(domain.resolvedMetricKeys)) {
      reviewStatus = "resolved";
    }

    const evidenceRows = positiveMetricSummaries(availableMetricKeys);
    const evidenceSummary = evidenceRows.length > 0
      ? evidenceRows.join(" | ")
      : hasEvidence
        ? "Evidence available with no elevated queue signal."
        : "Domain evidence unavailable in this tenant snapshot.";

    return {
      alertId: `queue-${domain.domainId}`,
      domainId: domain.domainId,
      domainTitle: domain.domainTitle,
      title: domain.title,
      severity,
      reviewStatus,
      evidenceSummary,
      sourceMetrics: availableMetricKeys,
      sourceDomains: domain.sourceDomains,
      recommendedHumanAction: domain.recommendedHumanAction,
      dataQualityNote: domain.dataQualityNote,
      tenantScoped: true,
      readonly: true,
    };
  });

  const criticalCount = alerts.filter((alert) => alert.severity === "critical").length;
  const reviewRequiredCount = alerts.filter((alert) => alert.reviewStatus === "review_required").length;

  const severityClass: Record<GovernanceReviewAlert["severity"], string> = {
    critical: "bg-red-100 text-red-700",
    high: "bg-amber-100 text-amber-700",
    medium: "bg-blue-100 text-blue-700",
    low: "bg-emerald-100 text-emerald-700",
    unavailable: "bg-muted text-muted-foreground",
  };

  return (
    <section className="space-y-4" data-testid="governance-alert-review-queue">
      <div className="rounded-lg border bg-card p-4">
        <p className="text-sm font-semibold">Governance Alert / Review Queue</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Read-only queue showing what needs human attention now, why it matters, and which domain emitted supporting evidence.
          Review required items are evidence-backed and remain human-managed.
        </p>
        <p className="mt-2 text-xs text-muted-foreground">
          Tenant {tenantId} context only • Human review required • Evidence-backed • Read-only • No automatic action
        </p>
        <div className="mt-3 grid gap-2 sm:grid-cols-3">
          <div className="rounded-md border bg-muted/20 p-3">
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Total alerts</p>
            <p className="mt-1 text-sm font-medium">{alerts.length.toLocaleString()}</p>
          </div>
          <div className="rounded-md border bg-muted/20 p-3">
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Critical count</p>
            <p className="mt-1 text-sm font-medium">{criticalCount.toLocaleString()}</p>
          </div>
          <div className="rounded-md border bg-muted/20 p-3">
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Review required count</p>
            <p className="mt-1 text-sm font-medium">{reviewRequiredCount.toLocaleString()}</p>
          </div>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        {alerts.map((alert) => (
          <article key={alert.alertId} data-testid={`governance-alert-domain-${alert.domainId}`} className="rounded-lg border bg-card p-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-sm font-semibold">{alert.domainTitle}</h3>
                <p className="mt-1 text-xs text-muted-foreground">{alert.title}</p>
              </div>
              <span className={`rounded-full px-2 py-1 text-[11px] font-medium ${severityClass[alert.severity]}`}>{alert.severity}</span>
            </div>

            <div className="mt-3 space-y-1 text-xs text-muted-foreground">
              <p>Review status: {alert.reviewStatus}</p>
              <p>Evidence: {alert.evidenceSummary}</p>
              <p>Source domains: {alert.sourceDomains.join(" / ")}</p>
              <p>Source metrics: {alert.sourceMetrics.length > 0 ? alert.sourceMetrics.slice(0, 3).join(", ") : "unavailable"}</p>
              <p>Recommended human action: {alert.recommendedHumanAction}</p>
              <p>Read-only: {alert.readonly ? "yes" : "no"}</p>
              <p>Tenant-scoped: {alert.tenantScoped ? "yes" : "no"}</p>
              <p>Data quality note: {alert.dataQualityNote}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function KpiEvidenceDrilldownContract({
  data,
  tenantId,
}: {
  data: { cards: DashboardCardSnapshot[] } | undefined;
  tenantId: number;
}) {
  const cardByMetricKey = useMemo(() => {
    const entries = (data?.cards ?? []).map((card) => [card.metric_key, card] as const);
    return new Map(entries);
  }, [data?.cards]);

  const readMetricValue = (metricKey: string) => {
    const card = cardByMetricKey.get(metricKey);
    if (!card) return null;
    const value = Number(card.value);
    return Number.isFinite(value) ? value : null;
  };

  const hasPositiveValue = (metricKeys: string[]) => metricKeys.some((metricKey) => {
    const value = readMetricValue(metricKey);
    return value !== null && value > 0;
  });

  const drilldowns: KpiEvidenceDrilldown[] = KPI_EVIDENCE_DRILLDOWN_CONFIG.map((config) => {
    const availableMetricKeys = config.metricKeys.filter((metricKey) => cardByMetricKey.has(metricKey));
    const hasEvidence = availableMetricKeys.length > 0;

    let riskLevel: KpiEvidenceDrilldown["riskLevel"] = "low";
    if (!hasEvidence) {
      riskLevel = "unavailable";
    } else if (hasPositiveValue(config.criticalMetricKeys)) {
      riskLevel = "critical";
    } else if (hasPositiveValue(config.highMetricKeys)) {
      riskLevel = "high";
    } else if (hasPositiveValue(config.mediumMetricKeys) || hasPositiveValue(config.reviewMetricKeys)) {
      riskLevel = "medium";
    }

    const reviewRequired = hasEvidence && (hasPositiveValue(config.reviewMetricKeys) || hasPositiveValue(config.highMetricKeys) || hasPositiveValue(config.criticalMetricKeys));

    const evidenceSources: KpiEvidenceSource[] = config.metricKeys.slice(0, 4).map((metricKey) => {
      const card = cardByMetricKey.get(metricKey);
      const value = readMetricValue(metricKey);
      return {
        metricKey,
        label: card?.title ?? metricKey,
        valueLabel: value === null ? "Unavailable" : value.toLocaleString(),
        sourceDomain: config.sourceDomains[0] ?? config.domainTitle,
        interpretation: value === null ? "Evidence unavailable in current tenant snapshot." : value > 0 ? "Evidence supports visibility of this KPI/risk/alert." : "Evidence available with no elevated signal.",
        available: value !== null,
      };
    });

    const positiveEvidenceSummary = evidenceSources
      .filter((source) => source.available && source.valueLabel !== "0")
      .slice(0, 3)
      .map((source) => `${source.label}: ${source.valueLabel}`)
      .join(" | ");

    const evidenceSummary = positiveEvidenceSummary.length > 0
      ? positiveEvidenceSummary
      : hasEvidence
        ? "Evidence-backed metrics are present with no elevated value in this snapshot."
        : "Evidence unavailable in current tenant snapshot.";

    return {
      drilldownId: `kpi-evidence-${config.domainId}`,
      title: config.title,
      domainId: config.domainId,
      domainTitle: config.domainTitle,
      sourceMetrics: availableMetricKeys,
      sourceDomains: config.sourceDomains,
      evidenceSummary,
      explanation: config.explanation,
      riskLevel,
      reviewRequired,
      dataQualityNote: config.dataQualityNote,
      readonly: true,
      tenantScoped: true,
      evidenceSources,
    };
  });

  const riskBadgeClass: Record<KpiEvidenceDrilldown["riskLevel"], string> = {
    critical: "bg-red-100 text-red-700",
    high: "bg-amber-100 text-amber-700",
    medium: "bg-blue-100 text-blue-700",
    low: "bg-emerald-100 text-emerald-700",
    unavailable: "bg-muted text-muted-foreground",
  };

  return (
    <section className="space-y-4" data-testid="kpi-evidence-drilldown-contract">
      <div className="rounded-lg border bg-card p-4">
        <p className="text-sm font-semibold">KPI Evidence Drilldown Contract</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Evidence-backed drilldown explaining why KPI, risk, and alert signals are visible for governance review.
          Read-only evidence context is tenant-scoped and supports human review only.
        </p>
        <p className="mt-2 text-xs text-muted-foreground">
          Tenant {tenantId} context only • Source metrics • Source domains • Human review • Read-only • No automatic action
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        {drilldowns.map((drilldown) => (
          <article key={drilldown.drilldownId} data-testid={`kpi-evidence-drilldown-domain-${drilldown.domainId}`} className="rounded-lg border bg-card p-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-sm font-semibold">{drilldown.domainTitle}</h3>
                <p className="mt-1 text-xs text-muted-foreground">{drilldown.title}</p>
              </div>
              <span className={`rounded-full px-2 py-1 text-[11px] font-medium ${riskBadgeClass[drilldown.riskLevel]}`}>{drilldown.riskLevel}</span>
            </div>

            <div className="mt-3 space-y-1 text-xs text-muted-foreground">
              <p>Evidence-backed: {drilldown.riskLevel === "unavailable" ? "unavailable" : "yes"}</p>
              <p>Source metrics: {drilldown.sourceMetrics.length > 0 ? drilldown.sourceMetrics.slice(0, 4).join(", ") : "unavailable"}</p>
              <p>Source domains: {drilldown.sourceDomains.join(" / ")}</p>
              <p>Evidence summary: {drilldown.evidenceSummary}</p>
              <p>Explanation: {drilldown.explanation}</p>
              <p>Human review: {drilldown.reviewRequired ? "required" : "not currently required"}</p>
              <p>Read-only: yes</p>
              <p>No automatic action: yes</p>
              <p>Data quality note: {drilldown.dataQualityNote}</p>
            </div>

            <div className="mt-3 rounded-md border bg-muted/20 p-3 text-xs text-muted-foreground space-y-1">
              {drilldown.evidenceSources.map((source) => (
                <p key={source.metricKey}>
                  {source.label} ({source.sourceDomain}): {source.valueLabel}
                </p>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function GovernanceCommandCenterContract({ tenantId }: { tenantId: number }) {
  return (
    <section className="space-y-3" data-testid="governance-command-center-contract">
      <div className="rounded-lg border bg-card p-4">
        <p className="text-sm font-semibold">Governance Command Center Contract</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Consolidated rector/ministry governance dashboard contract: tenant-scoped, evidence-backed, read-only, and human-review driven.
          No automatic action is executed from this surface.
        </p>
        <p className="mt-2 text-xs text-muted-foreground">
          Tenant {tenantId} context only • Read-only • Evidence-backed • Human review • No automatic action
        </p>
      </div>
      <div className="rounded-lg border bg-card p-4" data-testid="governance-command-center-section-order">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Consolidated section order</p>
        <ol className="mt-2 list-decimal pl-5 space-y-1 text-xs text-muted-foreground">
          {GOVERNANCE_COMMAND_CENTER_SECTIONS.map((section) => (
            <li key={section.sectionId}>{section.title}</li>
          ))}
        </ol>
      </div>
    </section>
  );
}

const riskBadgeClass: Record<string, string> = {
  critical: "bg-red-100 text-red-700",
  high: "bg-amber-100 text-amber-700",
  medium: "bg-blue-100 text-blue-700",
  low: "bg-emerald-100 text-emerald-700",
  unavailable: "bg-muted text-muted-foreground",
};

function RectorKpiDrilldownPanel({ tenantId }: { tenantId: number }) {
  const { data, isLoading, isError } = useRectorKpiDrilldown(tenantId);

  return (
    <section className="space-y-4" data-testid="rector-kpi-drilldown-panel">
      <div className="rounded-lg border bg-card p-4">
        <p className="text-sm font-semibold">Rector KPI Evidence Drilldown</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Domain-level evidence completeness derived from existing KPI metric snapshots.
          Read-only — no policy enforcement, no autonomous decision, no data mutation.
        </p>
        <p className="mt-2 text-xs text-muted-foreground">
          Tenant {tenantId} • Source: {data?.source ?? "kpi_metrics_engine_v1"} •
          Read-only: yes • Tenant-scoped: yes
        </p>
      </div>

      {isLoading && (
        <div className="rounded-lg border bg-card p-4" data-testid="rector-kpi-drilldown-loading">
          <p className="text-sm text-muted-foreground">Loading evidence drilldown…</p>
        </div>
      )}

      {isError && !isLoading && (
        <div className="rounded-lg border bg-card p-4" data-testid="rector-kpi-drilldown-error">
          <p className="text-sm text-muted-foreground">Evidence drilldown unavailable in current snapshot.</p>
        </div>
      )}

      {!isLoading && !isError && data && (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4" data-testid="rector-kpi-drilldown-summary-counts">
            <div className="rounded-md border bg-muted/20 p-3 text-center">
              <p className="text-lg font-bold">{data.total_domains}</p>
              <p className="text-xs text-muted-foreground">Total domains</p>
            </div>
            <div className="rounded-md border bg-muted/20 p-3 text-center">
              <p className="text-lg font-bold">{data.review_required_count}</p>
              <p className="text-xs text-muted-foreground">Review required</p>
            </div>
            <div className="rounded-md border bg-muted/20 p-3 text-center">
              <p className="text-lg font-bold">{data.critical_domains_count}</p>
              <p className="text-xs text-muted-foreground">Critical</p>
            </div>
            <div className="rounded-md border bg-muted/20 p-3 text-center">
              <p className="text-lg font-bold">{data.unavailable_domains_count}</p>
              <p className="text-xs text-muted-foreground">Unavailable</p>
            </div>
          </div>

          <div className="grid gap-4 xl:grid-cols-2" data-testid="rector-kpi-drilldown-domains">
            {data.domains.map((domain) => (
              <article
                key={domain.drilldown_id}
                data-testid={`rector-kpi-drilldown-domain-${domain.domain_id}`}
                className="rounded-lg border bg-card p-4"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="text-sm font-semibold">{domain.domain_title}</h3>
                    <p className="mt-1 text-xs text-muted-foreground">{domain.title}</p>
                  </div>
                  <span className={`rounded-full px-2 py-1 text-[11px] font-medium ${riskBadgeClass[domain.risk_level] ?? riskBadgeClass.unavailable}`}>
                    {domain.risk_level}
                  </span>
                </div>

                <div className="mt-3 space-y-1 text-xs text-muted-foreground">
                  <p>Evidence: {domain.evidence_summary}</p>
                  <p>Source domains: {domain.source_domains.join(" / ")}</p>
                  <p>Review required: {domain.review_required ? "yes" : "no"}</p>
                  <p>Read-only: yes • Tenant-scoped: yes • No automatic action</p>
                  {domain.optional && <p>Optional domain: shown when tenant metrics are available</p>}
                </div>

                {domain.evidence_sources.length > 0 && (
                  <div className="mt-3 rounded-md border bg-muted/20 p-3">
                    <ul className="space-y-1 text-xs text-muted-foreground">
                      {domain.evidence_sources.map((src) => (
                        <li key={src.metric_key}>
                          {src.label}: {src.value_label}
                          {!src.available && <span className="ml-1 text-muted-foreground/60">(unavailable)</span>}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <p className="mt-3 text-xs text-muted-foreground">
                  {domain.explanation}
                </p>
                <p className="mt-1 text-xs text-muted-foreground/70">Data quality: {domain.data_quality_note}</p>
              </article>
            ))}
          </div>
        </>
      )}
    </section>
  );
}

function DashboardSkeletonGrid() {
  return (
    <div className="grid gap-4 grid-cols-1 md:grid-cols-2 xl:grid-cols-3" data-testid="kpi-loading-grid">
      {Array.from({ length: 6 }).map((_, idx) => (
        <div key={idx} className="rounded-lg border bg-card p-6">
          <Skeleton className="h-4 w-40" />
          <Skeleton className="mt-3 h-8 w-24" />
          <Skeleton className="mt-4 h-8 w-full" />
        </div>
      ))}
    </div>
  );
}

export default function RectorDashboardPage() {
  const { user } = useAdminAuth();
  const { t } = useLanguage();
  const tenantId = user?.tenantId ?? 0;
  const { roles, hasPermission } = usePermissions();
  const { data, isLoading, isError, refetch } = useRectorDashboard(tenantId);

  const generatedLabel = useMemo(() => {
    if (!data?.generated_at) return t("ui.na");
    return formatRelative(data.generated_at);
  }, [data?.generated_at, t]);

  // Student dashboard
  if (roles.includes("student")) {
    return (
      <div className="space-y-6" data-testid="student-dashboard">
        <PageHeader title={t("nav.dashboard")} icon={LayoutDashboard} />
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-3">
          <Link href="/console/scheduling" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <CalendarDays className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">{t("dashboard.student.scheduleTitle")}</p>
            <p className="text-xs text-muted-foreground">{t("dashboard.student.scheduleDescription")}</p>
          </Link>
          <Link href="/console/grades" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">{t("dashboard.student.gradesTitle")}</p>
            <p className="text-xs text-muted-foreground">{t("dashboard.student.gradesDescription")}</p>
          </Link>
          <Link href="/console/transcripts" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <FileText className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">{t("dashboard.student.transcriptTitle")}</p>
            <p className="text-xs text-muted-foreground">{t("dashboard.student.transcriptDescription")}</p>
          </Link>
        </div>
      </div>
    );
  }

  // Teacher dashboard
  if (roles.includes("teacher")) {
    return (
      <div className="space-y-6" data-testid="teacher-dashboard">
        <PageHeader title={t("nav.dashboard")} icon={LayoutDashboard} />
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-3">
          <Link href="/console/students" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <GraduationCap className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">{t("dashboard.teacher.studentsTitle")}</p>
            <p className="text-xs text-muted-foreground">{t("dashboard.teacher.studentsDescription")}</p>
          </Link>
          <Link href="/console/grades" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">{t("dashboard.teacher.gradesTitle")}</p>
            <p className="text-xs text-muted-foreground">{t("dashboard.teacher.gradesDescription")}</p>
          </Link>
          <Link href="/console/enrollments" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <ClipboardCheck className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">{t("dashboard.teacher.requestsTitle")}</p>
            <p className="text-xs text-muted-foreground">{t("dashboard.teacher.requestsDescription")}</p>
          </Link>
        </div>
      </div>
    );
  }

  // Dean dashboard
  if (roles.includes("dean")) {
    return (
      <div className="space-y-6" data-testid="dean-dashboard">
        <PageHeader title={t("nav.dashboard")} icon={LayoutDashboard} />
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
          <Link href="/console/students" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <GraduationCap className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">{t("dashboard.dean.studentsTitle")}</p>
            <p className="text-xs text-muted-foreground">{t("dashboard.dean.studentsDescription")}</p>
          </Link>
          <Link href="/console/enrollments" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <BookOpen className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">{t("dashboard.dean.enrollmentsTitle")}</p>
            <p className="text-xs text-muted-foreground">{t("dashboard.dean.enrollmentsDescription")}</p>
          </Link>
          <Link href="/console/grades" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">{t("dashboard.dean.gradesTitle")}</p>
            <p className="text-xs text-muted-foreground">{t("dashboard.dean.gradesDescription")}</p>
          </Link>
          <Link href="/console/scheduling" className="rounded-lg border bg-card p-6 hover:bg-muted/40 transition-colors flex flex-col gap-2">
            <CalendarDays className="h-5 w-5 text-primary" />
            <p className="font-medium text-sm">{t("dashboard.dean.schedulingTitle")}</p>
            <p className="text-xs text-muted-foreground">{t("dashboard.dean.schedulingDescription")}</p>
          </Link>
        </div>
        {hasPermission(PERMISSIONS.METRICS_READ) && (
          <div>
            {isLoading && <DashboardSkeletonGrid />}
            {!isLoading && !isError && data && data.cards.length > 0 && (
              <div className="grid gap-4 grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
                {data.cards.map((card) => (
                  <KpiCard key={card.metric_key} title={card.title} value={card.value} trendPoints={card.trend_7d} severityLevel={(card.metadata_json?.severity_level as "warning" | "critical" | null) ?? null} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // Admin / operator / viewer — full executive dashboard
  if (!hasPermission(PERMISSIONS.DASHBOARD_READ)) return <AccessDenied />;

  return (
    <div className="space-y-6" data-testid="rector-dashboard-page">
      <PageHeader
        title={t("dashboard.executive.title")}
        description={t("dashboard.executive.dataDate")
          .replace("{date}", data?.snapshot_date ? formatDate(data.snapshot_date) : "-")
          .replace("{generated}", generatedLabel)}
        icon={LayoutDashboard}
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => { void refetch(); }}
            disabled={isLoading}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            {t("dashboard.executive.refresh")}
          </Button>
        }
      />

      {isLoading && <DashboardSkeletonGrid />}

      {isError && !isLoading && (
        <ErrorState
          title={t("dashboard.executive.loadFailedTitle")}
          message={t("dashboard.executive.loadFailedMessage")}
          onRetry={() => { void refetch(); }}
        />
      )}

      {!isLoading && !isError && (!data || data.cards.length === 0) && (
        <EmptyState
          title={t("dashboard.executive.noDataTitle")}
          description={t("dashboard.executive.noDataDescription")}
          action={
            <Button variant="outline" onClick={() => { void refetch(); }}>
              {t("dashboard.executive.retry")}
            </Button>
          }
        />
      )}

      {!isLoading && !isError && data && data.cards.length > 0 && (
        <div className="grid gap-4 grid-cols-1 md:grid-cols-2 xl:grid-cols-3" data-testid="kpi-cards-grid">
          {data.cards.map((card) => (
            <KpiCard key={card.metric_key} title={card.title} value={card.value} trendPoints={card.trend_7d} severityLevel={(card.metadata_json?.severity_level as "warning" | "critical" | null) ?? null} />
          ))}
        </div>
      )}

      {EXECUTIVE_KPI_SECTIONS.map((section) => (
        <ExecutiveKpiSection key={section.testId} section={section} />
      ))}

      <GovernanceCommandCenterContract tenantId={tenantId} />

      <GovernanceReportShell data={data} tenantId={tenantId} generatedLabel={generatedLabel} />

      <CrossDomainRiskHeatmap data={data} tenantId={tenantId} />

      <GovernanceAlertReviewQueue data={data} tenantId={tenantId} />

      <KpiEvidenceDrilldownContract data={data} tenantId={tenantId} />

      <RectorKpiDrilldownPanel tenantId={tenantId} />

      <AutomationOverviewWidget tenantId={tenantId} />
    </div>
  );
}
