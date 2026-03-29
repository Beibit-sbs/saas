import React from "react";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi, describe, it, expect, beforeEach } from "vitest";
import AutomationRuleNewPage from "@/app/(admin)/console/automation/new/page";
import * as createRuleModule from "@/modules/platform/automation/create-rule";
import * as useToastModule from "@/shared/ui/use-toast";
import * as navigationModule from "next/navigation";

const useAdminAuthMock = vi.fn();

// Mock dependencies
vi.mock("@/modules/platform/automation/create-rule");
vi.mock("@/shared/ui/use-toast");
vi.mock("next/navigation");
vi.mock("@/shared/auth/context", () => ({
  useAdminAuth: (...args: unknown[]) => useAdminAuthMock(...args),
}));
vi.mock("@/shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
}));

describe("AutomationRuleNewPage", () => {
  const mockPush = vi.fn();
  const mockToast = vi.fn();
  const mockMutate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockMutate.mockReset();
    useAdminAuthMock.mockReturnValue({
      user: { tenantId: 1, roles: ["admin"], permissions: [] },
      isLoading: false,
      isAuthenticated: true,
      refreshSession: vi.fn(),
      logout: vi.fn(),
      hasPermission: vi.fn(() => true),
      hasAnyPermission: vi.fn(() => true),
    });

    (navigationModule.useRouter as any).mockReturnValue({
      push: mockPush,
    });
    (useToastModule.useToast as any).mockReturnValue({
      toast: mockToast,
    });

    (createRuleModule.useCreateAutomationRule as any).mockReturnValue({
      mutateAsync: mockMutate,
    });
  });

  it("renders form with all required fields", () => {
    render(<AutomationRuleNewPage />);

    // Check headers
    expect(screen.getByText("Create Automation Rule")).toBeInTheDocument();

    // Check form fields exist
    expect(screen.getByLabelText(/Rule Name/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Description/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Event Type/)).toBeInTheDocument();

    // Check condition fields
    expect(screen.getByText("Condition (Optional)")).toBeInTheDocument();

    // Check actions section
    expect(screen.getByText("Actions")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /^Add Action$/i })
    ).toBeInTheDocument();

    // Check JSON preview
    expect(screen.getByText("JSON Preview")).toBeInTheDocument();

    // Check buttons
    expect(screen.getByText("Cancel")).toBeInTheDocument();
    expect(screen.getByText("Create Rule")).toBeInTheDocument();
  });

  it("allows adding and removing actions", async () => {
    const user = userEvent.setup();
    render(<AutomationRuleNewPage />);

    // Initially no actions
    expect(
      screen.getByText(/No actions defined yet/)
    ).toBeInTheDocument();

    // Click "Add Action"
    const addActionBtn = screen.getByRole("button", { name: /^Add Action$/i });
    await user.click(addActionBtn);

    // Action should appear
    await waitFor(() => {
      expect(screen.getByText("Action 1")).toBeInTheDocument();
    });

    // Add another action
    await user.click(addActionBtn);

    // Second action should appear
    await waitFor(() => {
      expect(screen.getByText("Action 2")).toBeInTheDocument();
    });

    // Remove first action via scoped header button (stable, role-based)
    const actionHeader = screen.getByText("Action 1").parentElement;
    expect(actionHeader).toBeTruthy();
    const removeButton = within(actionHeader as HTMLElement).getByRole("button");
    await user.click(removeButton);

    // Should only have Action 1 (which was previously Action 2)
    await waitFor(() => {
      expect(screen.getByText("Action 1")).toBeInTheDocument();
      expect(screen.queryByText("Action 2")).not.toBeInTheDocument();
    });
  });

  it("updates JSON preview when form values change", async () => {
    const user = userEvent.setup();
    render(<AutomationRuleNewPage />);

    const nameInput = screen.getByLabelText(/Rule Name/);
    const eventTypeSelect = screen.getByLabelText(/Event Type/);

    // Check initial preview
    let previewText = screen.getByText("JSON Preview").parentElement?.textContent || "";
    expect(previewText).toContain("untitled");

    // Update name
    await user.type(nameInput, "Test Rule");

    // Preview should update
    previewText = screen.getByText("JSON Preview").parentElement?.textContent || "";
    expect(previewText).toContain("Test Rule");

    // Click event type dropdown and select first option
    await user.click(eventTypeSelect);

    const firstEventOption = await screen.findByRole("option", {
      name: "tenant.created",
    });
    await user.click(firstEventOption);

    // Preview should include event_type
    previewText = screen.getByText("JSON Preview").parentElement?.textContent || "";
    expect(previewText).toContain("tenant.created");
  });

  it("handles form submission with all fields", async () => {
    const user = userEvent.setup();
    mockMutate.mockResolvedValueOnce({ id: 123 });

    render(<AutomationRuleNewPage />);

    // Fill in name
    const nameInput = screen.getByLabelText(/Rule Name/);
    await user.type(nameInput, "Test Automation");

    // Fill in description
    const descInput = screen.getByLabelText(/Description/);
    await user.type(descInput, "This is a test rule");

    // Select event type
    const eventTypeSelect = screen.getByLabelText(/Event Type/);
    await user.click(eventTypeSelect);
    const eventOption = await screen.findByRole("option", {
      name: "student.created",
    });
    await user.click(eventOption);

    // Fill in condition
    const conditionFieldInput = screen.getByPlaceholderText(/e.g., gpa/);
    await user.type(conditionFieldInput, "gpa");

    const conditionValueInput = screen.getByPlaceholderText(/e.g., 3.5/);
    await user.type(conditionValueInput, "2.0");

    // Add an action
    const addActionBtn = screen.getByRole("button", { name: /^Add Action$/i });
    await user.click(addActionBtn);

    await waitFor(() => {
      expect(screen.getByText("Action 1")).toBeInTheDocument();
    });

    // Select action type
    const actionTypeSelect = document.getElementById("action-type-0");
    expect(actionTypeSelect).toBeTruthy();
    await user.click(actionTypeSelect!);
    const actionOption = await screen.findByRole("option", {
      name: "Send Notification",
    });
    await user.click(actionOption);

    // Wait for conditional fields to appear and fill them
    const templateInput = await screen.findByPlaceholderText(/Template name/);
    await user.type(templateInput, "alert_template");

    // Submit form
    const submitBtn = screen.getByText("Create Rule");
    await user.click(submitBtn);

    // Wait for mutation to be called
    await waitFor(() => {
      expect(mockMutate).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "Test Automation",
          description: "This is a test rule",
          event_type: "student.created",
          is_active: true,
        })
      );
    });

    // Should show success toast
    expect(mockToast).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "Rule created",
      })
    );

    // Should navigate to rules list
    expect(mockPush).toHaveBeenCalledWith("/console/automation");
  });

  it("builds correct condition_json when condition fields are filled", async () => {
    const user = userEvent.setup();
    mockMutate.mockResolvedValueOnce({ id: 123 });

    render(<AutomationRuleNewPage />);

    // Fill required fields
    const nameInput = screen.getByLabelText(/Rule Name/);
    await user.type(nameInput, "Condition Test");

    const eventTypeSelect = screen.getByLabelText(/Event Type/);
    await user.click(eventTypeSelect);
    const eventOption = await screen.findByRole("option", {
      name: "grade.submitted",
    });
    await user.click(eventOption);

    // Fill condition fields
    const conditionFieldInput = screen.getByPlaceholderText(/e.g., gpa/);
    await user.type(conditionFieldInput, "score");

    const operatorSelect = screen.getByRole("combobox", { name: /operator/i });
    await user.click(operatorSelect);
    const operatorOption = await screen.findByRole("option", {
      name: "greater than (>)",
    });
    await user.click(operatorOption);

    const conditionValueInput = screen.getByPlaceholderText(/e.g., 3.5/);
    await user.type(conditionValueInput, "85");

    // Submit
    const submitBtn = screen.getByText("Create Rule");
    await user.click(submitBtn);

    await waitFor(() => {
      expect(mockMutate).toHaveBeenCalledWith(
        expect.objectContaining({
          condition_json: expect.objectContaining({
            field: "score",
            operator: ">",
            value: 85,
          }),
        })
      );
    });
  });

  it("sends empty condition_json when no condition fields are filled", async () => {
    const user = userEvent.setup();
    mockMutate.mockResolvedValueOnce({ id: 123 });

    render(<AutomationRuleNewPage />);

    // Fill only required fields
    const nameInput = screen.getByLabelText(/Rule Name/);
    await user.type(nameInput, "No Condition");

    const eventTypeSelect = screen.getByLabelText(/Event Type/);
    await user.click(eventTypeSelect);
    const eventOption = await screen.findByRole("option", {
      name: "tenant.created",
    });
    await user.click(eventOption);

    // Leave condition fields empty
    // Submit
    const submitBtn = screen.getByText("Create Rule");
    await user.click(submitBtn);

    await waitFor(() => {
      expect(mockMutate).toHaveBeenCalledWith(
        expect.objectContaining({
          condition_json: {},
        })
      );
    });
  });

  it("shows error toast on submission failure", async () => {
    const user = userEvent.setup();
    const errorMsg = "Server error";
    mockMutate.mockRejectedValueOnce(new Error(errorMsg));

    render(<AutomationRuleNewPage />);

    // Fill required fields
    const nameInput = screen.getByLabelText(/Rule Name/);
    await user.type(nameInput, "Error Test");

    const eventTypeSelect = screen.getByLabelText(/Event Type/);
    await user.click(eventTypeSelect);
    const eventOption = await screen.findByRole("option", {
      name: "student.created",
    });
    await user.click(eventOption);

    // Submit
    const submitBtn = screen.getByText("Create Rule");
    await user.click(submitBtn);

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Failed to create rule",
          description: errorMsg,
          variant: "destructive",
        })
      );
    });

    // Should NOT navigate
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("disables submit button when form is invalid", async () => {
    render(<AutomationRuleNewPage />);

    const submitBtn = screen.getByText("Create Rule") as HTMLButtonElement;

    // Initially disabled (name and event_type required)
    expect(submitBtn).toBeDisabled();

    // After filling name but not event_type, still disabled
    const user = userEvent.setup();
    const nameInput = screen.getByLabelText(/Rule Name/);
    await user.type(nameInput, "Test");

    // Should still be disabled until event_type is filled
    expect(submitBtn).toBeDisabled();
  });

  it("navigates to rules list when Cancel is clicked", async () => {
    const user = userEvent.setup();
    render(<AutomationRuleNewPage />);

    const cancelBtn = screen.getByText("Cancel");
    await user.click(cancelBtn);

    expect(mockPush).toHaveBeenCalledWith("/console/automation");
  });

  it("transforms actions correctly based on action type", async () => {
    const user = userEvent.setup();
    mockMutate.mockResolvedValueOnce({ id: 123 });

    render(<AutomationRuleNewPage />);

    // Fill required fields
    const nameInput = screen.getByLabelText(/Rule Name/);
    await user.type(nameInput, "Multi Action Test");

    const eventTypeSelect = screen.getByLabelText(/Event Type/);
    await user.click(eventTypeSelect);
    const eventOption = await screen.findByRole("option", {
      name: "enrollment.created",
    });
    await user.click(eventOption);

    // Add first action: send_notification
    let addActionBtn = screen.getByRole("button", { name: /^Add Action$/i });
    await user.click(addActionBtn);

    await waitFor(() => {
      expect(screen.getByText("Action 1")).toBeInTheDocument();
    });

    let actionTypeSelect = document.getElementById("action-type-0");
    expect(actionTypeSelect).toBeTruthy();
    await user.click(actionTypeSelect!);
    let actionOption = await screen.findByRole("option", {
      name: "Send Notification",
    });
    await user.click(actionOption);

    let templateInput = await screen.findByPlaceholderText(/Template name/);
    await user.type(templateInput, "notify_template");

    // Add second action: create_task
    addActionBtn = screen.getByRole("button", { name: /^Add Action$/i });
    await user.click(addActionBtn);

    await waitFor(() => {
      expect(screen.getByText("Action 2")).toBeInTheDocument();
    });

    actionTypeSelect = document.getElementById("action-type-1");
    expect(actionTypeSelect).toBeTruthy();
    await user.click(actionTypeSelect!);
    actionOption = await screen.findByRole("option", {
      name: "Create Task",
    });
    await user.click(actionOption);

    let jobTypeInput = await screen.findByPlaceholderText(/Job type/);
    await user.type(jobTypeInput, "review_task");

    // Submit
    const submitBtn = screen.getByText("Create Rule");
    await user.click(submitBtn);

    await waitFor(() => {
      expect(mockMutate).toHaveBeenCalledWith(
        expect.objectContaining({
          actions_json: expect.arrayContaining([
            expect.objectContaining({
              type: "send_notification",
              template: "notify_template",
            }),
            expect.objectContaining({
              type: "create_task",
              job_type: "review_task",
            }),
          ]),
        })
      );
    });
  });
});
