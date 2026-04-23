import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import BrainCorePage from "../../app/(admin)/console/ai/brain/page";

const useAdminAuthMock = vi.fn();
const useBrainDecisionsMock = vi.fn();
const useBrainOutcomesMock = vi.fn();
const useBrainExplanationMock = vi.fn();
const useBrainPolicyProfileMock = vi.fn();
const useBrainPolicyTuningMock = vi.fn();
const useApplyBrainPolicyTuningMock = vi.fn();

let allowAccess = true;

vi.mock("../../shared/auth/context", () => ({
  useAdminAuth: (...args: unknown[]) => useAdminAuthMock(...args),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: ReactNode }) => (
    allowAccess ? <>{children}</> : <div>Access Denied</div>
  ),
}));

vi.mock("../../shared/ui/confirm-action-dialog", () => ({
  ConfirmActionDialog: ({ trigger }: { trigger: ReactNode }) => <>{trigger}</>,
}));

vi.mock("../../shared/ui/use-toast", () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

vi.mock("../../modules/brain-core/hooks", () => ({
  useBrainDecisions: (...args: unknown[]) => useBrainDecisionsMock(...args),
  useBrainOutcomes: (...args: unknown[]) => useBrainOutcomesMock(...args),
  useBrainExplanation: (...args: unknown[]) => useBrainExplanationMock(...args),
  useBrainPolicyProfile: (...args: unknown[]) => useBrainPolicyProfileMock(...args),
  useBrainPolicyTuning: (...args: unknown[]) => useBrainPolicyTuningMock(...args),
  useApplyBrainPolicyTuning: (...args: unknown[]) => useApplyBrainPolicyTuningMock(...args),
}));

describe("BrainCorePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;

    useAdminAuthMock.mockReturnValue({
      user: { tenantId: 101, sub: "admin@tenant" },
    });

    useBrainDecisionsMock.mockReturnValue({
      data: {
        items: [
          {
            decision_id: "dec-1-abcdef",
            decision_type: "risk",
            priority: "critical",
            status: "approval_pending",
            created_at: "2026-04-22T08:10:00Z",
          },
        ],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    useBrainOutcomesMock.mockReturnValue({
      data: {
        items: [
          {
            outcome_id: "out-1",
            decision_id: "dec-1-abcdef",
            outcome_type: "completed",
            effectiveness: "positive",
            created_at: "2026-04-22T09:10:00Z",
          },
        ],
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    useBrainExplanationMock.mockReturnValue({
      data: {
        summary: "Decision summary",
        factors: ["attendance_rate=0.35"],
        policy_notes: ["approval role = dean"],
        expected_outcome: "Actions dispatched",
      },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    useBrainPolicyProfileMock.mockReturnValue({
      data: {
        autonomy_level: 2,
        require_approval_for_critical: true,
        default_approval_role: "dean",
      },
      refetch: vi.fn(),
    });

    useBrainPolicyTuningMock.mockReturnValue({
      data: {
        changed: true,
        reason: "high_negative_outcome_rate",
        suggested_profile: {
          autonomy_level: 1,
          require_approval_for_critical: true,
        },
        metrics: {
          total_outcomes: 4,
          positive_rate: 0.25,
          negative: 3,
          negative_rate: 0.75,
        },
      },
      refetch: vi.fn(),
    });

    useApplyBrainPolicyTuningMock.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    });
  });

  it("renders decisions, explanation, and outcomes sections", () => {
    render(<BrainCorePage />);

    expect(screen.getByText("Brain Core Decision Center")).toBeInTheDocument();
    expect(screen.getByText("Decision summary")).toBeInTheDocument();
    expect(screen.getByText("Outcomes")).toBeInTheDocument();
    expect(screen.getByText("Apply suggestion")).toBeInTheDocument();
  });

  it("renders Access Denied when permission is missing", () => {
    allowAccess = false;

    render(<BrainCorePage />);

    expect(screen.getByText("Access Denied")).toBeInTheDocument();
  });
});
