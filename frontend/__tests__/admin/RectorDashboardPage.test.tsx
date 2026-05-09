import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import RectorDashboardPage from "../../app/(admin)/console/dashboard/page";

const useRectorDashboardMock = vi.fn();
const useAdminAuthMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/platform/kpi/use-dashboard", () => ({
  useRectorDashboard: (...args: unknown[]) => useRectorDashboardMock(...args),
  useTenantKpiMetrics: () => ({ data: null, isLoading: false }),
}));

vi.mock("../../modules/platform/kpi/wave1-kpi-bar", () => ({
  Wave1KpiBar: ({ metricKeys, labels }: { metricKeys: string[]; labels: Record<string, string> }) => (
    <div
      data-testid="wave1-kpi-bar-mock"
      data-keys={metricKeys.join(",")}
      data-labels={Object.values(labels).join("|")}
    />
  ),
}));

vi.mock("../../shared/auth/context", () => ({
  useAdminAuth: (...args: unknown[]) => useAdminAuthMock(...args),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: ReactNode }) => <>{children}</>,
  PermissionGate: ({ children }: { children: ReactNode }) => <>{children}</>,
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

vi.mock("../../shared/hooks/use-permissions", () => ({
  usePermissions: () => ({
    hasPermission: () => allowAccess,
    hasAnyPermission: () => allowAccess,
    roles: allowAccess ? ["admin"] : [],
  }),
}));

vi.mock("../../modules/platform/automation/automation-overview-widget", () => ({
  AutomationOverviewWidget: () => <div data-testid="automation-overview-widget" />,
}));

vi.mock("@/app/components/LanguageProvider", () => ({
  useLanguage: () => ({
    t: (key: string) => {
      const dict: Record<string, string> = {
        "dashboard.executive.title": "University Executive Dashboard",
        "dashboard.executive.dataDate": "Data date: {date} | Generated: {generated}",
        "dashboard.executive.refresh": "Refresh",
        "dashboard.executive.loadFailedTitle": "Failed to load executive dashboard",
        "dashboard.executive.loadFailedMessage": "KPI data is temporarily unavailable.",
      };
      return dict[key] ?? key;
    },
  }),
}));

describe("RectorDashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useAdminAuthMock.mockReturnValue({
      user: { tenantId: 1, roles: ["admin"], permissions: [] },
      isLoading: false,
      isAuthenticated: true,
      refreshSession: vi.fn(),
      logout: vi.fn(),
      hasPermission: vi.fn(() => true),
      hasAnyPermission: vi.fn(() => true),
    });
  });

  it("renders dashboard header and metadata", () => {
    useRectorDashboardMock.mockReturnValue({
      data: {
        tenant_id: 1,
        snapshot_date: "2026-03-24",
        generated_at: "2026-03-24T08:42:00Z",
        source: "kpi_metrics_engine_v1",
        cards: [],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<RectorDashboardPage />);

    expect(screen.getByText("University Executive Dashboard")).toBeInTheDocument();
    expect(screen.getByText(/Data date:/)).toHaveTextContent("24 Mar 2026");
    expect(screen.getByText(/Generated:/)).toBeInTheDocument();
  });

  it("renders KPI cards from dashboard payload", () => {
    useRectorDashboardMock.mockReturnValue({
      data: {
        tenant_id: 1,
        snapshot_date: "2026-03-24",
        generated_at: "2026-03-24T08:42:00Z",
        source: "kpi_metrics_engine_v1",
        cards: [
          {
            metric_key: "total_students",
            title: "Total Students",
            value: 1200,
            trend_7d: [
              { snapshot_date: "2026-03-18", value: 1180 },
              { snapshot_date: "2026-03-24", value: 1200 },
            ],
            metadata_json: {},
          },
          {
            metric_key: "total_failed_jobs",
            title: "Failed Jobs",
            value: 4,
            trend_7d: [
              { snapshot_date: "2026-03-18", value: 2 },
              { snapshot_date: "2026-03-24", value: 4 },
            ],
            metadata_json: {},
          },
        ],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<RectorDashboardPage />);

    expect(screen.getByTestId("kpi-cards-grid")).toBeInTheDocument();
    expect(screen.getByText("Total Students")).toBeInTheDocument();
    expect(screen.getByText("Failed Jobs")).toBeInTheDocument();
    expect(screen.getByText(/1,?200/)).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
  });

  it("shows loading state while query is pending", () => {
    useRectorDashboardMock.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    });

    render(<RectorDashboardPage />);

    expect(screen.getByTestId("kpi-loading-grid")).toBeInTheDocument();
  });

  it("shows error state and refetch action", () => {
    const refetch = vi.fn();
    useRectorDashboardMock.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      refetch,
    });

    render(<RectorDashboardPage />);

    expect(screen.getByText("Failed to load executive dashboard")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(refetch).toHaveBeenCalledTimes(1);
  });

  it("shows access denied when read permission is missing", () => {
    allowAccess = false;
    useRectorDashboardMock.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<RectorDashboardPage />);

    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });

  it("renders Wave 1 KPI cards with severity indicators", () => {
    useRectorDashboardMock.mockReturnValue({
      data: {
        tenant_id: 1,
        snapshot_date: "2026-05-04",
        generated_at: "2026-05-04T10:00:00Z",
        source: "kpi_metrics_engine_v1",
        cards: [
          {
            metric_key: "high_risk_students_count",
            title: "High Risk Students",
            value: 18,
            trend_7d: [
              { snapshot_date: "2026-04-27", value: 12 },
              { snapshot_date: "2026-05-04", value: 18 },
            ],
            metadata_json: { severity_level: "warning", policy_pack: "student_success_wave1_v1" },
          },
          {
            metric_key: "critical_risk_students_count",
            title: "Critical Risk Students",
            value: 7,
            trend_7d: [
              { snapshot_date: "2026-04-27", value: 3 },
              { snapshot_date: "2026-05-04", value: 7 },
            ],
            metadata_json: { severity_level: "critical", policy_pack: "early_warning_wave1_v1" },
          },
          {
            metric_key: "course_fill_rate",
            title: "Course Fill Rate",
            value: 82,
            trend_7d: [
              { snapshot_date: "2026-04-27", value: 80 },
              { snapshot_date: "2026-05-04", value: 82 },
            ],
            metadata_json: {},
          },
        ],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<RectorDashboardPage />);

    expect(screen.getByTestId("kpi-cards-grid")).toBeInTheDocument();
    expect(screen.getByText("High Risk Students")).toBeInTheDocument();
    expect(screen.getByText("Critical Risk Students")).toBeInTheDocument();
    expect(screen.getByText("Course Fill Rate")).toBeInTheDocument();
    expect(screen.getByText("18")).toBeInTheDocument();
    expect(screen.getByText("7")).toBeInTheDocument();
    expect(screen.getByText("82")).toBeInTheDocument();
  });

  it("includes Wave 4 KPI section for dashboard contract consumption", () => {
    useRectorDashboardMock.mockReturnValue({
      data: {
        tenant_id: 1,
        snapshot_date: "2026-05-05",
        generated_at: "2026-05-05T10:00:00Z",
        source: "kpi_metrics_engine_v1",
        cards: [
          {
            metric_key: "total_students",
            title: "Total Students",
            value: 1000,
            trend_7d: [],
            metadata_json: {},
          },
        ],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<RectorDashboardPage />);
    const bars = screen.getAllByTestId("wave1-kpi-bar-mock");
    const wave4 = bars.find((node) => {
      const keys = node.getAttribute("data-keys") ?? "";
      return (
        keys.includes("academic_integrity_risk_count")
        && keys.includes("exam_proctoring_violations_count")
        && keys.includes("thesis_governance_risk_count")
        && keys.includes("research_ethics_review_cases_count")
        && keys.includes("integrity_case_resolution_sla_risk_count")
      );
    });
    expect(wave4).toBeTruthy();
  });

  it("includes A-017 consolidation KPI section with budget, billing, and integrity metrics", () => {
    useRectorDashboardMock.mockReturnValue({
      data: {
        tenant_id: 1,
        snapshot_date: "2026-05-08",
        generated_at: "2026-05-08T10:00:00Z",
        source: "kpi_metrics_engine_v1",
        cards: [
          {
            metric_key: "total_students",
            title: "Total Students",
            value: 1000,
            trend_7d: [],
            metadata_json: {},
          },
        ],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<RectorDashboardPage />);
    const bars = screen.getAllByTestId("wave1-kpi-bar-mock");
    const a017 = bars.find((node) => {
      const keys = node.getAttribute("data-keys") ?? "";
      return (
        keys.includes("budget_overrun_risk_count")
        && keys.includes("budget_overrun_amount_at_risk")
        && keys.includes("budget_health_score")
        && keys.includes("total_active_subscriptions")
        && keys.includes("delinquency_cases_active")
        && keys.includes("overdue_amount_at_risk")
        && keys.includes("delinquency_recovery_rate")
        && keys.includes("academic_integrity_review_cases_count")
        && keys.includes("exam_proctoring_violations_count")
        && keys.includes("exam_integrity_reviews_count")
        && keys.includes("exam_integrity_requires_approval_count")
        && keys.includes("research_ethics_review_cases_count")
        && keys.includes("research_ethics_requires_approval_count")
      );
    });
    expect(a017).toBeTruthy();
  });

  it("keeps A-017 consolidation section stable when optional dashboard payload is empty", () => {
    useRectorDashboardMock.mockReturnValue({
      data: {
        tenant_id: 1,
        snapshot_date: "2026-05-08",
        generated_at: "2026-05-08T10:00:00Z",
        source: "kpi_metrics_engine_v1",
        cards: [],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<RectorDashboardPage />);
    const bars = screen.getAllByTestId("wave1-kpi-bar-mock");
    const a017 = bars.find((node) => {
      const keys = node.getAttribute("data-keys") ?? "";
      return keys.includes("budget_overrun_risk_count") && keys.includes("research_ethics_requires_approval_count");
    });
    expect(a017).toBeTruthy();
  });

  it("includes A-018.5 campus operations consolidation section", () => {
    useRectorDashboardMock.mockReturnValue({
      data: {
        tenant_id: 1,
        snapshot_date: "2026-05-10",
        generated_at: "2026-05-10T10:00:00Z",
        source: "kpi_metrics_engine_v1",
        cards: [
          {
            metric_key: "total_students",
            title: "Total Students",
            value: 1000,
            trend_7d: [],
            metadata_json: {},
          },
        ],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<RectorDashboardPage />);
    const bars = screen.getAllByTestId("wave1-kpi-bar-mock");
    const a0185 = bars.find((node) => {
      const keys = node.getAttribute("data-keys") ?? "";
      return (
        keys.includes("scheduling_conflicts_count")
        && keys.includes("room_conflict_count")
        && keys.includes("access_denied_count")
        && keys.includes("unauthorized_attempts_count")
        && keys.includes("active_access_cards_count")
        && keys.includes("suspended_access_cards_count")
        && keys.includes("security_access_anomaly_count")
        && keys.includes("events_published_count")
        && keys.includes("events_started_count")
        && keys.includes("events_completed_count")
        && keys.includes("events_cancelled_count")
        && keys.includes("events_registration_full_count")
        && keys.includes("visitor_requests_pending_count")
        && keys.includes("visitors_checked_in_count")
        && keys.includes("visitor_unauthorized_attempts_count")
        && keys.includes("security_incidents_open_count")
        && keys.includes("security_incidents_escalated_count")
      );
    });
    expect(a0185).toBeTruthy();
  });

  it("keeps campus operations section stable when optional KPI values are missing", () => {
    useRectorDashboardMock.mockReturnValue({
      data: {
        tenant_id: 1,
        snapshot_date: "2026-05-10",
        generated_at: "2026-05-10T10:00:00Z",
        source: "kpi_metrics_engine_v1",
        cards: [],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<RectorDashboardPage />);
    const bars = screen.getAllByTestId("wave1-kpi-bar-mock");
    const campusOps = bars.find((node) => {
      const keys = node.getAttribute("data-keys") ?? "";
      return (
        keys.includes("scheduling_conflicts_count")
        && keys.includes("security_incidents_open_count")
        && keys.includes("security_incidents_resolved_count")
      );
    });
    expect(campusOps).toBeTruthy();
  });

  it("campus operations labels remain non-destructive and non-hardware", () => {
    useRectorDashboardMock.mockReturnValue({
      data: {
        tenant_id: 1,
        snapshot_date: "2026-05-10",
        generated_at: "2026-05-10T10:00:00Z",
        source: "kpi_metrics_engine_v1",
        cards: [],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<RectorDashboardPage />);
    const bars = screen.getAllByTestId("wave1-kpi-bar-mock");
    const campusOps = bars.find((node) => {
      const keys = node.getAttribute("data-keys") ?? "";
      return keys.includes("scheduling_conflicts_count") && keys.includes("security_incidents_resolved_count");
    });

    expect(campusOps).toBeTruthy();
    const labels = (campusOps?.getAttribute("data-labels") ?? "").toLowerCase();
    expect(labels).not.toContain("hardware");
    expect(labels).not.toContain("lockout");
    expect(labels).not.toContain("ban");
    expect(labels).not.toContain("disciplin");
  });

  it("includes A-019.5 completion metrics in campus operations section", () => {
    useRectorDashboardMock.mockReturnValue({
      data: {
        tenant_id: 1,
        snapshot_date: "2026-05-10",
        generated_at: "2026-05-10T10:00:00Z",
        source: "kpi_metrics_engine_v1",
        cards: [],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<RectorDashboardPage />);
    const bars = screen.getAllByTestId("wave1-kpi-bar-mock");
    const campusOps = bars.find((node) => {
      const keys = node.getAttribute("data-keys") ?? "";
      return (
        keys.includes("visitor_visits_completed_count")
        && keys.includes("visitor_visits_cancelled_count")
        && keys.includes("security_incidents_resolved_count")
        && keys.includes("security_incident_review_required_count")
        && keys.includes("security_high_risk_incidents_count")
      );
    });
    expect(campusOps).toBeTruthy();
  });

  it("uses authenticated tenant context for dashboard query", () => {
    useAdminAuthMock.mockReturnValue({
      user: { tenantId: 42, roles: ["admin"], permissions: [] },
      isLoading: false,
      isAuthenticated: true,
      refreshSession: vi.fn(),
      logout: vi.fn(),
      hasPermission: vi.fn(() => true),
      hasAnyPermission: vi.fn(() => true),
    });
    useRectorDashboardMock.mockReturnValue({
      data: {
        tenant_id: 42,
        snapshot_date: "2026-05-10",
        generated_at: "2026-05-10T10:00:00Z",
        source: "kpi_metrics_engine_v1",
        cards: [],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<RectorDashboardPage />);

    expect(useRectorDashboardMock).toHaveBeenCalledWith(42);
  });

  it("includes A-020.6 room allocation scheduling intelligence KPI section", () => {
    useRectorDashboardMock.mockReturnValue({
      data: {
        tenant_id: 1,
        snapshot_date: "2026-05-11",
        generated_at: "2026-05-11T10:00:00Z",
        source: "kpi_metrics_engine_v1",
        cards: [],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<RectorDashboardPage />);

    const bars = screen.getAllByTestId("wave1-kpi-bar-mock");
    const roomAllocation = bars.find((node) => {
      const keys = node.getAttribute("data-keys") ?? "";
      return (
        keys.includes("room_allocation_recommendations_count")
        && keys.includes("room_allocation_review_required_count")
        && keys.includes("room_allocation_no_viable_candidate_count")
        && keys.includes("room_allocation_candidate_evaluated_count")
        && keys.includes("room_capacity_mismatch_count")
        && keys.includes("room_equipment_mismatch_count")
        && keys.includes("room_computer_shortage_count")
        && keys.includes("room_type_mismatch_count")
      );
    });

    expect(roomAllocation).toBeTruthy();
  });

  it("renders non-destructive advisory wording for room allocation section", () => {
    useRectorDashboardMock.mockReturnValue({
      data: {
        tenant_id: 1,
        snapshot_date: "2026-05-11",
        generated_at: "2026-05-11T10:00:00Z",
        source: "kpi_metrics_engine_v1",
        cards: [],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<RectorDashboardPage />);

    expect(screen.getByText("Room Allocation / Scheduling Intelligence")).toBeInTheDocument();
    expect(screen.getByText(/Recommendation and Review required insights are evidence-only/i)).toBeInTheDocument();
    expect(screen.getByText(/No automatic assignment\. No auto-apply\./i)).toBeInTheDocument();

    const pageText = document.body.textContent?.toLowerCase() ?? "";
    expect(pageText).not.toContain("assigned automatically");
    expect(pageText).not.toContain("auto-applied");
    expect(pageText).not.toContain("room changed");
    expect(pageText).not.toContain("schedule updated automatically");
    expect(pageText).not.toContain("optimization applied");
    expect(pageText).not.toContain("fake optimization");
    expect(pageText).not.toContain("booking overridden");
  });

  it("renders the ministry-ready governance reporting shell with evidence-backed sections", () => {
    useRectorDashboardMock.mockReturnValue({
      data: {
        tenant_id: 1,
        snapshot_date: "2026-05-12",
        generated_at: "2026-05-12T10:00:00Z",
        source: "kpi_metrics_engine_v1",
        cards: [
          { metric_key: "total_students", title: "Total Students", value: 1200, trend_7d: [], metadata_json: {} },
          { metric_key: "academic_integrity_review_cases_count", title: "Academic Integrity Review Cases", value: 7, trend_7d: [], metadata_json: {} },
          { metric_key: "high_risk_students_count", title: "High Risk Students Count", value: 18, trend_7d: [], metadata_json: {} },
          { metric_key: "budget_overrun_risk_count", title: "Budget Overrun Risk Count", value: 4, trend_7d: [], metadata_json: {} },
          { metric_key: "scheduling_conflicts_count", title: "Scheduling Conflict Count", value: 9, trend_7d: [], metadata_json: {} },
          { metric_key: "security_incidents_open_count", title: "Security Incidents Open Count", value: 2, trend_7d: [], metadata_json: {} },
          { metric_key: "research_ethics_review_cases_count", title: "Research Ethics Review Cases", value: 3, trend_7d: [], metadata_json: {} },
          { metric_key: "room_allocation_review_required_count", title: "Room Allocation Review Required Count", value: 5, trend_7d: [], metadata_json: {} },
          { metric_key: "analytics_kpi_reads_total", title: "Analytics KPI Reads Total", value: 42, trend_7d: [], metadata_json: {} },
        ],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<RectorDashboardPage />);

    const shell = screen.getByTestId("ministry-governance-report-shell");
    expect(shell).toBeInTheDocument();
    expect(screen.getByText("Ministry / Governance Reporting")).toBeInTheDocument();
    expect(screen.getByText(/Read-only, tenant-scoped, evidence-backed reporting shell/i)).toBeInTheDocument();
    expect(screen.getByText(/Not submitted externally/i)).toBeInTheDocument();

    expect(screen.getByTestId("governance-report-section-institution-governance-summary")).toBeInTheDocument();
    expect(screen.getByTestId("governance-report-section-academic-governance")).toBeInTheDocument();
    expect(screen.getByTestId("governance-report-section-student-risk-intervention")).toBeInTheDocument();
    expect(screen.getByTestId("governance-report-section-finance-procurement-assets")).toBeInTheDocument();
    expect(screen.getByTestId("governance-report-section-campus-scheduling-room-allocation")).toBeInTheDocument();
    expect(screen.getByTestId("governance-report-section-security-visitor-operations")).toBeInTheDocument();
    expect(screen.getByTestId("governance-report-section-research-accreditation-quality")).toBeInTheDocument();
    expect(screen.getByTestId("governance-report-section-brain-review-required")).toBeInTheDocument();
    expect(screen.getByTestId("governance-report-section-evidence-gate-readiness")).toBeInTheDocument();
    expect(screen.getByTestId("governance-report-section-known-conditions-data-quality")).toBeInTheDocument();

    const shellText = shell.textContent?.toLowerCase() ?? "";
    expect(shellText).not.toContain("submitted to ministry");
    expect(shellText).not.toContain("official certified score");
    expect(shellText).not.toContain("auto disciplinary");
    expect(shellText).not.toContain("auto schedule change");
    expect(shellText).not.toContain("fake demo data");
  });

  it("keeps the ministry shell stable when optional KPI evidence is missing", () => {
    useRectorDashboardMock.mockReturnValue({
      data: {
        tenant_id: 1,
        snapshot_date: "2026-05-12",
        generated_at: "2026-05-12T10:00:00Z",
        source: "kpi_metrics_engine_v1",
        cards: [],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<RectorDashboardPage />);

    const shell = screen.getByTestId("ministry-governance-report-shell");
    expect(shell).toBeInTheDocument();
    expect(screen.getAllByText(/Not available/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Missing metrics show as Not available/i)).toBeInTheDocument();
  });

  it("renders cross-domain risk heatmap with supported governance domains and safe wording", () => {
    useRectorDashboardMock.mockReturnValue({
      data: {
        tenant_id: 1,
        snapshot_date: "2026-05-13",
        generated_at: "2026-05-13T10:00:00Z",
        source: "kpi_metrics_engine_v1",
        cards: [
          { metric_key: "academic_integrity_high_risk_count", title: "Academic Integrity High Risk Count", value: 2, trend_7d: [], metadata_json: {} },
          { metric_key: "academic_integrity_cases_pending_review", title: "Academic Integrity Cases Pending Review", value: 4, trend_7d: [], metadata_json: {} },
          { metric_key: "budget_overrun_risk_count", title: "Budget Overrun Risk Count", value: 3, trend_7d: [], metadata_json: {} },
          { metric_key: "active_finance_risk_signals_count", title: "Active Finance Risk Signals Count", value: 6, trend_7d: [], metadata_json: {} },
          { metric_key: "scheduling_conflicts_count", title: "Scheduling Conflict Count", value: 5, trend_7d: [], metadata_json: {} },
          { metric_key: "security_incidents_escalated_count", title: "Security Incidents Escalated Count", value: 2, trend_7d: [], metadata_json: {} },
          { metric_key: "security_incident_review_required_count", title: "Security Incident Review Required Count", value: 1, trend_7d: [], metadata_json: {} },
          { metric_key: "room_allocation_review_required_count", title: "Room Allocation Review Required Count", value: 3, trend_7d: [], metadata_json: {} },
          { metric_key: "room_capacity_mismatch_count", title: "Room Capacity Mismatch Count", value: 2, trend_7d: [], metadata_json: {} },
          { metric_key: "high_risk_students_count", title: "High Risk Students Count", value: 8, trend_7d: [], metadata_json: {} },
          { metric_key: "research_ethics_review_cases_count", title: "Research Ethics Review Cases", value: 2, trend_7d: [], metadata_json: {} },
          { metric_key: "exam_integrity_requires_approval_count", title: "Exam Integrity Requires Approval Count", value: 2, trend_7d: [], metadata_json: {} },
          { metric_key: "finance_operations_actionability_count", title: "Finance Operations Actionability Count", value: 3, trend_7d: [], metadata_json: {} },
        ],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<RectorDashboardPage />);

    const heatmap = screen.getByTestId("cross-domain-risk-heatmap");
    expect(heatmap).toBeInTheDocument();
    expect(screen.getByText("Cross-domain Risk Heatmap")).toBeInTheDocument();

    expect(screen.getByTestId("risk-heatmap-domain-academic-governance")).toBeInTheDocument();
    expect(screen.getByTestId("risk-heatmap-domain-finance-procurement-assets")).toBeInTheDocument();
    expect(screen.getByTestId("risk-heatmap-domain-campus-operations")).toBeInTheDocument();
    expect(screen.getByTestId("risk-heatmap-domain-visitor-security-operations")).toBeInTheDocument();
    expect(screen.getByTestId("risk-heatmap-domain-room-allocation-scheduling-intelligence")).toBeInTheDocument();
    expect(screen.getByTestId("risk-heatmap-domain-brain-review-required-actionability")).toBeInTheDocument();

    expect(screen.getByTestId("ministry-governance-report-shell")).toBeInTheDocument();
    expect(screen.getByText("Finance and Operations Health")).toBeInTheDocument();
    expect(screen.getByText("Academic Integrity and Governance")).toBeInTheDocument();

    const pageText = document.body.textContent?.toLowerCase() ?? "";
    expect(pageText).not.toContain("fake demo score");
    expect(pageText).not.toContain("official ministry certified score");
    expect(pageText).not.toContain("automatic disciplinary action");
    expect(pageText).not.toContain("automatic security lockout");
    expect(pageText).not.toContain("automatic room assignment");
    expect(pageText).not.toContain("automatic procurement approval");
    expect(pageText).not.toContain("destructive action");
  });

  it("renders unavailable state and data quality note when heatmap domain metrics are missing", () => {
    useAdminAuthMock.mockReturnValue({
      user: { tenantId: 77, roles: ["admin"], permissions: [] },
      isLoading: false,
      isAuthenticated: true,
      refreshSession: vi.fn(),
      logout: vi.fn(),
      hasPermission: vi.fn(() => true),
      hasAnyPermission: vi.fn(() => true),
    });
    useRectorDashboardMock.mockReturnValue({
      data: {
        tenant_id: 77,
        snapshot_date: "2026-05-13",
        generated_at: "2026-05-13T10:00:00Z",
        source: "kpi_metrics_engine_v1",
        cards: [],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<RectorDashboardPage />);

    expect(useRectorDashboardMock).toHaveBeenCalledWith(77);
    const heatmap = screen.getByTestId("cross-domain-risk-heatmap");
    expect(heatmap).toBeInTheDocument();
    expect(screen.getAllByText(/unavailable/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Domain evidence is unavailable in current tenant snapshot/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Data quality note:/i).length).toBeGreaterThan(0);
  });

  it("renders governance alert review queue as read-only evidence-backed human review surface", () => {
    useAdminAuthMock.mockReturnValue({
      user: { tenantId: 55, roles: ["admin"], permissions: [] },
      isLoading: false,
      isAuthenticated: true,
      refreshSession: vi.fn(),
      logout: vi.fn(),
      hasPermission: vi.fn(() => true),
      hasAnyPermission: vi.fn(() => true),
    });
    useRectorDashboardMock.mockReturnValue({
      data: {
        tenant_id: 55,
        snapshot_date: "2026-05-14",
        generated_at: "2026-05-14T10:00:00Z",
        source: "kpi_metrics_engine_v1",
        cards: [
          { metric_key: "academic_integrity_high_risk_count", title: "Academic Integrity High Risk Count", value: 2, trend_7d: [], metadata_json: {} },
          { metric_key: "academic_integrity_cases_pending_review", title: "Academic Integrity Cases Pending Review", value: 4, trend_7d: [], metadata_json: {} },
          { metric_key: "budget_overrun_risk_count", title: "Budget Overrun Risk Count", value: 3, trend_7d: [], metadata_json: {} },
          { metric_key: "budget_review_actions_count", title: "Budget Review Actions Count", value: 3, trend_7d: [], metadata_json: {} },
          { metric_key: "scheduling_conflicts_count", title: "Scheduling Conflict Count", value: 6, trend_7d: [], metadata_json: {} },
          { metric_key: "security_incident_review_required_count", title: "Security Incident Review Required Count", value: 2, trend_7d: [], metadata_json: {} },
          { metric_key: "security_high_risk_incidents_count", title: "Security High-Risk Incidents Count", value: 1, trend_7d: [], metadata_json: {} },
          { metric_key: "room_allocation_review_required_count", title: "Room Allocation Review Required Count", value: 2, trend_7d: [], metadata_json: {} },
          { metric_key: "room_allocation_no_viable_candidate_count", title: "Room Allocation No Viable Candidate Count", value: 1, trend_7d: [], metadata_json: {} },
          { metric_key: "finance_operations_actionability_count", title: "Finance Operations Actionability Count", value: 5, trend_7d: [], metadata_json: {} },
          { metric_key: "high_risk_students_count", title: "High Risk Students Count", value: 9, trend_7d: [], metadata_json: {} },
          { metric_key: "research_ethics_requires_approval_count", title: "Research Ethics Requires Approval", value: 2, trend_7d: [], metadata_json: {} },
        ],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<RectorDashboardPage />);

    expect(useRectorDashboardMock).toHaveBeenCalledWith(55);
    const queue = screen.getByTestId("governance-alert-review-queue");
    expect(queue).toBeInTheDocument();
    expect(screen.getByText("Governance Alert / Review Queue")).toBeInTheDocument();
    expect(screen.getByText(/Read-only queue/i)).toBeInTheDocument();
    expect(screen.getByText(/Human review required/i)).toBeInTheDocument();
    expect(screen.getByText(/Evidence-backed/i)).toBeInTheDocument();
    expect(screen.getByText(/No automatic action/i)).toBeInTheDocument();

    expect(screen.getByTestId("governance-alert-domain-academic-governance")).toBeInTheDocument();
    expect(screen.getByTestId("governance-alert-domain-finance-procurement-assets")).toBeInTheDocument();
    expect(screen.getByTestId("governance-alert-domain-campus-operations")).toBeInTheDocument();
    expect(screen.getByTestId("governance-alert-domain-security-visitor-operations")).toBeInTheDocument();
    expect(screen.getByTestId("governance-alert-domain-room-allocation-scheduling-intelligence")).toBeInTheDocument();
    expect(screen.getByTestId("governance-alert-domain-brain-review-required")).toBeInTheDocument();

    expect(screen.getByText("Cross-domain Risk Heatmap")).toBeInTheDocument();
    expect(screen.getByTestId("ministry-governance-report-shell")).toBeInTheDocument();
    expect(screen.getByText("Finance and Operations Health")).toBeInTheDocument();

    const pageText = document.body.textContent?.toLowerCase() ?? "";
    expect(pageText).not.toContain("fake alert");
    expect(pageText).not.toContain("fake demo value");
    expect(pageText).not.toContain("auto-approved");
    expect(pageText).not.toContain("auto-resolved");
    expect(pageText).not.toContain("destructive action");
    expect(pageText).not.toContain("submitted to ministry");
    expect(pageText).not.toContain("disciplinary action applied");
    expect(pageText).not.toContain("security lockout applied");
    expect(pageText).not.toContain("room assigned automatically");
    expect(pageText).not.toContain("schedule changed automatically");
    expect(pageText).not.toContain("procurement approved automatically");
    expect(pageText).not.toContain("action executed");
  });

  it("keeps governance alert queue stable with missing optional metrics and unavailable domain evidence", () => {
    useAdminAuthMock.mockReturnValue({
      user: { tenantId: 88, roles: ["admin"], permissions: [] },
      isLoading: false,
      isAuthenticated: true,
      refreshSession: vi.fn(),
      logout: vi.fn(),
      hasPermission: vi.fn(() => true),
      hasAnyPermission: vi.fn(() => true),
    });
    useRectorDashboardMock.mockReturnValue({
      data: {
        tenant_id: 88,
        snapshot_date: "2026-05-14",
        generated_at: "2026-05-14T10:00:00Z",
        source: "kpi_metrics_engine_v1",
        cards: [],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<RectorDashboardPage />);

    expect(useRectorDashboardMock).toHaveBeenCalledWith(88);
    const queue = screen.getByTestId("governance-alert-review-queue");
    expect(queue).toBeInTheDocument();
    expect(screen.getAllByText(/unavailable/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Data quality note:/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Source metrics: unavailable/i)).toBeInTheDocument();
  });

  it("renders KPI evidence drilldown contract with evidence-backed source lineage and human review wording", () => {
    useAdminAuthMock.mockReturnValue({
      user: { tenantId: 66, roles: ["admin"], permissions: [] },
      isLoading: false,
      isAuthenticated: true,
      refreshSession: vi.fn(),
      logout: vi.fn(),
      hasPermission: vi.fn(() => true),
      hasAnyPermission: vi.fn(() => true),
    });
    useRectorDashboardMock.mockReturnValue({
      data: {
        tenant_id: 66,
        snapshot_date: "2026-05-15",
        generated_at: "2026-05-15T10:00:00Z",
        source: "kpi_metrics_engine_v1",
        cards: [
          { metric_key: "academic_integrity_high_risk_count", title: "Academic Integrity High Risk Count", value: 2, trend_7d: [], metadata_json: {} },
          { metric_key: "academic_integrity_cases_pending_review", title: "Academic Integrity Cases Pending Review", value: 4, trend_7d: [], metadata_json: {} },
          { metric_key: "budget_overrun_risk_count", title: "Budget Overrun Risk Count", value: 3, trend_7d: [], metadata_json: {} },
          { metric_key: "budget_review_actions_count", title: "Budget Review Actions Count", value: 2, trend_7d: [], metadata_json: {} },
          { metric_key: "scheduling_conflicts_count", title: "Scheduling Conflict Count", value: 5, trend_7d: [], metadata_json: {} },
          { metric_key: "security_incident_review_required_count", title: "Security Incident Review Required Count", value: 1, trend_7d: [], metadata_json: {} },
          { metric_key: "room_allocation_review_required_count", title: "Room Allocation Review Required Count", value: 3, trend_7d: [], metadata_json: {} },
          { metric_key: "room_allocation_no_viable_candidate_count", title: "Room Allocation No Viable Candidate Count", value: 1, trend_7d: [], metadata_json: {} },
          { metric_key: "research_ethics_requires_approval_count", title: "Research Ethics Requires Approval", value: 2, trend_7d: [], metadata_json: {} },
        ],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<RectorDashboardPage />);

    expect(useRectorDashboardMock).toHaveBeenCalledWith(66);
    const drilldown = screen.getByTestId("kpi-evidence-drilldown-contract");
    expect(drilldown).toBeInTheDocument();
    expect(screen.getByText("KPI Evidence Drilldown Contract")).toBeInTheDocument();
    expect(screen.getByText(/Evidence-backed drilldown/i)).toBeInTheDocument();
    expect(screen.getByText(/Source metrics/i)).toBeInTheDocument();
    expect(screen.getByText(/Source domains/i)).toBeInTheDocument();
    expect(screen.getByText(/Human review/i)).toBeInTheDocument();
    expect(screen.getByText(/Read-only/i)).toBeInTheDocument();
    expect(screen.getByText(/No automatic action/i)).toBeInTheDocument();

    expect(screen.getByTestId("kpi-evidence-drilldown-domain-academic-governance")).toBeInTheDocument();
    expect(screen.getByTestId("kpi-evidence-drilldown-domain-finance-procurement-assets")).toBeInTheDocument();
    expect(screen.getByTestId("kpi-evidence-drilldown-domain-campus-operations")).toBeInTheDocument();
    expect(screen.getByTestId("kpi-evidence-drilldown-domain-security-visitor-operations")).toBeInTheDocument();
    expect(screen.getByTestId("kpi-evidence-drilldown-domain-room-allocation-scheduling-intelligence")).toBeInTheDocument();
    expect(screen.getByTestId("kpi-evidence-drilldown-domain-brain-review-required")).toBeInTheDocument();

    expect(screen.getByTestId("governance-alert-review-queue")).toBeInTheDocument();
    expect(screen.getByTestId("cross-domain-risk-heatmap")).toBeInTheDocument();
    expect(screen.getByTestId("ministry-governance-report-shell")).toBeInTheDocument();
    expect(screen.getByText("Finance and Operations Health")).toBeInTheDocument();

    const pageText = document.body.textContent?.toLowerCase() ?? "";
    expect(pageText).not.toContain("fake drilldown");
    expect(pageText).not.toContain("fabricated metric");
    expect(pageText).not.toContain("auto-approved");
    expect(pageText).not.toContain("auto-resolved");
    expect(pageText).not.toContain("submitted to ministry");
    expect(pageText).not.toContain("disciplinary action applied");
    expect(pageText).not.toContain("security lockout applied");
    expect(pageText).not.toContain("room assigned automatically");
    expect(pageText).not.toContain("schedule changed automatically");
    expect(pageText).not.toContain("procurement approved automatically");
    expect(pageText).not.toContain("action executed");
  });

  it("keeps KPI evidence drilldown stable when tenant metrics are unavailable", () => {
    useAdminAuthMock.mockReturnValue({
      user: { tenantId: 99, roles: ["admin"], permissions: [] },
      isLoading: false,
      isAuthenticated: true,
      refreshSession: vi.fn(),
      logout: vi.fn(),
      hasPermission: vi.fn(() => true),
      hasAnyPermission: vi.fn(() => true),
    });
    useRectorDashboardMock.mockReturnValue({
      data: {
        tenant_id: 99,
        snapshot_date: "2026-05-15",
        generated_at: "2026-05-15T10:00:00Z",
        source: "kpi_metrics_engine_v1",
        cards: [],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<RectorDashboardPage />);

    expect(useRectorDashboardMock).toHaveBeenCalledWith(99);
    const drilldown = screen.getByTestId("kpi-evidence-drilldown-contract");
    expect(drilldown).toBeInTheDocument();
    expect(screen.getAllByText(/unavailable/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Data quality note:/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Evidence unavailable in current tenant snapshot/i)).toBeInTheDocument();
    expect(screen.getByText(/Source metrics: unavailable/i)).toBeInTheDocument();
  });
});
