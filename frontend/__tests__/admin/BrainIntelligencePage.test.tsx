import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

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
  useBrainPolicyReasoning: () => ({
    data: {
      tenant_id: 1,
      reasoning: "Fallback reasoning recommends measured policy adjustments.",
      current_profile: {
        tenant_id: 1,
        autonomy_level: 2,
        require_approval_for_critical: true,
        default_approval_role: "approver",
        enable_ai_reasoning: true,
      },
      recommendations: [
        {
          recommendation: "Keep approval checks for critical decisions",
          rationale: "Negative outcomes remain below alert threshold but still require oversight.",
          risk_level: "low",
          expected_impact: "positive",
        },
      ],
      alternative_policies: [
        {
          name: "Balanced Policy",
          profile: {
            tenant_id: 1,
            autonomy_level: 2,
            require_approval_for_critical: true,
            default_approval_role: "approver",
            enable_ai_reasoning: true,
          },
          reasoning: "Moderate autonomy with review",
          adoption_risk: "low",
          rationale: "Balances speed and oversight",
        },
      ],
      effectiveness_metrics: {
        tenant_id: 1,
        total_outcomes: 10,
        positive: 7,
        neutral: 1,
        negative: 2,
        positive_rate: 0.7,
        negative_rate: 0.2,
      },
      timestamp: "2026-04-30T10:00:00Z",
    },
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  }),
  useBrainCrossTenantRecommendations: () => ({
    data: {
      tenant_id: 1,
      sample_size: 3,
      recommended_profile: {
        tenant_id: 1,
        autonomy_level: 2,
        require_approval_for_critical: true,
        default_approval_role: "approver",
        enable_ai_reasoning: true,
      },
      peer_benchmarks: {
        avg_positive_rate: 0.72,
        avg_negative_rate: 0.12,
        ai_reasoning_adoption_rate: 0.67,
        median_autonomy_level: 2,
      },
      rationale: ["Aggregated 3 peer tenants without exposing identifiers."],
      generated_at: "2026-04-30T10:00:00Z",
    },
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  }),
  useBrainPredictivePolicyOptimization: () => ({
    data: {
      tenant_id: 1,
      horizon_days: 14,
      risk_score: 0.34,
      forecast_band: "moderate",
      drivers: ["2 recent high-severity signals"],
      current_profile: {
        tenant_id: 1,
        autonomy_level: 2,
        require_approval_for_critical: true,
        default_approval_role: "approver",
        enable_ai_reasoning: true,
      },
      predicted_profile: {
        tenant_id: 1,
        autonomy_level: 2,
        require_approval_for_critical: true,
        default_approval_role: "approver",
        enable_ai_reasoning: true,
      },
      recommended_actions: ["Keep policy stable and continue monitoring peer benchmarks."],
      generated_at: "2026-04-30T10:00:00Z",
    },
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
  Button: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button {...props}>{children}</button>
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
    expect(screen.getAllByText(/Autonomy Level/i).length).toBeGreaterThan(0);
    expect(screen.getByText("2")).toBeInTheDocument(); // autonomy_level
    expect(screen.getAllByText(/AI Reasoning/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Enabled/i)).toBeInTheDocument();
  });

  it("shows preview changes button when learning ready", () => {
    render(<BrainIntelligencePage />);
    const previewBtn = screen.getByTestId("btn-dry-run");
    expect(previewBtn).toBeInTheDocument();
    expect(previewBtn).toBeEnabled();
  });

  it("displays dry-run preview after clicking preview button", async () => {
    const u = userEvent.setup();
    render(<BrainIntelligencePage />);
    const previewBtn = screen.getByTestId("btn-dry-run");
    await u.click(previewBtn);
    // Preview should show suggested changes
    expect(screen.getByText(/Suggested Changes/i)).toBeInTheDocument();
    expect(screen.getByTestId("btn-apply")).toBeInTheDocument();
  });

  it("shows apply confirmation dialog", async () => {
    const u = userEvent.setup();
    render(<BrainIntelligencePage />);
    const previewBtn = screen.getByTestId("btn-dry-run");
    await u.click(previewBtn);
    const applyBtn = screen.getByTestId("btn-apply");
    await u.click(applyBtn);
    expect(screen.getByText(/Apply learning to policy profile/i)).toBeInTheDocument();
  });

  it("renders policy reasoning section", () => {
    render(<BrainIntelligencePage />);
    expect(screen.getByTestId("brain-policy-reasoning")).toBeInTheDocument();
    expect(screen.getByText(/Policy Reasoning/i)).toBeInTheDocument();
    expect(screen.getByText(/Fallback reasoning recommends measured policy adjustments/i)).toBeInTheDocument();
  });

  it("renders peer learning and predictive optimization suite", () => {
    render(<BrainIntelligencePage />);
    expect(screen.getByTestId("brain-policy-optimization-suite")).toBeInTheDocument();
    expect(screen.getByText(/Peer Learning Benchmark/i)).toBeInTheDocument();
    expect(screen.getByText(/Predictive Policy Optimization/i)).toBeInTheDocument();
  });
});
