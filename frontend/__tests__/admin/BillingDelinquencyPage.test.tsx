import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import BillingDelinquencyPage from "../../app/(admin)/console/billing/delinquency/page";
import { formatCurrencyAmount } from "../../shared/utils/format";

// --- mocks ---

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/console/billing/delinquency",
}));

vi.mock("../../app/components/LanguageProvider", async () => {
  const { en: commonEn } = await import("../../i18n/common/en");
  const { en: adminEn } = await import("../../i18n/admin/en");
  const dict = { ...commonEn, ...adminEn } as Record<string, string>;
  return {
    useLanguage: () => ({
      t: (key: string) => dict[key] ?? key,
    }),
  };
});

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("../../shared/hooks/use-mutation-feedback", () => ({
  useMutationFeedback: () => ({
    getHandlers: () => ({ onSuccess: vi.fn(), onError: vi.fn() }),
  }),
}));

const mockUseTenants = vi.fn();
vi.mock("@tanstack/react-query", async (importActual) => {
  const actual = await importActual<typeof import("@tanstack/react-query")>();
  return {
    ...actual,
    useQuery: (...args: Parameters<typeof actual.useQuery>) => {
      // intercept tenant list query by queryKey
      const opts = args[0] as { queryKey: unknown[] };
      if (Array.isArray(opts.queryKey) && opts.queryKey[0] === "tenants") {
        return mockUseTenants();
      }
      return actual.useQuery(...args);
    },
  };
});

const mockUseDelinquencyRecords = vi.fn();
const mockUseDelinquencyDashboard = vi.fn();
const mockUseDunningPolicy = vi.fn();
const mockUseEscalate = vi.fn();
const mockUseResolve = vi.fn();
const mockUseSendReminder = vi.fn();

vi.mock("../../modules/billing/hooks", () => ({
  useTenantDelinquencyRecords: () => mockUseDelinquencyRecords(),
  useTenantDelinquencyDashboard: () => mockUseDelinquencyDashboard(),
  useTenantDunningPolicy: () => mockUseDunningPolicy(),
  useEscalateDelinquency: () => mockUseEscalate(),
  useResolveDelinquency: () => mockUseResolve(),
  useSendDelinquencyReminder: () => mockUseSendReminder(),
}));

const mockUseTenantLocale = vi.fn();

vi.mock("../../modules/currency-localization/hooks", () => ({
  useTenantLocale: () => mockUseTenantLocale(),
}));

// --- fixtures ---

const KZT_LOCALE = {
  data: {
    profile_id: 1,
    tenant_id: 5,
    currency_code: "KZT",
    language_code: "kk",
    timezone: "Asia/Almaty",
  },
  isLoading: false,
  error: null,
};

const SAMPLE_RECORD = {
  id: 1,
  tenant_id: 5,
  invoice_id: "INV-2026-001",
  status: "open",
  opened_at: "2026-01-01T00:00:00Z",
  last_reminder_at: null,
  reminder_count: 0,
  escalated_at: null,
  resolved_at: null,
  resolution: null,
  notes: null,
  amount_cents: 15000,
};

const SAMPLE_DASHBOARD = {
  total: 3,
  open_total: 2,
  total_overdue_cents: 45000,
  by_status: { open: 2, resolved: 1 },
};

const SAMPLE_POLICY = {
  grace_period_days: 5,
  overdue_period_days: 30,
  suspension_period_days: 60,
  auto_cancel_after_days: 90,
  reminder_schedule: [7, 14, 21],
  require_approval_for_reactivation: false,
};

const TENANTS = [{ id: 5, slug: "alpha", name: "Alpha University" }];

function setupDefaults() {
  mockUseTenants.mockReturnValue({
    data: { tenants: TENANTS },
    isLoading: false,
  });
  mockUseDelinquencyDashboard.mockReturnValue({
    data: SAMPLE_DASHBOARD,
    isLoading: false,
  });
  mockUseDunningPolicy.mockReturnValue({
    data: SAMPLE_POLICY,
    isLoading: false,
  });
  mockUseDelinquencyRecords.mockReturnValue({
    data: { items: [SAMPLE_RECORD] },
    isLoading: false,
    error: null,
  });
  mockUseEscalate.mockReturnValue({ mutate: vi.fn(), isPending: false });
  mockUseResolve.mockReturnValue({ mutate: vi.fn(), isPending: false });
  mockUseSendReminder.mockReturnValue({ mutate: vi.fn(), isPending: false });
  mockUseTenantLocale.mockReturnValue(KZT_LOCALE);
}

describe("BillingDelinquencyPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaults();
  });

  it("renders page heading", () => {
    render(<BillingDelinquencyPage />);
    expect(screen.getByText("Delinquency")).toBeInTheDocument();
  });

  it("renders tenant selector buttons", () => {
    render(<BillingDelinquencyPage />);
    expect(screen.getByText("Alpha University")).toBeInTheDocument();
  });

  it("shows KZT-formatted total overdue when tenant locale is KZT", () => {
    render(<BillingDelinquencyPage />);
    fireEvent.click(screen.getByText("Alpha University"));
    // Total Overdue: 45000 cents = 450.00 KZT
    const expected = formatCurrencyAmount(450, { currencyCode: "KZT", languageCode: "kk" });
    expect(screen.getByText(expected)).toBeInTheDocument();
    expect(screen.getByText("Tenant currency: KZT")).toBeInTheDocument();
  });

  it("falls back to USD when locale is unavailable", () => {
    mockUseTenantLocale.mockReturnValue({ data: null, isLoading: false, error: null });
    render(<BillingDelinquencyPage />);
    fireEvent.click(screen.getByText("Alpha University"));
    const expected = formatCurrencyAmount(450, { currencyCode: "USD", languageCode: "en" });
    expect(screen.getByText(expected)).toBeInTheDocument();
    expect(screen.getByText("Tenant currency: USD")).toBeInTheDocument();
  });

  it("shows KZT-formatted amount in records table", () => {
    render(<BillingDelinquencyPage />);
    fireEvent.click(screen.getByText("Alpha University"));
    // amount_cents = 15000 → 150.00 KZT
    const expected = formatCurrencyAmount(150, { currencyCode: "KZT", languageCode: "kk" });
    expect(screen.getByText(expected)).toBeInTheDocument();
  });

  it("shows dunning policy details", () => {
    render(<BillingDelinquencyPage />);
    fireEvent.click(screen.getByText("Alpha University"));
    expect(screen.getByText("Dunning Policy")).toBeInTheDocument();
    expect(screen.getByText("5 days")).toBeInTheDocument();
  });
});
