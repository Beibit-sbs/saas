import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import BillingSubscriptionsPage from "../../app/(admin)/console/billing/subscriptions/page";

// --- navigation mock ---
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/console/billing/subscriptions",
}));

vi.mock("../../app/components/LanguageProvider", async () => {
  return {
    useLanguage: () => ({ t: (key: string) => key }),
  };
});

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
}));

vi.mock("../../shared/hooks/use-mutation-feedback", () => ({
  useMutationFeedback: () => ({
    getHandlers: () => ({ onSuccess: vi.fn(), onError: vi.fn() }),
    feedback: null,
    showSuccess: vi.fn(),
    showError: vi.fn(),
  }),
}));

// --- billing hooks mock ---
const mockUseBillingPlans = vi.fn();
const mockUseTenantBillingState = vi.fn();
const mockAssignMutate = vi.fn();
const mockChangePlanMutate = vi.fn();
const mockTransitionMutate = vi.fn();

vi.mock("../../modules/billing/hooks", () => ({
  useBillingPlans: () => mockUseBillingPlans(),
  useTenantBillingState: () => mockUseTenantBillingState(),
  useAssignBillingSubscription: () => ({
    mutate: mockAssignMutate,
    isPending: false,
  }),
  useChangeBillingPlan: () => ({
    mutate: mockChangePlanMutate,
    isPending: false,
  }),
  useTransitionBillingSubscription: () => ({
    mutate: mockTransitionMutate,
    isPending: false,
  }),
}));

// --- react-query tenants mock ---
const mockUseQueryTenants = vi.fn();

vi.mock("@tanstack/react-query", async (importActual) => {
  const actual = await importActual<typeof import("@tanstack/react-query")>();
  return {
    ...actual,
    useQuery: () => mockUseQueryTenants(),
    useMutation: () => ({ mutate: vi.fn(), isPending: false }),
    useQueryClient: () => ({ invalidateQueries: vi.fn() }),
  };
});

vi.mock("../../shared/api/client", () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiPut: vi.fn(),
}));

// --- fixtures ---

const PLANS = [
  { id: 1, code: "starter", name: "Starter", price_cents: 1000, features: {}, limits: {}, active: true, created_at: "2026-01-01" },
  { id: 2, code: "pro", name: "Pro", price_cents: 5000, features: {}, limits: {}, active: true, created_at: "2026-01-01" },
];

const TENANTS = [
  { id: 1, slug: "alpha", name: "Alpha Corp", status: "active" },
  { id: 2, slug: "beta", name: "Beta Ltd", status: "active" },
];

const BILLING_STATE = {
  tenant_id: 1,
  plan_code: "starter",
  plan_id: 1,
  next_plan_code: null,
  subscription_status: "active",
  billing_state: "read_write",
  period_start: "2026-01-01T00:00:00Z",
  period_end: "2026-02-01T00:00:00Z",
  limits: {},
  usage: {},
  subscription: null,
};

beforeEach(() => {
  vi.clearAllMocks();
  mockUseBillingPlans.mockReturnValue({
    data: PLANS,
    isLoading: false,
    error: null,
  });
  mockUseTenantBillingState.mockReturnValue({
    data: null,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  });
  mockUseQueryTenants.mockReturnValue({
    data: { tenants: TENANTS },
    isLoading: false,
    error: null,
  });
});

// ─── tests ───────────────────────────────────────────────────────────────────

describe("BillingSubscriptionsPage", () => {
  it("renders page title", () => {
    render(<BillingSubscriptionsPage />);
    expect(screen.getAllByText("Subscriptions").length).toBeGreaterThan(0);
  });

  it("renders tenant selector section", () => {
    render(<BillingSubscriptionsPage />);
    expect(screen.getByText("Select Tenant")).toBeTruthy();
  });

  it("renders tenant buttons", () => {
    render(<BillingSubscriptionsPage />);
    expect(screen.getByText("Alpha Corp")).toBeTruthy();
    expect(screen.getByText("Beta Ltd")).toBeTruthy();
  });

  it("shows loading state for tenants", () => {
    mockUseQueryTenants.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });
    render(<BillingSubscriptionsPage />);
    expect(screen.getByText("Loading tenants…")).toBeTruthy();
  });

  it("shows error state when tenants fail to load", () => {
    mockUseQueryTenants.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("Network error"),
    });
    render(<BillingSubscriptionsPage />);
    expect(screen.getByText("Failed to load tenants")).toBeTruthy();
  });

  it("shows prompt to select tenant when none selected", () => {
    render(<BillingSubscriptionsPage />);
    expect(
      screen.getByText("Select a tenant above to view and manage their subscription.")
    ).toBeTruthy();
  });

  it("shows billing state after tenant selected", () => {
    mockUseTenantBillingState.mockReturnValue({
      data: BILLING_STATE,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<BillingSubscriptionsPage />);
    const alphaBtn = screen.getByText("Alpha Corp");
    fireEvent.click(alphaBtn);
    expect(screen.getByText("Current Subscription")).toBeTruthy();
  });

  it("shows plan name in subscription state", () => {
    mockUseTenantBillingState.mockReturnValue({
      data: BILLING_STATE,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<BillingSubscriptionsPage />);
    fireEvent.click(screen.getByText("Alpha Corp"));
    expect(screen.getByText("starter")).toBeTruthy();
  });

  it("shows subscription status badge", () => {
    mockUseTenantBillingState.mockReturnValue({
      data: BILLING_STATE,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<BillingSubscriptionsPage />);
    fireEvent.click(screen.getByText("Alpha Corp"));
    expect(screen.getAllByText("active").length).toBeGreaterThan(0);
  });

  it("shows Change Plan section after tenant selection", () => {
    mockUseTenantBillingState.mockReturnValue({
      data: BILLING_STATE,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<BillingSubscriptionsPage />);
    fireEvent.click(screen.getByText("Alpha Corp"));
    expect(screen.getByText("Change Plan")).toBeTruthy();
  });

  it("shows plan options in plan selector", () => {
    mockUseTenantBillingState.mockReturnValue({
      data: BILLING_STATE,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<BillingSubscriptionsPage />);
    fireEvent.click(screen.getByText("Alpha Corp"));
    expect(screen.getByText("Starter (starter)")).toBeTruthy();
    expect(screen.getByText("Pro (pro)")).toBeTruthy();
  });

  it("shows Assign button after tenant selected", () => {
    mockUseTenantBillingState.mockReturnValue({
      data: BILLING_STATE,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<BillingSubscriptionsPage />);
    fireEvent.click(screen.getByText("Alpha Corp"));
    expect(screen.getByText("Assign")).toBeTruthy();
  });

  it("shows Schedule Change button", () => {
    mockUseTenantBillingState.mockReturnValue({
      data: BILLING_STATE,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<BillingSubscriptionsPage />);
    fireEvent.click(screen.getByText("Alpha Corp"));
    expect(screen.getByText("Schedule Change")).toBeTruthy();
  });

  it("shows Transition Status section", () => {
    mockUseTenantBillingState.mockReturnValue({
      data: BILLING_STATE,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<BillingSubscriptionsPage />);
    fireEvent.click(screen.getByText("Alpha Corp"));
    expect(screen.getByText("Transition Status")).toBeTruthy();
  });

  it("shows Apply button for status transition", () => {
    mockUseTenantBillingState.mockReturnValue({
      data: BILLING_STATE,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<BillingSubscriptionsPage />);
    fireEvent.click(screen.getByText("Alpha Corp"));
    expect(screen.getByText("Apply")).toBeTruthy();
  });

  it("shows billing state loading indicator", () => {
    mockUseTenantBillingState.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    });
    render(<BillingSubscriptionsPage />);
    fireEvent.click(screen.getByText("Alpha Corp"));
    expect(screen.getByText("Loading billing state…")).toBeTruthy();
  });

  it("shows billing state error", () => {
    mockUseTenantBillingState.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("state failed"),
      refetch: vi.fn(),
    });
    render(<BillingSubscriptionsPage />);
    fireEvent.click(screen.getByText("Alpha Corp"));
    expect(screen.getByText("Failed to load billing state")).toBeTruthy();
  });

  it("shows Usage / Limits section", () => {
    mockUseTenantBillingState.mockReturnValue({
      data: BILLING_STATE,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<BillingSubscriptionsPage />);
    fireEvent.click(screen.getByText("Alpha Corp"));
    expect(screen.getByText("Usage / Limits")).toBeTruthy();
  });

  it("shows 'No limits configured' when limits are empty", () => {
    mockUseTenantBillingState.mockReturnValue({
      data: { ...BILLING_STATE, limits: {}, usage: {} },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<BillingSubscriptionsPage />);
    fireEvent.click(screen.getByText("Alpha Corp"));
    expect(screen.getByText("No limits configured")).toBeTruthy();
  });

  it("shows period dates when available", () => {
    mockUseTenantBillingState.mockReturnValue({
      data: BILLING_STATE,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<BillingSubscriptionsPage />);
    fireEvent.click(screen.getByText("Alpha Corp"));
    expect(screen.getByText("Period")).toBeTruthy();
  });

  it("shows status options in transition dropdown", () => {
    mockUseTenantBillingState.mockReturnValue({
      data: BILLING_STATE,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<BillingSubscriptionsPage />);
    fireEvent.click(screen.getByText("Alpha Corp"));
    expect(screen.getByText("suspended")).toBeTruthy();
    expect(screen.getByText("past_due")).toBeTruthy();
  });

  it("page description rendered", () => {
    render(<BillingSubscriptionsPage />);
    expect(
      screen.getByText("View and manage tenant billing subscriptions and plan assignments")
    ).toBeTruthy();
  });
});
