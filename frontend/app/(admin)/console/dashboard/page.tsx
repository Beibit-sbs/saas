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
import { useRectorDashboard } from "@/modules/platform/kpi/use-dashboard";
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
  data: { cards: Array<{ metric_key: string; title: string; value: number; trend_7d: unknown[]; metadata_json: Record<string, unknown> }> } | undefined;
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

      <GovernanceReportShell data={data} tenantId={tenantId} generatedLabel={generatedLabel} />

      <AutomationOverviewWidget tenantId={tenantId} />
    </div>
  );
}
