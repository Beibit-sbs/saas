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
  useBrainLearningEvaluation: () => ({
    data: {
      tenant_id: 1,
      total_decisions: 50,
      total_outcomes: 45,
      positive_outcomes: 30,
      negative_outcomes: 10,
      neutral_outcomes: 5,
      effectiveness_score: 0.75,
      policy_drift_detected: false,
      learning_ready: true,
      evaluated_at: "2026-04-30T10:00:00Z",
    },
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  }),
  useBrainPolicyProfile: () => ({
    data: {
      tenant_id: 1,
      autonomy_level: 2,
      require_approval_for_critical: true,
      default_approval_role: "approver",
      enable_ai_reasoning: true,
    },
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  }),
  useBrainLearningApply: () => ({
    mutateAsync: vi.fn(async (payload: any) => ({
      status: payload.dry_run ? "preview" : "applied",
      dry_run: payload.dry_run,
      learning_ready: true,
      changed: true,
      reason: "Improved decision effectiveness",
      preview_profile: payload.dry_run ? {
        tenant_id: 1,
        autonomy_level: 3,
        require_approval_for_critical: false,
        default_approval_role: "approver",
        enable_ai_reasoning: true,
      } : undefined,
      applied_by: payload.actor,
      applied_at: new Date().toISOString(),
      profile: !payload.dry_run ? {
        tenant_id: 1,
        autonomy_level: 3,
        require_approval_for_critical: false,
        default_approval_role: "approver",
        enable_ai_reasoning: true,
      } : undefined,
    })),
    isPending: false,
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

  // XVIII2 — Governance UI tests
  it("renders governance section when learning is ready", () => {
    render(<BrainIntelligencePage />);
    expect(screen.getByTestId("brain-governance")).toBeInTheDocument();
    expect(screen.getByText(/Adaptive Governance/i)).toBeInTheDocument();
    expect(screen.getByText(/Ready to Apply/i)).toBeInTheDocument();
  });

  it("displays current policy profile", () => {
    render(<BrainIntelligencePage />);
    const governanceSection = screen.getByTestId("brain-governance");
    expect(governanceSection).toBeInTheDocument();
    expect(screen.getByText(/Current Policy Profile/i)).toBeInTheDocument();
    expect(screen.getByText(/Autonomy Level/i)).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument(); // autonomy_level
    expect(screen.getByText(/AI Reasoning/i)).toBeInTheDocument();
    expect(screen.getByText(/Enabled/i)).toBeInTheDocument();
  });

  it("shows preview changes button when learning ready", () => {
    render(<BrainIntelligencePage />);
    const previewBtn = screen.getByTestId("btn-dry-run");
    expect(previewBtn).toBeInTheDocument();
    expect(previewBtn).toBeEnabled();
  });

  it("displays dry-run preview after clicking preview button", async () => {
    const { user } = await import("@testing-library/user-event");
    const u = user();
    render(<BrainIntelligencePage />);
    const previewBtn = screen.getByTestId("btn-dry-run");
    await u.click(previewBtn);
    // Preview should show suggested changes
    expect(screen.getByText(/Suggested Changes/i)).toBeInTheDocument();
    expect(screen.getByText(/Preview Changes/i)).toBeInTheDocument();
  });

  it("shows apply confirmation dialog", async () => {
    const { user } = await import("@testing-library/user-event");
    const u = user();
    render(<BrainIntelligencePage />);
    const previewBtn = screen.getByTestId("btn-dry-run");
    await u.click(previewBtn);
    const applyBtn = screen.getByTestId("btn-apply");
    await u.click(applyBtn);
    expect(screen.getByText(/Apply learning to policy profile/i)).toBeInTheDocument();
  });
});
