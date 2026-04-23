import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import type { ReactNode } from "react";

import AIRoutingPage from "../../app/(admin)/console/ai/routing/page";

const usePoliciesMock = vi.fn();
const useCreatePolicyMock = vi.fn();
const useUpdatePolicyMock = vi.fn();
const useDeletePolicyMock = vi.fn();
const useSelectionLogMock = vi.fn();

vi.mock("../../modules/ai-routing/hooks", () => ({
  useAIRoutingPolicies: (...args: unknown[]) => usePoliciesMock(...args),
  useCreateAIRoutingPolicy: (...args: unknown[]) => useCreatePolicyMock(...args),
  useUpdateAIRoutingPolicy: (...args: unknown[]) => useUpdatePolicyMock(...args),
  useDeleteAIRoutingPolicy: (...args: unknown[]) => useDeletePolicyMock(...args),
  useAIRoutingSelectionLog: (...args: unknown[]) => useSelectionLogMock(...args),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

const stubMutations = () => {
  useCreatePolicyMock.mockReturnValue({ mutate: vi.fn(), isPending: false });
  useUpdatePolicyMock.mockReturnValue({ mutate: vi.fn(), isPending: false });
  useDeletePolicyMock.mockReturnValue({ mutate: vi.fn(), isPending: false });
};

describe("AIRoutingPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    stubMutations();
  });

  it("renders page heading", () => {
    usePoliciesMock.mockReturnValue({ data: [], isLoading: false, isError: false, refetch: vi.fn() });
    useSelectionLogMock.mockReturnValue({ data: [] });

    render(<AIRoutingPage />);
    expect(screen.getByTestId("ai-routing-page")).toBeInTheDocument();
  });

  it("shows empty state when no policies", () => {
    usePoliciesMock.mockReturnValue({ data: [], isLoading: false, isError: false, refetch: vi.fn() });
    useSelectionLogMock.mockReturnValue({ data: [] });

    render(<AIRoutingPage />);
    expect(screen.getByTestId("no-policies")).toBeInTheDocument();
  });

  it("renders policies list", () => {
    usePoliciesMock.mockReturnValue({
      data: [
        {
          id: 1,
          tenant_id: 1,
          name: "Test Policy",
          strategy: "priority",
          enabled: true,
          rules: [{ task_type: "chat", target_model: "openai.gpt4", priority: 10 }],
          fallback_chain: ["openai.default.chat"],
          created_at: "2026-04-21T00:00:00Z",
          updated_at: "2026-04-21T00:00:00Z",
        },
      ],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
    useSelectionLogMock.mockReturnValue({ data: [] });

    render(<AIRoutingPage />);
    expect(screen.getByTestId("policy-row-1")).toBeInTheDocument();
    expect(screen.getByText("Test Policy")).toBeInTheDocument();
  });

  it("shows enabled/disabled badge", () => {
    usePoliciesMock.mockReturnValue({
      data: [
        {
          id: 2,
          tenant_id: 1,
          name: "Disabled Policy",
          strategy: "priority",
          enabled: false,
          rules: [],
          fallback_chain: [],
          created_at: "2026-04-21T00:00:00Z",
          updated_at: "2026-04-21T00:00:00Z",
        },
      ],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
    useSelectionLogMock.mockReturnValue({ data: [] });

    render(<AIRoutingPage />);
    const badge = screen.getByTestId("policy-status-2");
    expect(badge).toHaveTextContent("disabled");
  });

  it("shows selection log entries", () => {
    usePoliciesMock.mockReturnValue({ data: [], isLoading: false, isError: false, refetch: vi.fn() });
    useSelectionLogMock.mockReturnValue({
      data: [
        {
          timestamp: "2026-04-21T10:00:00Z",
          tenant_id: 1,
          model_key: "openai.default.chat",
          mode: "auto",
          selection: "priority_default",
          task_type: "chat",
        },
      ],
    });

    render(<AIRoutingPage />);
    expect(screen.getByTestId("log-entry-0")).toBeInTheDocument();
    expect(screen.getByText("openai.default.chat")).toBeInTheDocument();
  });

  it("opens create policy form on Add Policy click", () => {
    usePoliciesMock.mockReturnValue({ data: [], isLoading: false, isError: false, refetch: vi.fn() });
    useSelectionLogMock.mockReturnValue({ data: [] });

    render(<AIRoutingPage />);
    fireEvent.click(screen.getByTestId("add-policy-btn"));
    expect(screen.getByTestId("create-policy-form")).toBeInTheDocument();
    expect(screen.getByTestId("policy-name-input")).toBeInTheDocument();
  });

  it("calls createPolicy.mutate when form is submitted", () => {
    const mutate = vi.fn();
    useCreatePolicyMock.mockReturnValue({ mutate, isPending: false });
    usePoliciesMock.mockReturnValue({ data: [], isLoading: false, isError: false, refetch: vi.fn() });
    useSelectionLogMock.mockReturnValue({ data: [] });

    render(<AIRoutingPage />);
    fireEvent.click(screen.getByTestId("add-policy-btn"));
    fireEvent.change(screen.getByTestId("policy-name-input"), { target: { value: "New Policy" } });
    fireEvent.click(screen.getByTestId("save-policy-btn"));

    expect(mutate).toHaveBeenCalledWith(
      expect.objectContaining({ name: "New Policy", strategy: "priority", enabled: true }),
      expect.any(Object),
    );
  });
});
