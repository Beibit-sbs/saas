import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import AICopilotPage from "../../app/(admin)/console/ai/copilot/page";

const useAskCopilotMock = vi.fn();
const useAdminAuthMock = vi.fn();

vi.mock("../../modules/platform/ai/use-copilot", () => ({
  useAskCopilot: (...args: unknown[]) => useAskCopilotMock(...args),
}));

vi.mock("../../shared/auth/context", () => ({
  useAdminAuth: (...args: unknown[]) => useAdminAuthMock(...args),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: ReactNode }) => <>{children}</>,
  PermissionGate: ({ children }: { children: ReactNode }) => <>{children}</>,
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

vi.mock("@/app/components/LanguageProvider", async () => {
  const { en: commonEn } = await import("../../i18n/common/en");
  const { en: adminEn } = await import("../../i18n/admin/en");
  const dict = { ...commonEn, ...adminEn } as Record<string, string>;

  return {
    useLanguage: () => ({
      t: (key: string) => dict[key] ?? key,
    }),
  };
});

describe("AICopilotPage", () => {
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

  it("renders input and submit button", () => {
    useAskCopilotMock.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isError: false,
      data: undefined,
    });

    render(<AICopilotPage />);

    expect(screen.getByTestId("ai-copilot-page")).toBeInTheDocument();
    expect(screen.getByTestId("copilot-question-input")).toBeInTheDocument();
    expect(screen.getByTestId("copilot-submit-btn")).toBeInTheDocument();
  });

  it("submits question and renders structured answer", () => {
    const mutate = vi.fn();
    useAskCopilotMock.mockReturnValue({
      mutate,
      isPending: false,
      isError: false,
      data: {
        question: "How many students do we currently have?",
        summary: "Current Students: 42.",
        insights: [{ title: "Current Students", value: "42", explanation: "From KPI dashboard metric." }],
        sources: [{ source_type: "kpi", reference: "dashboard:total_students" }],
        warnings: [],
      },
    });

    render(<AICopilotPage />);

    fireEvent.change(screen.getByTestId("copilot-question-input"), {
      target: { value: "How many students do we currently have?" },
    });
    fireEvent.click(screen.getByTestId("copilot-submit-btn"));

    expect(mutate).toHaveBeenCalledWith({
      tenant_id: 1,
      question: "How many students do we currently have?",
      context: {},
    });

    expect(screen.getByTestId("copilot-answer-panel")).toBeInTheDocument();
    expect(screen.getByText("Current Students: 42.")).toBeInTheDocument();
    expect(screen.getByTestId("copilot-sources")).toHaveTextContent("kpi: dashboard:total_students");
  });

  it("shows error state on failure", () => {
    useAskCopilotMock.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isError: true,
      data: undefined,
    });

    render(<AICopilotPage />);

    expect(screen.getByText("Copilot request failed")).toBeInTheDocument();
  });

  it("renders recommendations section when present", () => {
    useAskCopilotMock.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isError: false,
      data: {
        question: "Are there students at risk?",
        summary: "1 student(s) flagged at risk.",
        insights: [],
        sources: [],
        warnings: [],
        recommendations: [
          {
            recommendation_type: "academic_risk_followup",
            title: "Follow up with at-risk students",
            priority: "medium",
            reason: "1 student(s) are flagged as academically at risk.",
            suggested_actions: [
              { action_type: "navigate", label: "View Academic Risk Report", target: "/console/analytics/academic-risk" },
            ],
          },
        ],
      },
    });

    render(<AICopilotPage />);

    expect(screen.getByTestId("copilot-recommendations")).toBeInTheDocument();
    expect(screen.getByTestId("copilot-recommendation-academic_risk_followup")).toBeInTheDocument();
    expect(screen.getByText("Follow up with at-risk students")).toBeInTheDocument();
    expect(screen.getByText("1 student(s) are flagged as academically at risk.")).toBeInTheDocument();
    const badge = screen.getByTestId("copilot-rec-priority-badge");
    expect(badge).toHaveTextContent("medium");
    const link = screen.getByTestId("copilot-rec-action-link");
    expect(link).toHaveTextContent("View Academic Risk Report");
    expect(link).toHaveAttribute("href", "/console/analytics/academic-risk");
  });

  it("does not render recommendations section when empty", () => {
    useAskCopilotMock.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isError: false,
      data: {
        question: "KPI?",
        summary: "All good.",
        insights: [],
        sources: [],
        warnings: [],
        recommendations: [],
      },
    });

    render(<AICopilotPage />);

    expect(screen.queryByTestId("copilot-recommendations")).not.toBeInTheDocument();
  });

  it("renders high priority recommendation with destructive badge", () => {
    useAskCopilotMock.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
      isError: false,
      data: {
        question: "Platform health?",
        summary: "20 jobs failed.",
        insights: [],
        sources: [],
        warnings: [],
        recommendations: [
          {
            recommendation_type: "failed_jobs_attention",
            title: "Investigate failed background jobs",
            priority: "high",
            reason: "20 background job(s) have failed.",
            suggested_actions: [
              { action_type: "navigate", label: "View Job Queue", target: "/console/platform/jobs" },
            ],
          },
        ],
      },
    });

    render(<AICopilotPage />);

    const badge = screen.getByTestId("copilot-rec-priority-badge");
    expect(badge).toHaveTextContent("high");
  });
});
