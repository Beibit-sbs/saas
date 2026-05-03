import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import InvoicesPage from "../../app/(admin)/console/billing/invoices/page";
import { formatCurrencyAmount } from "../../shared/utils/format";

// --- navigation mock ---
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/console/billing/invoices",
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

// --- react-query mocks ---
const mockUseTenantsQuery = vi.fn();
const mockUseInvoicesQuery = vi.fn();
const mockFinalizeMutate = vi.fn();
const mockSendMutate = vi.fn();
const mockVoidMutate = vi.fn();

vi.mock("@tanstack/react-query", async (importActual) => {
  const actual = await importActual<typeof import("@tanstack/react-query")>();
  return {
    ...actual,
    useQuery: (...args: Parameters<typeof actual.useQuery>) => {
      const opts = args[0] as { queryKey: unknown[] };
      if (Array.isArray(opts.queryKey)) {
        if (opts.queryKey[0] === "tenants") return mockUseTenantsQuery();
        if (opts.queryKey[0] === "invoices") return mockUseInvoicesQuery();
      }
      return { data: undefined, isLoading: false, error: null };
    },
    useMutation: (...args: Parameters<typeof actual.useMutation>) => {
      const opts = args[0] as { mutationFn: (v: unknown) => unknown };
      const fn = opts?.mutationFn?.toString() ?? "";
      if (fn.includes("/finalize")) {
        return { mutate: mockFinalizeMutate, isPending: false };
      }
      if (fn.includes("/send")) {
        return { mutate: mockSendMutate, isPending: false };
      }
      return { mutate: mockVoidMutate, isPending: false };
    },
    useQueryClient: () => ({ invalidateQueries: vi.fn() }),
  };
});

// --- locale mock ---
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

const TENANTS = [{ id: 5, slug: "alpha", name: "Alpha University" }];

const SAMPLE_INVOICE_DRAFT = {
  invoice_id: "inv-001",
  tenant_id: 5,
  invoice_number: "INV-2026-0001",
  status: "draft",
  currency_code: "KZT",
  items: [],
  total_cents: 25000,
  due_date: "2026-06-01",
  notes: "",
  issued_at: null,
  sent_at: null,
  payments: [],
  voided_at: null,
};

const SAMPLE_INVOICE_PAID = {
  ...SAMPLE_INVOICE_DRAFT,
  invoice_id: "inv-002",
  invoice_number: "INV-2026-0002",
  status: "paid",
  total_cents: 50000,
};

const SAMPLE_INVOICE_OVERDUE = {
  ...SAMPLE_INVOICE_DRAFT,
  invoice_id: "inv-003",
  invoice_number: "INV-2026-0003",
  status: "overdue",
  total_cents: 10000,
};

function setupDefaults() {
  mockUseTenantsQuery.mockReturnValue({
    data: { tenants: TENANTS },
    isLoading: false,
  });
  mockUseInvoicesQuery.mockReturnValue({
    data: { invoices: [SAMPLE_INVOICE_DRAFT, SAMPLE_INVOICE_PAID, SAMPLE_INVOICE_OVERDUE] },
    isLoading: false,
    error: null,
  });
  mockUseTenantLocale.mockReturnValue(KZT_LOCALE);
}

// ---------- tests ----------

describe("InvoicesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaults();
  });

  it("renders page heading", () => {
    render(<InvoicesPage />);
    expect(screen.getByText("Invoices")).toBeInTheDocument();
  });

  it("renders tenant selector with options", () => {
    render(<InvoicesPage />);
    expect(screen.getByRole("combobox", { name: /select tenant/i })).toBeInTheDocument();
    expect(screen.getByText("Alpha University")).toBeInTheDocument();
  });

  it("does not show invoice table before tenant is selected", () => {
    render(<InvoicesPage />);
    expect(screen.queryByText("INV-2026-0001")).not.toBeInTheDocument();
  });

  it("shows invoice table after selecting a tenant", () => {
    render(<InvoicesPage />);
    const select = screen.getByRole("combobox", { name: /select tenant/i });
    fireEvent.change(select, { target: { value: "5" } });
    expect(screen.getByText("INV-2026-0001")).toBeInTheDocument();
    expect(screen.getByText("INV-2026-0002")).toBeInTheDocument();
    expect(screen.getByText("INV-2026-0003")).toBeInTheDocument();
  });

  it("renders KZT-formatted totals for invoices", () => {
    render(<InvoicesPage />);
    fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
      target: { value: "5" },
    });
    // SAMPLE_INVOICE_DRAFT: 25000 cents = 250 KZT
    const expected = formatCurrencyAmount(250, { currencyCode: "KZT", languageCode: "kk" });
    expect(screen.getByText(expected)).toBeInTheDocument();
  });

  it("shows stats cards with correct counts", () => {
    render(<InvoicesPage />);
    fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
      target: { value: "5" },
    });
    expect(screen.getByText("Total Invoices")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("Paid")).toBeInTheDocument();
    expect(screen.getByText("Overdue")).toBeInTheDocument();
    expect(screen.getByText("Drafts")).toBeInTheDocument();
  });

  it("shows Finalize action only for draft invoices", () => {
    render(<InvoicesPage />);
    fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
      target: { value: "5" },
    });
    expect(screen.getByRole("button", { name: /finalize INV-2026-0001/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /finalize INV-2026-0002/i })).not.toBeInTheDocument();
  });

  it("shows Void action for draft and overdue invoices", () => {
    render(<InvoicesPage />);
    fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
      target: { value: "5" },
    });
    expect(screen.getByRole("button", { name: /void INV-2026-0001/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /void INV-2026-0003/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /void INV-2026-0002/i })).not.toBeInTheDocument();
  });

  it("shows void dialog when Void button is clicked", () => {
    render(<InvoicesPage />);
    fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
      target: { value: "5" },
    });
    fireEvent.click(screen.getByRole("button", { name: /void INV-2026-0001/i }));
    expect(screen.getByText("Void Invoice")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /confirm void/i })).toBeInTheDocument();
  });

  it("closes void dialog on cancel", () => {
    render(<InvoicesPage />);
    fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
      target: { value: "5" },
    });
    fireEvent.click(screen.getByRole("button", { name: /void INV-2026-0001/i }));
    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(screen.queryByText("Void Invoice")).not.toBeInTheDocument();
  });

  it("shows status badges for each status", () => {
    render(<InvoicesPage />);
    fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
      target: { value: "5" },
    });
    expect(screen.getAllByText("draft").length).toBeGreaterThan(0);
    expect(screen.getAllByText("paid").length).toBeGreaterThan(0);
    expect(screen.getAllByText("overdue").length).toBeGreaterThan(0);
  });

  it("shows status filter dropdown", () => {
    render(<InvoicesPage />);
    fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
      target: { value: "5" },
    });
    expect(screen.getByRole("combobox", { name: /filter by status/i })).toBeInTheDocument();
  });

  it("shows empty state when no invoices", () => {
    mockUseInvoicesQuery.mockReturnValue({
      data: { invoices: [] },
      isLoading: false,
      error: null,
    });
    render(<InvoicesPage />);
    fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
      target: { value: "5" },
    });
    expect(screen.getByText("No invoices found.")).toBeInTheDocument();
  });

  it("shows error state on fetch error", () => {
    mockUseInvoicesQuery.mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error("Network error"),
    });
    render(<InvoicesPage />);
    fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
      target: { value: "5" },
    });
    expect(screen.getByText("Failed to load invoices")).toBeInTheDocument();
  });
});
