import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { PlatformSectionView } from "../../app/(admin)/console/platform/platform-section-view";

const pushMock = vi.fn();
const hasPermissionMock = vi.fn();
const mutateMock = vi.fn();
const invalidateQueriesMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

vi.mock("@/shared/ui/require-admin-role", () => ({
  RequireAdminRole: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("@/shared/hooks/use-permissions", () => ({
  usePermissions: () => ({ hasPermission: hasPermissionMock }),
}));

vi.mock("@/shared/ui/permission-gate", () => ({
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

const mockWebhookSubs = [
  { id: 1, event_type: "integration.updated", target_url: "https://example.com/hook", is_active: true },
  { id: 2, event_type: "user.created", target_url: "https://example.com/hook2", is_active: false },
];

const mockWebhookDeliveries = {
  items: [
    {
      id: 10,
      delivery_status: "delivered",
      event_type: "integration.updated",
      retry_count: 0,
      outbox_event_id: 5,
      response_status_code: 200,
      next_retry_at: null,
      last_error: null,
    },
    {
      id: 11,
      delivery_status: "failed",
      event_type: "user.created",
      retry_count: 3,
      outbox_event_id: 6,
      response_status_code: 503,
      next_retry_at: "2026-04-21T10:00:00Z",
      last_error: "Connection timeout",
    },
  ],
};

vi.mock("@tanstack/react-query", async () => {
  const actual = await vi.importActual<typeof import("@tanstack/react-query")>("@tanstack/react-query");
  return {
    ...actual,
    useQuery: ({ queryKey }: { queryKey: unknown[] }) => {
      const key = queryKey as string[];
      if (key.includes("subs")) return { data: mockWebhookSubs };
      if (key.includes("deliveries")) return { data: mockWebhookDeliveries };
      if (key.includes("tenants")) return { data: { tenants: [{ id: 1, slug: "t1", name: "Tenant 1", status: "active", plan_id: 1 }] } };
      if (key.includes("ops-summary")) return { data: { queues: { retry_backlog: 2, dead_webhooks: 1, failed_webhooks: 3, failed_automation_executions: 0 } } };
      return { data: undefined };
    },
    useQueryClient: () => ({ invalidateQueries: invalidateQueriesMock }),
    useMutation: () => ({ mutate: mutateMock, isPending: false }),
  };
});

describe("Webhook Subscriptions UI (Gap 2 DoD)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
    hasPermissionMock.mockReturnValue(true);
  });

  it("test_webhook_subscriptions_page_renders: renders integrations tab with webhook subscriptions list", () => {
    render(<PlatformSectionView section={"integrations" as any} />);

    expect(screen.getByTestId("platform-console-integrations")).toBeInTheDocument();
    // event_type appears in both subscriptions list and deliveries list
    expect(screen.getAllByText("integration.updated").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("user.created").length).toBeGreaterThanOrEqual(1);
  });

  it("test_webhook_create_form_validation: create button is disabled until all required fields are filled", async () => {
    const user = userEvent.setup();
    render(<PlatformSectionView section={"integrations" as any} />);

    const submitBtn = screen.getByTestId("webhook-create-submit");
    expect(submitBtn).toBeDisabled();

    await user.type(screen.getByTestId("webhook-event-type-input"), "integration.updated");
    expect(submitBtn).toBeDisabled();

    await user.type(screen.getByTestId("webhook-target-url-input"), "https://example.com/hook");
    expect(submitBtn).toBeDisabled();

    // signing secret must be >= 16 chars
    await user.type(screen.getByTestId("webhook-signing-secret-input"), "short");
    expect(submitBtn).toBeDisabled();

    await user.clear(screen.getByTestId("webhook-signing-secret-input"));
    await user.type(screen.getByTestId("webhook-signing-secret-input"), "a_valid_secret_1234");
    expect(submitBtn).not.toBeDisabled();
  });

  it("test_webhook_create_form_validation: submitting the form calls mutate with correct payload", async () => {
    const user = userEvent.setup();
    render(<PlatformSectionView section={"integrations" as any} />);

    await user.type(screen.getByTestId("webhook-event-type-input"), "integration.updated");
    await user.type(screen.getByTestId("webhook-target-url-input"), "https://example.com/hook");
    await user.type(screen.getByTestId("webhook-signing-secret-input"), "a_valid_secret_1234");

    const submitBtn = screen.getByTestId("webhook-create-submit");
    await user.click(submitBtn);

    expect(mutateMock).toHaveBeenCalledWith({
      tenant_id: 1,
      event_type: "integration.updated",
      target_url: "https://example.com/hook",
      signing_secret: "a_valid_secret_1234",
    });
  });

  it("test_webhook_delivery_history_display: renders delivery history with status and error details", () => {
    render(<PlatformSectionView section={"integrations" as any} />);

    // Both delivery entries should appear
    const deliveryRows = screen.getAllByText(/integration\.updated|user\.created/);
    expect(deliveryRows.length).toBeGreaterThanOrEqual(2);

    // Error message displayed for failed delivery
    expect(screen.getByText("Connection timeout")).toBeInTheDocument();
  });

  it("deactivate button shown only for active subscriptions", () => {
    render(<PlatformSectionView section={"integrations" as any} />);

    const deactivateButtons = screen.getAllByRole("button", { name: /Deactivate/i });
    // Only 1 active subscription → 1 deactivate button
    expect(deactivateButtons).toHaveLength(1);
  });
});
