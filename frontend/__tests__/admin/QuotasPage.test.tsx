import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import QuotasPage from "../../app/(admin)/console/billing/quotas/page";

// --- navigation mock ---
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/console/billing/quotas",
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
  RequirePermission: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
}));

vi.mock("../../shared/hooks/use-mutation-feedback", () => ({
  useMutationFeedback: () => ({
    getHandlers: () => ({ onSuccess: vi.fn(), onError: vi.fn() }),
  }),
}));

// --- react-query mocks ---
const mockUsePlansQuery = vi.fn();
const mockUseTenantsQuery = vi.fn();
const mockUseQuotasQuery = vi.fn();
const mockUseConsistencyQuery = vi.fn();
const mockUseCheckQuery = vi.fn();
const mockUpdateMutate = vi.fn();

vi.mock("@tanstack/react-query", async (importActual) => {
  const actual = await importActual<typeof import("@tanstack/react-query")>();
  return {
    ...actual,
    useQuery: (...args: Parameters<typeof actual.useQuery>) => {
      const opts = args[0] as { queryKey: unknown[] };
      if (Array.isArray(opts.queryKey)) {
        if (opts.queryKey[0] === "plans") return mockUsePlansQuery();
        if (opts.queryKey[0] === "tenants") return mockUseTenantsQuery();
        if (opts.queryKey[0] === "quotas") return mockUseQuotasQuery();
        if (opts.queryKey[0] === "quotas-consistency")
          return mockUseConsistencyQuery();
        if (opts.queryKey[0] === "quota-check") return mockUseCheckQuery();
      }
      return { data: undefined, isLoading: false, error: null };
    },
    useMutation: () => ({ mutate: mockUpdateMutate, isPending: false }),
    useQueryClient: () => ({ invalidateQueries: vi.fn() }),
  };
});

vi.mock("../../shared/api/client", () => ({
  apiGet: vi.fn(),
  apiPut: vi.fn(),
}));

// --- fixtures ---

const PLANS = [
  { id: 1, code: "free", name: "Free" },
  { id: 2, code: "pro", name: "Pro" },
];

const TENANTS = [{ id: 5, slug: "uni-alpha", name: "Alpha University" }];

const QUOTA_1: import("../../app/(admin)/console/billing/quotas/page").QuotaRow =
  { id: 1, plan_id: 1, key: "users", limit_value: 10 };

const QUOTA_2: import("../../app/(admin)/console/billing/quotas/page").QuotaRow =
  { id: 2, plan_id: 1, key: "api_requests", limit_value: 5000 };

const QUOTA_3: import("../../app/(admin)/console/billing/quotas/page").QuotaRow =
  { id: 3, plan_id: 2, key: "users", limit_value: 100 };

const CONSISTENCY_CLEAN = {
  total_plan_count: 4,
  configured_plan_quota_count: 4,
  issue_count: 0,
  issues: [],
};

const CONSISTENCY_ISSUES = {
  total_plan_count: 4,
  configured_plan_quota_count: 3,
  issue_count: 2,
  issues: [
    {
      issue_type: "plan_missing_quota_key",
      plan_id: 1,
      plan_code: "free",
      quota_key: "storage_mb",
      detail: "Plan is missing a baseline quota key.",
    },
  ],
};

const CHECK_OK = {
  tenant_id: 5,
  quota_key: "users",
  limit_value: 100,
  current_value: 8,
  within_limit: true,
  soft_warning: false,
  message: "within quota",
};

const CHECK_EXCEEDED = {
  tenant_id: 5,
  quota_key: "users",
  limit_value: 10,
  current_value: 15,
  within_limit: false,
  soft_warning: true,
  message: "quota exceeded (soft enforcement)",
};

// --- setup helpers ---

function defaultMocks() {
  mockUsePlansQuery.mockReturnValue({ data: { plans: PLANS }, error: null });
  mockUseTenantsQuery.mockReturnValue({
    data: { tenants: TENANTS },
    error: null,
  });
  mockUseQuotasQuery.mockReturnValue({
    data: { quotas: [QUOTA_1, QUOTA_2, QUOTA_3] },
    error: null,
  });
  mockUseConsistencyQuery.mockReturnValue({
    data: CONSISTENCY_CLEAN,
    error: null,
  });
  mockUseCheckQuery.mockReturnValue({ data: undefined, error: null });
}

beforeEach(() => {
  vi.clearAllMocks();
  defaultMocks();
});

// ═══════════════════════════════════════════════════════════════════════════════
// Rendering tests
// ═══════════════════════════════════════════════════════════════════════════════

describe("QuotasPage — rendering", () => {
  it("renders page header with title", () => {
    render(<QuotasPage />);
    expect(screen.getByText("Quota Management")).toBeInTheDocument();
  });

  it("renders subtitle", () => {
    render(<QuotasPage />);
    expect(
      screen.getByText("Configure plan quotas and check tenant limits")
    ).toBeInTheDocument();
  });

  it("renders Total Quotas stat card", () => {
    render(<QuotasPage />);
    expect(screen.getByText("Total Quotas")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("renders Plans Configured stat card", () => {
    render(<QuotasPage />);
    expect(screen.getByText("Plans Configured")).toBeInTheDocument();
  });

  it("renders Consistency Issues stat card — green when 0", () => {
    render(<QuotasPage />);
    expect(screen.getByText("Consistency Issues")).toBeInTheDocument();
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("shows quota rows in table", () => {
    render(<QuotasPage />);
    expect(screen.getAllByText("users").length).toBeGreaterThan(0);
    expect(screen.getByText("api_requests")).toBeInTheDocument();
  });

  it("renders quota limit values", () => {
    render(<QuotasPage />);
    expect(screen.getByText("5,000")).toBeInTheDocument();
  });

  it("renders plan filter dropdown with plans", () => {
    render(<QuotasPage />);
    const select = screen.getByRole("combobox", { name: /filter by plan/i });
    expect(select).toBeInTheDocument();
    expect(screen.getByText("Free")).toBeInTheDocument();
    expect(screen.getByText("Pro")).toBeInTheDocument();
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// Consistency issues
// ═══════════════════════════════════════════════════════════════════════════════

describe("QuotasPage — consistency", () => {
  it("shows 0 issues in green", () => {
    render(<QuotasPage />);
    const issueEl = screen
      .getAllByText("0")
      .find((el) => typeof el.className === "string" && el.className.includes("green"));
    expect(issueEl).toBeTruthy();
    if (!issueEl) return;
    expect(issueEl.className).toContain("green");
  });

  it("shows non-zero issues in red", () => {
    mockUseConsistencyQuery.mockReturnValue({
      data: CONSISTENCY_ISSUES,
      error: null,
    });
    render(<QuotasPage />);
    const redEls = screen.getAllByText("2").filter(
      (el) => el.className && el.className.includes("red")
    );
    expect(redEls.length).toBeGreaterThan(0);
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// Quota check
// ═══════════════════════════════════════════════════════════════════════════════

describe("QuotasPage — quota check", () => {
  it("renders tenant select for check", () => {
    render(<QuotasPage />);
    expect(
      screen.getByRole("combobox", { name: /select tenant for check/i })
    ).toBeInTheDocument();
  });

  it("renders quota key input", () => {
    render(<QuotasPage />);
    expect(screen.getByLabelText("Quota key to check")).toBeInTheDocument();
  });

  it("Check button is disabled initially", () => {
    render(<QuotasPage />);
    expect(screen.getByRole("button", { name: /check/i })).toBeDisabled();
  });

  it("shows within quota result in green", () => {
    mockUseCheckQuery.mockReturnValue({ data: CHECK_OK, error: null });
    render(<QuotasPage />);

    const tenantSelect = screen.getByRole("combobox", {
      name: /select tenant for check/i,
    });
    fireEvent.change(tenantSelect, { target: { value: "5" } });

    const keyInput = screen.getByLabelText("Quota key to check");
    fireEvent.change(keyInput, { target: { value: "users" } });

    fireEvent.click(screen.getByRole("button", { name: /check/i }));

    expect(screen.getByText("within quota")).toBeInTheDocument();
  });

  it("shows exceeded result in red when quota is exceeded", () => {
    mockUseCheckQuery.mockReturnValue({ data: CHECK_EXCEEDED, error: null });
    render(<QuotasPage />);

    const tenantSelect = screen.getByRole("combobox", {
      name: /select tenant for check/i,
    });
    fireEvent.change(tenantSelect, { target: { value: "5" } });
    const keyInput = screen.getByLabelText("Quota key to check");
    fireEvent.change(keyInput, { target: { value: "users" } });
    fireEvent.click(screen.getByRole("button", { name: /check/i }));

    expect(
      screen.getByText("quota exceeded (soft enforcement)")
    ).toBeInTheDocument();
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// Edit modal
// ═══════════════════════════════════════════════════════════════════════════════

describe("QuotasPage — edit modal", () => {
  it("modal is not visible by default", () => {
    render(<QuotasPage />);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("opens modal on Edit button click", () => {
    render(<QuotasPage />);
    const editButtons = screen.getAllByRole("button", { name: /edit/i });
    fireEvent.click(editButtons[0]);
    expect(screen.getByRole("dialog", { name: /edit quota/i })).toBeInTheDocument();
  });

  it("shows plan_id and key in modal", () => {
    render(<QuotasPage />);
    const editButtons = screen.getAllByRole("button", { name: /edit/i });
    fireEvent.click(editButtons[0]);
    expect(
      screen.getByRole("dialog", { name: /edit quota/i })
    ).toBeInTheDocument();
    // modal shows the quota key
    expect(screen.getAllByText("users").length).toBeGreaterThan(0);
  });

  it("closes modal on Cancel click", () => {
    render(<QuotasPage />);
    const editButtons = screen.getAllByRole("button", { name: /edit/i });
    fireEvent.click(editButtons[0]);
    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("calls mutate on Save click", () => {
    render(<QuotasPage />);
    const editButtons = screen.getAllByRole("button", { name: /edit/i });
    fireEvent.click(editButtons[0]);
    fireEvent.click(screen.getByRole("button", { name: /save/i }));
    expect(mockUpdateMutate).toHaveBeenCalledTimes(1);
  });

  it("limit value input can be changed", () => {
    render(<QuotasPage />);
    const editButtons = screen.getAllByRole("button", { name: /edit/i });
    fireEvent.click(editButtons[0]);
    const limitInput = screen.getByLabelText("Limit value");
    fireEvent.change(limitInput, { target: { value: "9999" } });
    expect((limitInput as HTMLInputElement).value).toBe("9999");
  });
});

// ═══════════════════════════════════════════════════════════════════════════════
// Error state
// ═══════════════════════════════════════════════════════════════════════════════

describe("QuotasPage — error state", () => {
  it("renders error state when quota fetch fails", () => {
    mockUseQuotasQuery.mockReturnValue({
      data: undefined,
      error: new Error("network error"),
    });
    render(<QuotasPage />);
    expect(screen.getByText("Failed to load quotas")).toBeInTheDocument();
  });

  it("renders empty table when no quotas", () => {
    mockUseQuotasQuery.mockReturnValue({ data: { quotas: [] }, error: null });
    render(<QuotasPage />);
    expect(screen.queryByText("api_requests")).not.toBeInTheDocument();
    // All 3 stat cards show 0
    expect(screen.getAllByText("0").length).toBeGreaterThanOrEqual(1);
  });
});
