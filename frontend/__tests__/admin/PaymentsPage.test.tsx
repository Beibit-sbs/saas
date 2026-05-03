import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import PaymentsPage from "../../app/(admin)/console/billing/payments/page";
import { formatCurrencyAmount } from "../../shared/utils/format";

// --- navigation mock ---
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/console/billing/payments",
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
const mockUsePaymentsQuery = vi.fn();
const mockProcessMutate = vi.fn();
const mockCompleteMutate = vi.fn();
const mockFailMutate = vi.fn();
const mockRefundMutate = vi.fn();

vi.mock("@tanstack/react-query", async (importActual) => {
  const actual = await importActual<typeof import("@tanstack/react-query")>();
  return {
    ...actual,
    useQuery: (...args: Parameters<typeof actual.useQuery>) => {
      const opts = args[0] as { queryKey: unknown[] };
      if (Array.isArray(opts.queryKey)) {
        if (opts.queryKey[0] === "tenants") return mockUseTenantsQuery();
        if (opts.queryKey[0] === "payments") return mockUsePaymentsQuery();
      }
      return { data: undefined, isLoading: false, error: null };
    },
    useMutation: (...args: Parameters<typeof actual.useMutation>) => {
      const opts = args[0] as { mutationFn: (v: unknown) => unknown };
      const fn = opts?.mutationFn?.toString() ?? "";
      if (fn.includes("/process")) {
        return { mutate: mockProcessMutate, isPending: false };
      }
      if (fn.includes("/complete")) {
        return { mutate: mockCompleteMutate, isPending: false };
      }
      if (fn.includes("/fail")) {
        return { mutate: mockFailMutate, isPending: false };
      }
      return { mutate: mockRefundMutate, isPending: false };
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

const PAYMENT_PENDING = {
  payment_id: "pay-001",
  tenant_id: 5,
  student_id: "stu-1",
  amount: 15000,
  currency: "KZT",
  method: "KASPI",
  description: "Tuition",
  status: "PENDING",
  created_at: "2026-05-01T10:00:00Z",
};

const PAYMENT_PROCESSING = {
  ...PAYMENT_PENDING,
  payment_id: "pay-002",
  student_id: "stu-2",
  status: "PROCESSING",
};

const PAYMENT_COMPLETED = {
  ...PAYMENT_PENDING,
  payment_id: "pay-003",
  student_id: "stu-3",
  status: "COMPLETED",
  transaction_ref: "TXN-999",
};

const PAYMENT_FAILED = {
  ...PAYMENT_PENDING,
  payment_id: "pay-004",
  student_id: "stu-4",
  status: "FAILED",
  reason: "Insufficient funds",
};

function setupDefaults() {
  mockUseTenantsQuery.mockReturnValue({
    data: { tenants: TENANTS },
    isLoading: false,
  });
  mockUsePaymentsQuery.mockReturnValue({
    data: {
      payments: [PAYMENT_PENDING, PAYMENT_PROCESSING, PAYMENT_COMPLETED, PAYMENT_FAILED],
    },
    isLoading: false,
    error: null,
  });
  mockUseTenantLocale.mockReturnValue(KZT_LOCALE);
}

// ---------- tests ----------

describe("PaymentsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaults();
  });

  it("renders page heading", () => {
    render(<PaymentsPage />);
    expect(screen.getByText("Online Payments")).toBeInTheDocument();
  });

  it("renders tenant selector", () => {
    render(<PaymentsPage />);
    expect(screen.getByRole("combobox", { name: /select tenant/i })).toBeInTheDocument();
  });

  it("shows tenant options in selector", () => {
    render(<PaymentsPage />);
    expect(screen.getByText("Alpha University")).toBeInTheDocument();
  });

  it("does not show stats before tenant is selected", () => {
    render(<PaymentsPage />);
    expect(screen.queryByText("Total Payments")).not.toBeInTheDocument();
  });

  it("shows stat cards after tenant is selected", () => {
    render(<PaymentsPage />);
    fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
      target: { value: "5" },
    });
    expect(screen.getByText("Total Payments")).toBeInTheDocument();
    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getByText("In Progress")).toBeInTheDocument();
    expect(screen.getByText("Failed")).toBeInTheDocument();
  });

  it("shows correct stat counts", () => {
    render(<PaymentsPage />);
    fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
      target: { value: "5" },
    });
    // 4 payments total
    expect(screen.getByText("4")).toBeInTheDocument();
    // multiple "1"s are expected (completed=1, failed=1)
    expect(screen.getAllByText("1").length).toBeGreaterThanOrEqual(2);
    // in progress = PENDING + PROCESSING = 2
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("shows status badges for payments", () => {
    render(<PaymentsPage />);
    fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
      target: { value: "5" },
    });
    expect(screen.getAllByText("PENDING").length > 0).toBe(true);
    expect(screen.getAllByText("COMPLETED").length > 0).toBe(true);
    expect(screen.getAllByText("FAILED").length > 0).toBe(true);
  });

  it("shows Process button for PENDING payment", () => {
    render(<PaymentsPage />);
    fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
      target: { value: "5" },
    });
    expect(screen.getByRole("button", { name: /process pay-001/i })).toBeInTheDocument();
  });

  it("shows Complete and Fail buttons for PROCESSING payment", () => {
    render(<PaymentsPage />);
    fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
      target: { value: "5" },
    });
    expect(screen.getByRole("button", { name: /complete pay-002/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /fail pay-002/i })).toBeInTheDocument();
  });

  it("shows Refund button for COMPLETED payment", () => {
    render(<PaymentsPage />);
    fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
      target: { value: "5" },
    });
    expect(screen.getByRole("button", { name: /refund pay-003/i })).toBeInTheDocument();
  });

  it("shows Complete dialog when Complete button is clicked", () => {
    render(<PaymentsPage />);
    fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
      target: { value: "5" },
    });
    fireEvent.click(screen.getByRole("button", { name: /complete pay-002/i }));
    expect(screen.getByText("Complete Payment")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: /transaction reference/i })).toBeInTheDocument();
  });

  it("shows Fail dialog when Fail button is clicked", () => {
    render(<PaymentsPage />);
    fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
      target: { value: "5" },
    });
    fireEvent.click(screen.getByRole("button", { name: /fail pay-002/i }));
    expect(screen.getByText("Fail Payment")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: /fail reason/i })).toBeInTheDocument();
  });

  it("shows Refund dialog when Refund button is clicked", () => {
    render(<PaymentsPage />);
    fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
      target: { value: "5" },
    });
    fireEvent.click(screen.getByRole("button", { name: /refund pay-003/i }));
    expect(screen.getByText("Refund Payment")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: /refund reason/i })).toBeInTheDocument();
  });

  it("shows status filter dropdown", () => {
    render(<PaymentsPage />);
    fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
      target: { value: "5" },
    });
    expect(screen.getByRole("combobox", { name: /filter by status/i })).toBeInTheDocument();
  });

  it("shows error state when payments fail to load", () => {
    mockUsePaymentsQuery.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("Network error"),
    });
    render(<PaymentsPage />);
    fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
      target: { value: "5" },
    });
    expect(screen.getByText(/failed to load payments/i)).toBeInTheDocument();
  });
});
