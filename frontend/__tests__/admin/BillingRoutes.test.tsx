import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import BillingIndexPage from "../../app/(admin)/console/billing/page";
import BillingPlansPage from "../../app/(admin)/console/billing/plans/page";
import BillingQuotasPage from "../../app/(admin)/console/billing/quotas/page";
import BillingUsagePage from "../../app/(admin)/console/billing/usage/page";
import { formatCurrencyAmount } from "../../shared/utils/format";

const mockUseBillingPlans = vi.fn();
const mockUseTenantBillingState = vi.fn();
const mockUseTenantDelinquencyDashboard = vi.fn();
const mockUseTenantLocale = vi.fn();

vi.mock("next/navigation", () => ({
  redirect: vi.fn(),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/console/billing",
}));

vi.mock("../../shared/api/client", () => ({
  apiGet: vi.fn(() => new Promise(() => {})),
  apiPost: vi.fn(() => new Promise(() => {})),
  apiPatch: vi.fn(() => new Promise(() => {})),
  apiPut: vi.fn(() => new Promise(() => {})),
  apiDelete: vi.fn(() => new Promise(() => {})),
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(() => ({ data: undefined, isLoading: true, error: null })),
  useMutation: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
  useQueryClient: vi.fn(() => ({ invalidateQueries: vi.fn() })),
}));

vi.mock("../../app/(admin)/console/platform/platform-section-view", () => ({
  PlatformSectionView: ({ section }: { section: string }) => <div>section:{section}</div>,
}));

// BillingIndexPage is a "use client" component — mock auth/permission hooks.
vi.mock("../../shared/hooks/use-permissions", () => ({
  usePermissions: () => ({ hasPermission: () => true }),
}));

vi.mock("../../app/components/LanguageProvider", () => ({
  useLanguage: () => ({
    t: (key: string) => key,
    locale: "en",
    setLocale: () => {},
  }),
  LanguageProvider: ({ children }: { children: React.ReactNode }) => children,
}));

vi.mock("../../shared/auth/context", () => ({
  useAdminAuth: () => ({
    user: { id: "1", login: "admin", roles: ["admin"], tenant_id: 1 },
    token: "test-token",
    hasPermission: () => true,
  }),
  AuthContext: { Provider: ({ children }: { children: React.ReactNode }) => children },
}));

vi.mock("../../modules/billing/hooks", () => ({
  useBillingPlans: () => mockUseBillingPlans(),
  useTenantBillingState: () => mockUseTenantBillingState(),
  useTenantDelinquencyDashboard: () => mockUseTenantDelinquencyDashboard(),
}));

vi.mock("../../modules/currency-localization/hooks", () => ({
  useTenantLocale: () => mockUseTenantLocale(),
}));

beforeEach(() => {
  mockUseBillingPlans.mockReturnValue({
    data: [
      {
        id: 1,
        code: "starter",
        name: "Starter",
        price_cents: 1000,
        features: {},
        limits: {},
        active: true,
        created_at: "2026-05-03T00:00:00Z",
      },
    ],
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  });

  mockUseTenantBillingState.mockReturnValue({
    data: {
      tenant_id: 1,
      plan_code: "starter",
      plan_id: 1,
      next_plan_code: null,
      subscription_status: "active",
      billing_state: "read_write",
      period_start: null,
      period_end: null,
      limits: {},
      usage: {},
      subscription: {
        tenant_id: 1,
        plan_id: 1,
        plan_code: "starter",
        status: "active",
        started_at: "2026-05-03T00:00:00Z",
        trial_ends_at: null,
        current_period_start: "2026-05-01T00:00:00Z",
        current_period_end: "2026-06-01T00:00:00Z",
        next_plan_id: null,
        next_plan_code: null,
        updated_at: "2026-05-03T00:00:00Z",
      },
    },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  });

  mockUseTenantDelinquencyDashboard.mockReturnValue({
    data: {
      total: 1,
      open_total: 1,
      total_overdue_cents: 5000,
      by_status: { overdue: 1 },
    },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  });

  mockUseTenantLocale.mockReturnValue({
    data: {
      profile_id: 1,
      tenant_id: 1,
      currency_code: "KZT",
      language_code: "kk",
      timezone: "Asia/Almaty",
    },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  });
});

describe("Billing routes", () => {
  it("renders /console/billing index page with billing content", () => {
    render(<BillingIndexPage />);
    expect(screen.getByText("Billing")).toBeInTheDocument();
    expect(screen.getByText("Current Plan")).toBeInTheDocument();
    expect(screen.getByText("STARTER")).toBeInTheDocument();
    expect(screen.getByText(formatCurrencyAmount(50, { currencyCode: "KZT", languageCode: "kk" }))).toBeInTheDocument();
    expect(screen.getByText("Tenant currency: KZT")).toBeInTheDocument();
  });

  it("shows loading state for billing summary cards", () => {
    mockUseBillingPlans.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    });

    render(<BillingIndexPage />);
    expect(screen.getAllByText("Loading...").length).toBeGreaterThan(0);
  });

  it("shows error state when billing summary loading fails", () => {
    mockUseBillingPlans.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("boom"),
      refetch: vi.fn(),
    });

    render(<BillingIndexPage />);
    expect(screen.getByText("Billing data unavailable")).toBeInTheDocument();
  });

  it("shows empty-safe values when billing data is empty", () => {
    mockUseBillingPlans.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    mockUseTenantBillingState.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    mockUseTenantDelinquencyDashboard.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<BillingIndexPage />);
    expect(screen.getByText("No plan")).toBeInTheDocument();
    expect(screen.getByText("Tenant currency: KZT")).toBeInTheDocument();
  });

  it("falls back to USD formatting when tenant locale is missing", () => {
    mockUseTenantLocale.mockReturnValue({
      data: null,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<BillingIndexPage />);
    expect(screen.getByText(formatCurrencyAmount(50, { currencyCode: "USD", languageCode: "en" }))).toBeInTheDocument();
    expect(screen.getByText("Tenant currency: USD")).toBeInTheDocument();
  });

  it("maps /console/billing/plans to billing-plans section", () => {
    render(<BillingPlansPage />);
    expect(screen.getByText("Billing Plans")).toBeInTheDocument();
  });

  it("maps /console/billing/quotas to usage-quotas section", () => {
    render(<BillingQuotasPage />);
    expect(screen.getByText("Quota Management")).toBeInTheDocument();
  });

  it("maps /console/billing/usage to usage-quotas section", () => {
    render(<BillingUsagePage />);
    expect(screen.getByText("Usage Tracking")).toBeInTheDocument();
  });
});
