import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import RectorDashboardPage from "../../app/(admin)/console/dashboard/page";

const useRectorDashboardMock = vi.fn();
const useAdminAuthMock = vi.fn();

vi.mock("../../modules/platform/kpi/use-dashboard", () => ({
  useRectorDashboard: (...args: unknown[]) => useRectorDashboardMock(...args),
}));

vi.mock("../../shared/auth/context", () => ({
  useAdminAuth: (...args: unknown[]) => useAdminAuthMock(...args),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: ReactNode }) => <>{children}</>,
  PermissionGate: ({ children }: { children: ReactNode }) => <>{children}</>,
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

vi.mock("../../modules/platform/automation/automation-overview-widget", () => ({
  AutomationOverviewWidget: () => <div data-testid="automation-overview-widget" />,
}));

describe("RectorDashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
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
});
