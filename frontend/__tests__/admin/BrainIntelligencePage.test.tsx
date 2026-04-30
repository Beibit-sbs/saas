import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import BrainIntelligencePage from "../../app/(admin)/console/ai/brain/intelligence/page";

let allowAccess = true;

const mockKPI = {
  tenant_id: 1,
  signal_volume: { total: 42, by_type: { "academic.risk": 10 }, high_severity: 5 },
  decision_quality: {
    total_decisions: 20,
    dispatched: 15,
    approval_pending: 2,
    dispatch_rate: 0.75,
    avg_confidence: 0.82,
    recommendation_trigger_eligible: false,
  },
  outcome_effectiveness: {
    total_outcomes: 10,
    positive: 7,
    negative: 2,
    neutral: 1,
    effectiveness_score: 0.7,
  },
  top_risk_signals: [
    { event_type: "academic.attendance_risk.detected", count: 8 },
    { event_type: "finance.payment.overdue", count: 4 },
  ],
  brain_health: {
    policy_autonomy_level: 2,
    ai_reasoning_enabled: true,
    requires_approval_for_critical: true,
    health_status: "healthy",
  },
};

const mockRecommendations = {
  tenant_id: 1,
  recommendations: [
    {
      recommendation_id: "rec-001",
      tenant_id: 1,
      category: "academic_risk",
      severity: "high",
      title: "High student dropout risk detected",
      description: "8 students showing attendance risk patterns.",
      suggested_action: "Initiate intervention workflow for at-risk students.",
      confidence: 0.88,
      triggered_by: ["academic.attendance_risk.detected"],
    },
  ],
  generated_at: "2026-04-30T10:00:00Z",
};

vi.mock("../../modules/brain-core/hooks", () => ({
  useBrainExecutiveKPI: () => ({
    data: mockKPI,
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  }),
  useBrainRecommendations: () => ({
    data: mockRecommendations,
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  }),
}));

vi.mock("../../shared/auth/context", () => ({
  useAdminAuth: () => ({ user: { tenantId: 1, sub: "admin@test.com" } }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: React.ReactNode }) =>
    allowAccess ? <>{children}</> : <div>Access Denied</div>,
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

vi.mock("../../shared/ui/page-states", () => ({
  LoadingState: ({ title }: { title: string }) => <div>{title}</div>,
  ErrorState: ({ title }: { title: string }) => <div>{title}</div>,
}));

vi.mock("../../shared/ui/page-header", () => ({
  PageHeader: ({ title, description }: { title: string; description: string }) => (
    <div>
      <h1>{title}</h1>
      <p>{description}</p>
    </div>
  ),
}));

vi.mock("../../shared/ui/badge", () => ({
  Badge: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
}));

vi.mock("../../shared/ui/button", () => ({
  Button: ({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) => (
    <button onClick={onClick}>{children}</button>
  ),
}));

describe("BrainIntelligencePage", () => {
  beforeEach(() => {
    allowAccess = true;
  });

  it("renders page title", () => {
    render(<BrainIntelligencePage />);
    expect(screen.getByText(/Brain Intelligence Dashboard/i)).toBeInTheDocument();
  });

  it("renders executive KPI summary cards", () => {
    render(<BrainIntelligencePage />);
    const kpiSection = screen.getByTestId("brain-kpi-summary");
    expect(kpiSection).toBeInTheDocument();
    // Signal volume total = 42
    expect(screen.getByText("42")).toBeInTheDocument();
    // Total decisions = 20
    expect(screen.getByText("20")).toBeInTheDocument();
  });

  it("renders top risk signals table", () => {
    render(<BrainIntelligencePage />);
    expect(screen.getByTestId("brain-top-risks")).toBeInTheDocument();
    expect(screen.getByText("academic.attendance_risk.detected")).toBeInTheDocument();
    expect(screen.getByText("finance.payment.overdue")).toBeInTheDocument();
  });

  it("renders proactive recommendations", () => {
    render(<BrainIntelligencePage />);
    expect(screen.getByTestId("brain-recommendations")).toBeInTheDocument();
    expect(screen.getByText(/High student dropout risk detected/i)).toBeInTheDocument();
    expect(screen.getByText(/Initiate intervention workflow/i)).toBeInTheDocument();
  });

  it("shows access denied without permission", () => {
    allowAccess = false;
    render(<BrainIntelligencePage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
