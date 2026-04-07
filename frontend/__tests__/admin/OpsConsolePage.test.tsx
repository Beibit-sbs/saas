import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import OpsConsolePage from "../../app/(admin)/console/ops/page";

const useOpsHealthMock = vi.fn();
const useOpsMetricsMock = vi.fn();

let allowAccess = true;

vi.mock("../../modules/platform/ops/use-ops-health", () => ({
  useOpsHealth: (...args: unknown[]) => useOpsHealthMock(...args),
}));

vi.mock("../../modules/platform/ops/use-ops-metrics", () => ({
  useOpsMetrics: (...args: unknown[]) => useOpsMetricsMock(...args),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: ReactNode }) => (
    allowAccess ? <>{children}</> : <div>Access Denied</div>
  ),
  PermissionGate: ({ children }: { children: ReactNode }) => <>{children}</>,
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

vi.mock("../../app/components/LanguageProvider", () => ({
  useLanguage: () => ({
    t: (key: string) => {
      const dict: Record<string, string> = {
        "nav.platformOps": "Platform Ops Console",
        "console.ops.description": "Live reliability and operations telemetry",
        "ops.health.overallHealth": "Overall Health",
        "ops.health.workerNotRequired": "Not required in this environment",
        "ops.unableToLoadSignals": "Unable to load ops signals",
        "ops.retry": "Retry",
        "ops.partialDataMode": "Partial data mode",
      };
      return dict[key] ?? key;
    },
  }),
}));

const HEALTH_DATA = {
  overall: "healthy" as const,
  api: "healthy" as const,
  db: "healthy" as const,
  worker: "healthy" as const,
  workerHeartbeatAt: "2026-03-24T10:00:00Z",
  updatedAt: "2026-03-24T10:00:00Z",
  errors: [],
};

const METRICS_DATA = {
  queue: {
    outboxBacklog: 11,
    eventQueueSize: 9,
    failedWebhooks: 1,
    deadWebhooks: 0,
    failedAutomationExecutions: 2,
    deadAutomationExecutions: 0,
    failedJobs: 3,
    deadJobs: 1,
    schedulerLastRun: "2026-03-24T09:58:00Z",
    retryBacklog: 4,
    deadCount: 1,
  },
  traffic: {
    requestsPerMinute: 120,
    p50LatencyMs: 32,
    p95LatencyMs: 110,
    p99LatencyMs: 240,
    http4xxCount: 5,
    http5xxCount: 1,
    developerApiErrorCount: 2,
    errorRate: 0.02,
  },
  runtime: {
    workerHeartbeat: "2026-03-24T09:59:30Z",
    workerHeartbeatAgeSeconds: 30,
    schedulerHeartbeatAgeSeconds: 120,
  },
  backup: {
    lastStatus: "ok",
    lastStartedAt: "2026-03-24T09:00:00Z",
    lastFinishedAt: "2026-03-24T09:01:00Z",
    lastError: null,
  },
  updatedAt: "2026-03-24T10:00:00Z",
  errors: [],
};

describe("OpsConsolePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;

    useOpsHealthMock.mockReturnValue({
      data: HEALTH_DATA,
      isLoading: false,
      isFetching: false,
      refetch: vi.fn(),
    });

    useOpsMetricsMock.mockReturnValue({
      data: METRICS_DATA,
      isLoading: false,
      isFetching: false,
      refetch: vi.fn(),
    });
  });

  it("renders health overview section", () => {
    render(<OpsConsolePage />);
    expect(screen.getByTestId("ops-health-section")).toBeInTheDocument();
    expect(screen.getByText(/overall health/i)).toBeInTheDocument();
  });

  it("renders metrics tiles", () => {
    render(<OpsConsolePage />);
    expect(screen.getByTestId("metric-outbox-backlog")).toBeInTheDocument();
    expect(screen.getByTestId("metric-rpm")).toBeInTheDocument();
    expect(screen.getByTestId("metric-p95")).toBeInTheDocument();
    expect(screen.getByTestId("metric-error-rate")).toBeInTheDocument();
    expect(screen.getByTestId("metric-retry-backlog")).toBeInTheDocument();
  });

  it("renders loading state", () => {
    useOpsHealthMock.mockReturnValue({
      data: undefined,
      isLoading: true,
      isFetching: true,
      refetch: vi.fn(),
    });
    useOpsMetricsMock.mockReturnValue({
      data: undefined,
      isLoading: true,
      isFetching: true,
      refetch: vi.fn(),
    });

    render(<OpsConsolePage />);
    expect(screen.getByTestId("ops-console-page")).toBeInTheDocument();
    expect(screen.getByText(/platform ops console/i)).toBeInTheDocument();
  });

  it("renders error state when both health and metrics are unavailable", () => {
    useOpsHealthMock.mockReturnValue({
      data: undefined,
      isLoading: false,
      isFetching: false,
      refetch: vi.fn(),
    });
    useOpsMetricsMock.mockReturnValue({
      data: undefined,
      isLoading: false,
      isFetching: false,
      refetch: vi.fn(),
    });

    render(<OpsConsolePage />);
    expect(screen.getByText(/unable to load ops signals/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("renders AccessDenied when user lacks ops.read", () => {
    allowAccess = false;
    render(<OpsConsolePage />);
    expect(screen.getByText("Access Denied")).toBeInTheDocument();
  });

  it("renders partial data when one metrics endpoint fails", () => {
    useOpsMetricsMock.mockReturnValue({
      data: {
        ...METRICS_DATA,
        traffic: {
          requestsPerMinute: null,
          p50LatencyMs: null,
          p95LatencyMs: null,
          p99LatencyMs: null,
          http4xxCount: null,
          http5xxCount: null,
          developerApiErrorCount: null,
          errorRate: null,
        },
        errors: ["latency: Request failed"],
      },
      isLoading: false,
      isFetching: false,
      refetch: vi.fn(),
    });

    render(<OpsConsolePage />);
    expect(screen.getByTestId("ops-health-section")).toBeInTheDocument();
    expect(screen.getByText(/partial data mode/i)).toBeInTheDocument();
    expect(screen.getByText(/latency: Request failed/i)).toBeInTheDocument();
  });

  it("renders skipped worker state with helper text", () => {
    useOpsHealthMock.mockReturnValue({
      data: {
        ...HEALTH_DATA,
        worker: "skipped" as const,
      },
      isLoading: false,
      isFetching: false,
      refetch: vi.fn(),
    });

    render(<OpsConsolePage />);
    expect(screen.getByText("Skipped")).toBeInTheDocument();
    expect(screen.getByText("Not required in this environment")).toBeInTheDocument();
  });
});