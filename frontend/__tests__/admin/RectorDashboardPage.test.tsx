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
  Wave1KpiBar: ({ metricKeys }: { metricKeys: string[] }) => (
    <div data-testid="wave1-kpi-bar-mock" data-keys={metricKeys.join(",")} />
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
});
