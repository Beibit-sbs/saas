import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

import { Wave1KpiBar } from "../../modules/platform/kpi/wave1-kpi-bar";

const useTenantKpiMetricsMock = vi.fn();
const useAdminAuthMock = vi.fn();

vi.mock("../../modules/platform/kpi/use-dashboard", () => ({
  useTenantKpiMetrics: (...args: unknown[]) => useTenantKpiMetricsMock(...args),
}));

vi.mock("../../shared/auth/context", () => ({
  useAdminAuth: (...args: unknown[]) => useAdminAuthMock(...args),
}));

const KEYS = ["high_risk_students_count", "critical_risk_students_count", "intervention_auto_created_count"];
const LABELS: Record<string, string> = {
  high_risk_students_count: "High Risk Students",
  critical_risk_students_count: "Critical Risk Students",
  intervention_auto_created_count: "Auto-Triggered",
};

describe("Wave1KpiBar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAdminAuthMock.mockReturnValue({ user: { tenantId: 1 } });
  });

  it("shows loading skeletons while fetching", () => {
    useTenantKpiMetricsMock.mockReturnValue({ data: undefined, isLoading: true });

    render(<Wave1KpiBar metricKeys={KEYS} labels={LABELS} />);

    expect(screen.getByTestId("wave1-kpi-bar-loading")).toBeInTheDocument();
  });

  it("renders metric chips with values when data is available", () => {
    useTenantKpiMetricsMock.mockReturnValue({
      isLoading: false,
      data: [
        { metric_key: "high_risk_students_count", metric_value: 18 },
        { metric_key: "critical_risk_students_count", metric_value: 7 },
        { metric_key: "intervention_auto_created_count", metric_value: 3 },
      ],
    });

    render(<Wave1KpiBar metricKeys={KEYS} labels={LABELS} />);

    expect(screen.getByTestId("wave1-kpi-bar")).toBeInTheDocument();
    expect(screen.getByText("High Risk Students")).toBeInTheDocument();
    expect(screen.getByText("Critical Risk Students")).toBeInTheDocument();
    expect(screen.getByText("Auto-Triggered")).toBeInTheDocument();
    expect(screen.getByText("18")).toBeInTheDocument();
    expect(screen.getByText("7")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("shows em-dash for metrics not present in the snapshot", () => {
    useTenantKpiMetricsMock.mockReturnValue({
      isLoading: false,
      data: [
        { metric_key: "high_risk_students_count", metric_value: 5 },
        // critical_risk_students_count and intervention_auto_created_count missing
      ],
    });

    render(<Wave1KpiBar metricKeys={KEYS} labels={LABELS} />);

    expect(screen.getByText("5")).toBeInTheDocument();
    // Two missing metrics should show em-dash
    expect(screen.getAllByText("—")).toHaveLength(2);
  });

  it("renders nothing when data is null (returns null)", () => {
    useTenantKpiMetricsMock.mockReturnValue({ isLoading: false, data: null });

    const { container } = render(<Wave1KpiBar metricKeys={KEYS} labels={LABELS} />);

    expect(container.firstChild).toBeNull();
  });

  it("passes correct tenantId from auth context to useTenantKpiMetrics", () => {
    useAdminAuthMock.mockReturnValue({ user: { tenantId: 42 } });
    useTenantKpiMetricsMock.mockReturnValue({ isLoading: false, data: [] });

    render(<Wave1KpiBar metricKeys={KEYS} labels={LABELS} />);

    expect(useTenantKpiMetricsMock).toHaveBeenCalledWith(42);
  });
});
