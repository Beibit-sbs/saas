import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import AICopilotPage from "../../app/(admin)/console/ai/copilot/page";

const useAskCopilotMock = vi.fn();

vi.mock("../../modules/platform/ai/use-copilot", () => ({
  useAskCopilot: (...args: unknown[]) => useAskCopilotMock(...args),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: ReactNode }) => <>{children}</>,
  PermissionGate: ({ children }: { children: ReactNode }) => <>{children}</>,
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

describe("AICopilotPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
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
});
