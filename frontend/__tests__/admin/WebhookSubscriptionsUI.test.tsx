import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { PlatformSectionView } from "../../app/(admin)/console/platform/platform-section-view";

const pushMock = vi.fn();
const hasPermissionMock = vi.fn();

const apiGetMock = vi.fn();
const apiPostMock = vi.fn();
const apiPutMock = vi.fn();
const apiDeleteMock = vi.fn();

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

vi.mock("@/shared/api/client", () => ({
  apiGet: (...args: unknown[]) => apiGetMock(...args),
  apiPost: (...args: unknown[]) => apiPostMock(...args),
  apiPut: (...args: unknown[]) => apiPutMock(...args),
  apiDelete: (...args: unknown[]) => apiDeleteMock(...args),
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

function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

const TEST_TIMEOUT_MS = 30_000;

function renderWithQueryClient(): void {
  const queryClient = createTestQueryClient();
  render(
    <QueryClientProvider client={queryClient}>
      <PlatformSectionView section={"integrations" as any} />
    </QueryClientProvider>,
  );
}

describe("Webhook Subscriptions UI (Gap 2 DoD)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
    hasPermissionMock.mockReturnValue(true);

    apiPostMock.mockResolvedValue({ ok: true });
    apiPutMock.mockResolvedValue({ ok: true });
    apiDeleteMock.mockResolvedValue({ ok: true });

    apiGetMock.mockImplementation(async (path: string) => {
      if (path === "/api/admin/tenants") {
        return { tenants: [{ id: 1, slug: "t1", name: "Tenant 1", status: "active", plan_id: 1 }] };
      }
      if (path === "/platform/plans") {
        return { plans: [] };
      }
      if (path === "/platform/quotas") {
        return { quotas: [] };
      }
      if (path === "/api/admin/feature-flags") {
        return { flags: [] };
      }
      if (path === "/api/admin/integrations/settings") {
        return {
          ldap: { enabled: true, configured: true },
          ai_providers: [{ provider: "openai", configured: true }],
        };
      }
      if (path === "/api/v1/platform/ops/summary") {
        return { queues: { retry_backlog: 2, dead_webhooks: 1, failed_webhooks: 3, failed_automation_executions: 0 } };
      }
      if (path === "/api/admin/service-accounts") {
        return { accounts: [] };
      }
      if (path === "/api/v1/admin/tenants/1/webhooks/subscriptions") {
        return mockWebhookSubs;
      }
      if (path === "/api/v1/admin/tenants/1/webhooks/deliveries") {
        return mockWebhookDeliveries;
      }
      if (path === "/api/bff/admin/platform/automation/rules") {
        return [];
      }
      if (path === "/api/bff/admin/platform/automation/executions") {
        return [];
      }
      if (path === "/api/admin/audit/events") {
        return { events: [] };
      }
      if (path === "/platform/tenants/1/billing") {
        return {
          tenant_id: 1,
          plan_code: "basic",
          next_plan_code: null,
          subscription_status: "active",
          billing_state: "ok",
          limits: {},
          usage: {},
        };
      }
      return {};
    });
  });

  it("test_webhook_subscriptions_page_renders: renders integrations tab with webhook subscriptions list", async () => {
    renderWithQueryClient();

    expect(await screen.findByTestId("platform-console-integrations")).toBeInTheDocument();
    expect((await screen.findAllByText("integration.updated")).length).toBeGreaterThanOrEqual(1);
    expect((await screen.findAllByText("user.created")).length).toBeGreaterThanOrEqual(1);
  }, TEST_TIMEOUT_MS);

  it("test_webhook_create_form_validation: create button is disabled until all required fields are filled", async () => {
    const user = userEvent.setup();
    renderWithQueryClient();

    await screen.findByTestId("platform-console-integrations");

    const submitBtn = screen.getByTestId("webhook-create-submit");
    expect(submitBtn).toBeDisabled();

    await user.type(screen.getByTestId("webhook-event-type-input"), "integration.updated");
    expect(submitBtn).toBeDisabled();

    await user.type(screen.getByTestId("webhook-target-url-input"), "https://example.com/hook");
    expect(submitBtn).toBeDisabled();

    await user.type(screen.getByTestId("webhook-signing-secret-input"), "short");
    expect(submitBtn).toBeDisabled();

    await user.clear(screen.getByTestId("webhook-signing-secret-input"));
    await user.type(screen.getByTestId("webhook-signing-secret-input"), "a_valid_secret_1234");
    expect(submitBtn).not.toBeDisabled();
  }, TEST_TIMEOUT_MS);

  it("test_webhook_create_form_validation: submitting the form calls mutate with correct payload", async () => {
    const user = userEvent.setup();
    renderWithQueryClient();

    await screen.findByTestId("platform-console-integrations");

    await user.type(screen.getByTestId("webhook-event-type-input"), "integration.updated");
    await user.type(screen.getByTestId("webhook-target-url-input"), "https://example.com/hook");
    await user.type(screen.getByTestId("webhook-signing-secret-input"), "a_valid_secret_1234");

    await user.click(screen.getByTestId("webhook-create-submit"));

    await waitFor(() => {
      expect(apiPostMock).toHaveBeenCalledWith("/api/v1/admin/webhooks/subscriptions", {
        tenant_id: 1,
        event_type: "integration.updated",
        target_url: "https://example.com/hook",
        signing_secret: "a_valid_secret_1234",
      });
    });
  }, TEST_TIMEOUT_MS);

  it("test_webhook_delivery_history_display: renders delivery history with status and error details", async () => {
    renderWithQueryClient();

    await screen.findByTestId("platform-console-integrations");

    expect(await screen.findByText("Connection timeout")).toBeInTheDocument();
    expect(await screen.findByText(/outbox #6/i)).toBeInTheDocument();
    expect(await screen.findByText(/retries: 3/i)).toBeInTheDocument();
  }, TEST_TIMEOUT_MS);

  it("deactivate button shown only for active subscriptions", async () => {
    renderWithQueryClient();

    await screen.findByTestId("platform-console-integrations");

    const deactivateButtons = await screen.findAllByRole("button", { name: /Deactivate/i });
    expect(deactivateButtons).toHaveLength(1);
  }, TEST_TIMEOUT_MS);
});
