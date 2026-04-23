import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import AICostPage from "../../app/(admin)/console/ai/cost/page";

const useSummaryMock = vi.fn();
const useProjectionMock = vi.fn();
const useAnomaliesMock = vi.fn();
const useBudgetStatusMock = vi.fn();
const useSLOComplianceMock = vi.fn();
const useSLOViolationsMock = vi.fn();

vi.mock("../../modules/ai-cost/hooks", () => ({
  useAICostSummary: (...args: unknown[]) => useSummaryMock(...args),
  useAICostProjection: (...args: unknown[]) => useProjectionMock(...args),
  useAICostAnomalies: (...args: unknown[]) => useAnomaliesMock(...args),
  useAICostBudgetStatus: (...args: unknown[]) => useBudgetStatusMock(...args),
  useAISLOCompliance: (...args: unknown[]) => useSLOComplianceMock(...args),
  useAISLOViolations: (...args: unknown[]) => useSLOViolationsMock(...args),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

const EMPTY_SUMMARY = {
  tenant_id: 1,
  requests_total: 0,
  success_count: 0,
  degraded_count: 0,
  failed_count: 0,
  total_tokens: 0,
  avg_latency_ms: 0,
  estimated_cost_usd: 0,
  budget_limit_usd: 1000,
  budget_utilization_pct: 0,
  budget_alert: false,
  budget_hard_cap: false,
  anomaly_detected: false,
  anomaly_score_z: 0,
  anomaly_reason: null,
  models: [],
};

const stubDefaults = () => {
  useSummaryMock.mockReturnValue({ data: undefined, isLoading: false, isError: false, refetch: vi.fn() });
  useProjectionMock.mockReturnValue({ data: undefined });
  useAnomaliesMock.mockReturnValue({ data: [] });
  useBudgetStatusMock.mockReturnValue({ data: [] });
  useSLOComplianceMock.mockReturnValue({ data: [] });
  useSLOViolationsMock.mockReturnValue({ data: [] });
};

describe("AICostPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    stubDefaults();
  });

  it("renders page heading", () => {
    render(<AICostPage />);
    expect(screen.getByText(/AI Cost & Performance Governance/i)).toBeTruthy();
  });

  it("shows loading state when loading", () => {
    useSummaryMock.mockReturnValue({ data: undefined, isLoading: true, isError: false, refetch: vi.fn() });
    render(<AICostPage />);
    expect(screen.getByTestId("ai-cost-page")).toBeTruthy();
  });

  it("renders usage summary when data is available", () => {
    useSummaryMock.mockReturnValue({
      data: { ...EMPTY_SUMMARY, requests_total: 42, estimated_cost_usd: 3.14, budget_limit_usd: 500 },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
    render(<AICostPage />);
    expect(screen.getByTestId("requests-total").textContent).toBe("42");
    expect(screen.getByTestId("estimated-cost").textContent).toContain("3.14");
    expect(screen.getByTestId("budget-limit").textContent).toContain("500.00");
  });

  it("shows budget alert banner when budget_alert is true", () => {
    useSummaryMock.mockReturnValue({
      data: { ...EMPTY_SUMMARY, budget_alert: true, budget_utilization_pct: 92 },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
    render(<AICostPage />);
    expect(screen.getByTestId("budget-alert-banner")).toBeTruthy();
  });

  it("shows anomaly alert banner when anomaly_detected is true", () => {
    useSummaryMock.mockReturnValue({
      data: { ...EMPTY_SUMMARY, anomaly_detected: true, anomaly_reason: "Spike in cost" },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
    render(<AICostPage />);
    expect(screen.getByTestId("anomaly-alert-banner")).toBeTruthy();
    expect(screen.getByTestId("anomaly-alert-banner").textContent).toContain("Spike in cost");
  });

  it("renders projection section with costs", () => {
    useSummaryMock.mockReturnValue({
      data: EMPTY_SUMMARY,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
    useProjectionMock.mockReturnValue({
      data: {
        tenant_id: 1,
        period: "daily",
        elapsed_requests: 100,
        current_cost_usd: 10.5,
        projected_cost_usd: 21.0,
        projection_basis: "linear_daily",
      },
    });
    render(<AICostPage />);
    expect(screen.getByTestId("projection-section")).toBeTruthy();
    expect(screen.getByTestId("current-cost").textContent).toContain("10.50");
    expect(screen.getByTestId("projected-cost").textContent).toContain("21.00");
  });

  it("shows no SLO policies message when compliance list is empty", () => {
    useSummaryMock.mockReturnValue({
      data: EMPTY_SUMMARY,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
    useSLOComplianceMock.mockReturnValue({ data: [] });
    render(<AICostPage />);
    expect(screen.getByTestId("no-slo-policies")).toBeTruthy();
  });

  it("renders SLO compliance table with violation badge", () => {
    useSummaryMock.mockReturnValue({
      data: EMPTY_SUMMARY,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
    useSLOComplianceMock.mockReturnValue({
      data: [
        {
          tenant_id: 1,
          model_key: "openai.default.chat",
          requests_total: 200,
          p95_latency_ms_observed: 5000,
          error_rate_pct_observed: 12.0,
          p95_latency_ms_target: 2000,
          max_error_rate_pct_target: 5.0,
          latency_compliant: false,
          error_rate_compliant: false,
          compliant: false,
        },
      ],
    });
    useSLOViolationsMock.mockReturnValue({
      data: [
        {
          tenant_id: 1,
          model_key: "openai.default.chat",
          requests_total: 200,
          p95_latency_ms_observed: 5000,
          error_rate_pct_observed: 12.0,
          p95_latency_ms_target: 2000,
          max_error_rate_pct_target: 5.0,
          latency_compliant: false,
          error_rate_compliant: false,
          compliant: false,
          violation_types: ["latency", "error_rate"],
        },
      ],
    });
    render(<AICostPage />);
    expect(screen.getByTestId("slo-compliance-table")).toBeTruthy();
    expect(screen.getByTestId("slo-violations-banner")).toBeTruthy();
    expect(screen.getByTestId("slo-violation-badge")).toBeTruthy();
  });
});
