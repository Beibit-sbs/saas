import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import AutomationRulesPage from "../../app/(admin)/console/automation/page";
import AutomationExecutionsPage from "../../app/(admin)/console/automation/executions/page";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const useAutomationRulesMock = vi.fn();
const useAutomationExecutionsMock = vi.fn();
const useCreateAutomationRuleMock = vi.fn();
const useUpdateAutomationRuleMock = vi.fn();
const useToastMock = vi.fn();

vi.mock("../../modules/platform/automation/use-rules", () => ({
  useAutomationRules: (...args: unknown[]) => useAutomationRulesMock(...args),
  useUpdateAutomationRule: (...args: unknown[]) => useUpdateAutomationRuleMock(...args),
}));

vi.mock("../../modules/platform/automation/use-executions", () => ({
  useAutomationExecutions: (...args: unknown[]) => useAutomationExecutionsMock(...args),
}));

vi.mock("../../modules/platform/automation/create-rule", () => ({
  useCreateAutomationRule: (...args: unknown[]) => useCreateAutomationRuleMock(...args),
}));

vi.mock("../../shared/ui/use-toast", () => ({
  useToast: (...args: unknown[]) => useToastMock(...args),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: ReactNode }) => <>{children}</>,
  PermissionGate: ({ children }: { children: ReactNode }) => <>{children}</>,
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const MOCK_RULES = [
  {
    id: 1,
    tenant_id: 1,
    name: "Alert on Failed Grade",
    description: "Send notification when a grade below threshold is submitted",
    event_type: "grade.submitted",
    condition_json: { field: "grade_points", operator: "<", value: 50 },
    actions_json: [{ type: "send_notification", channel: "email", template: "low_grade_alert" }],
    is_active: true,
    created_at: "2026-03-20T10:00:00Z",
    updated_at: "2026-03-20T10:00:00Z",
    version: 1,
  },
  {
    id: 2,
    tenant_id: 1,
    name: "Onboard New Student",
    description: "",
    event_type: "student.created",
    condition_json: {},
    actions_json: [{ type: "create_task", job_type: "send_welcome_email", max_retries: 3 }],
    is_active: false,
    created_at: "2026-03-21T10:00:00Z",
    updated_at: "2026-03-21T10:00:00Z",
    version: 1,
  },
];

const MOCK_EXECUTIONS = [
  {
    id: 10,
    tenant_id: 1,
    rule_id: 1,
    event_id: 500,
    status: "completed",
    result_json: { actions_executed: 1 },
    error_message: null,
    executed_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
  },
  {
    id: 11,
    tenant_id: 1,
    rule_id: 1,
    event_id: 501,
    status: "failed",
    result_json: {},
    error_message: "Notification dispatch failed",
    executed_at: "2026-03-19T08:00:00Z",
    created_at: "2026-03-19T08:00:00Z",
  },
];

// ---------------------------------------------------------------------------
// Automation Rules Page
// ---------------------------------------------------------------------------

describe("AutomationRulesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    useCreateAutomationRuleMock.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    });
    useToastMock.mockReturnValue({
      toast: vi.fn(),
    });
    useUpdateAutomationRuleMock.mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue({}),
      isPending: false,
    });
  });

  it("renders rules page header and table with data", () => {
    useAutomationRulesMock.mockReturnValue({
      data: MOCK_RULES,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<AutomationRulesPage />);

    expect(screen.getByTestId("automation-rules-page")).toBeInTheDocument();
    expect(screen.getByText("Automation Rules")).toBeInTheDocument();
    expect(screen.getByText("Alert on Failed Grade")).toBeInTheDocument();
    expect(screen.getByText("Onboard New Student")).toBeInTheDocument();
  });

  it("shows event type badges in the table", () => {
    useAutomationRulesMock.mockReturnValue({
      data: MOCK_RULES,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<AutomationRulesPage />);

    expect(screen.getByText("grade.submitted")).toBeInTheDocument();
    expect(screen.getByText("student.created")).toBeInTheDocument();
  });

  it("renders toggle switch for rule activation", () => {
    useAutomationRulesMock.mockReturnValue({
      data: MOCK_RULES,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
    localStorage.setItem("user_permissions", JSON.stringify(["automation.write"]));

    render(<AutomationRulesPage />);

    expect(screen.getByTestId("toggle-rule-1")).toBeInTheDocument();
    expect(screen.getByTestId("toggle-rule-2")).toBeInTheDocument();
  });

  it("switch is disabled without automation.write permission", () => {
    useAutomationRulesMock.mockReturnValue({
      data: MOCK_RULES,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
    localStorage.setItem("user_permissions", JSON.stringify([]));

    render(<AutomationRulesPage />);

    const toggle1 = screen.getByTestId("toggle-rule-1");
    expect(toggle1).toBeDisabled();
  });

  it("confirm dialog appears when toggling a switch", () => {
    useAutomationRulesMock.mockReturnValue({
      data: MOCK_RULES,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
    localStorage.setItem("user_permissions", JSON.stringify(["automation.write"]));

    render(<AutomationRulesPage />);

    fireEvent.click(screen.getByTestId("toggle-rule-1"));
    expect(screen.getByText("Change rule status?")).toBeInTheDocument();
  });

  it("mutation succeeds and calls mutateAsync with correct params", async () => {
    const mutateStub = vi.fn().mockResolvedValue({ id: 1, is_active: false });
    useUpdateAutomationRuleMock.mockReturnValue({
      mutateAsync: mutateStub,
      isPending: false,
    });
    useAutomationRulesMock.mockReturnValue({
      data: MOCK_RULES,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
    localStorage.setItem("user_permissions", JSON.stringify(["automation.write"]));

    render(<AutomationRulesPage />);

    fireEvent.click(screen.getByTestId("toggle-rule-1"));

    // Get the button that appears in the dialog (the confirm button)
    const buttons = screen.queryAllByRole("button");
    const confirmButton = buttons.find((btn) => btn.textContent === "Deactivate");
    if (confirmButton) {
      fireEvent.click(confirmButton);
    }

    // Wait for async mutation
    await new Promise((resolve) => setTimeout(resolve, 100));

    expect(mutateStub).toHaveBeenCalledWith({ id: 1, is_active: false });
  });

  it("shows success toast message on rule activation", async () => {
    const toastFn = vi.fn();
    useToastMock.mockReturnValue({
      toast: toastFn,
    });
    useUpdateAutomationRuleMock.mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue({ id: 1, is_active: true }),
      isPending: false,
    });
    useAutomationRulesMock.mockReturnValue({
      data: MOCK_RULES,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
    localStorage.setItem("user_permissions", JSON.stringify(["automation.write"]));

    render(<AutomationRulesPage />);

    fireEvent.click(screen.getByTestId("toggle-rule-1"));

    // Find and click the confirm button in the dialog
    const buttons = screen.queryAllByRole("button");
    const confirmButton = buttons.find((btn) => btn.textContent === "Deactivate");
    if (confirmButton) {
      fireEvent.click(confirmButton);
    }

    // Wait a bit for async mutation to complete
    await new Promise((resolve) => setTimeout(resolve, 150));

    expect(toastFn).toHaveBeenCalledWith(
      expect.objectContaining({
        variant: "success",
        title: "Rule deactivated",
      }),
    );
  });

  it("shows loading skeleton while query is pending", () => {
    useAutomationRulesMock.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    });

    render(<AutomationRulesPage />);

    expect(screen.getByTestId("automation-rules-page")).toBeInTheDocument();
    // DataTable renders skeleton rows during loading
    expect(screen.queryByText("Alert on Failed Grade")).not.toBeInTheDocument();
  });

  it("shows error state when query fails and retries", () => {
    const refetch = vi.fn();
    useAutomationRulesMock.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      refetch,
    });

    render(<AutomationRulesPage />);

    expect(screen.getByText("Failed to load automation rules")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /retry/i }));
    expect(refetch).toHaveBeenCalledTimes(1);
  });

  it("opens create rule dialog when Create Rule button is clicked", () => {
    useAutomationRulesMock.mockReturnValue({
      data: MOCK_RULES,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<AutomationRulesPage />);

    fireEvent.click(screen.getByTestId("create-rule-btn"));
    expect(screen.getByTestId("create-rule-form")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Automation Executions Page
// ---------------------------------------------------------------------------

describe("AutomationExecutionsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders executions page header and table with data", () => {
    useAutomationExecutionsMock.mockReturnValue({
      data: MOCK_EXECUTIONS,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<AutomationExecutionsPage />);

    expect(screen.getByTestId("automation-executions-page")).toBeInTheDocument();
    expect(screen.getByText("Execution Log")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("11")).toBeInTheDocument();
  });

  it("shows status badges", () => {
    useAutomationExecutionsMock.mockReturnValue({
      data: MOCK_EXECUTIONS,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<AutomationExecutionsPage />);

    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getByText("Failed")).toBeInTheDocument();
  });

  it("displays error message for failed executions", () => {
    useAutomationExecutionsMock.mockReturnValue({
      data: MOCK_EXECUTIONS,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<AutomationExecutionsPage />);

    expect(screen.getByText("Notification dispatch failed")).toBeInTheDocument();
  });

  it("shows loading skeleton while query is pending", () => {
    useAutomationExecutionsMock.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    });

    render(<AutomationExecutionsPage />);

    expect(screen.getByTestId("automation-executions-page")).toBeInTheDocument();
    expect(screen.queryByText("10")).not.toBeInTheDocument();
  });

  it("shows error state when query fails", () => {
    const refetch = vi.fn();
    useAutomationExecutionsMock.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      refetch,
    });

    render(<AutomationExecutionsPage />);

    expect(screen.getByText("Failed to load execution log")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /retry/i }));
    expect(refetch).toHaveBeenCalledTimes(1);
  });
});
