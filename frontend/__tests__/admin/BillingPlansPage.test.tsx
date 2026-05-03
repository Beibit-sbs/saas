import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import BillingPlansPage from "../../app/(admin)/console/billing/plans/page";

// --- navigation mock ---
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/console/billing/plans",
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
const mockUsePlanStatsQuery = vi.fn();
const mockCreateMutate = vi.fn();
const mockUpdateMutate = vi.fn();
const mockDeactivateMutate = vi.fn();

vi.mock("@tanstack/react-query", async (importActual) => {
  const actual = await importActual<typeof import("@tanstack/react-query")>();
  let mutationIndex = 0;
  return {
    ...actual,
    useQuery: (...args: Parameters<typeof actual.useQuery>) => {
      const opts = args[0] as { queryKey: unknown[] };
      if (Array.isArray(opts.queryKey)) {
        if (opts.queryKey[0] === "billing-plans") return mockUsePlansQuery();
        if (opts.queryKey[0] === "billing-plans-stats") return mockUsePlanStatsQuery();
      }
      return { data: undefined, isLoading: false, error: null };
    },
    useMutation: () => {
      const mutations = [
        { mutate: mockCreateMutate, isPending: false },
        { mutate: mockUpdateMutate, isPending: false },
        { mutate: mockDeactivateMutate, isPending: false },
      ];
      const idx = mutationIndex % mutations.length;
      mutationIndex++;
      return mutations[idx];
    },
    useQueryClient: () => ({ invalidateQueries: vi.fn() }),
  };
});

vi.mock("../../shared/api/client", () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
}));

// --- fixtures ---

const PLANS: import("../../app/(admin)/console/billing/plans/page").PlanRow[] = [
  { id: 1, code: "free", name: "Free", description: "Starter plan", active: true },
  { id: 2, code: "pro", name: "Pro", description: "Professional", active: true },
  { id: 3, code: "old", name: "Old Plan", description: "Deprecated", active: false },
];

const STATS = { total: 3, active: 2, inactive: 1 };

function setupQueries(plans = PLANS, stats = STATS) {
  mockUsePlansQuery.mockReturnValue({ data: { plans }, isLoading: false, error: null });
  mockUsePlanStatsQuery.mockReturnValue({ data: stats, isLoading: false, error: null });
}

// ─── tests ────────────────────────────────────────────────────────────────────

describe("BillingPlansPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCreateMutate.mockReset();
    mockUpdateMutate.mockReset();
    mockDeactivateMutate.mockReset();
  });

  it("renders page header", () => {
    setupQueries();
    render(<BillingPlansPage />);
    expect(screen.getByText("Billing Plans")).toBeInTheDocument();
  });

  it("renders page description", () => {
    setupQueries();
    render(<BillingPlansPage />);
    expect(screen.getByText(/Manage subscription plans/i)).toBeInTheDocument();
  });

  it("shows total plans stat card", () => {
    setupQueries();
    render(<BillingPlansPage />);
    expect(screen.getByText("Total Plans")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("shows active plans stat card", () => {
    setupQueries();
    render(<BillingPlansPage />);
    expect(screen.getByText("Active Plans")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("shows inactive plans stat card", () => {
    setupQueries();
    render(<BillingPlansPage />);
    expect(screen.getByText("Inactive Plans")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
  });

  it("renders plan codes in table", () => {
    setupQueries();
    render(<BillingPlansPage />);
    expect(screen.getByText("free")).toBeInTheDocument();
    expect(screen.getByText("pro")).toBeInTheDocument();
  });

  it("renders plan names in table", () => {
    setupQueries();
    render(<BillingPlansPage />);
    expect(screen.getByText("Free")).toBeInTheDocument();
    expect(screen.getByText("Pro")).toBeInTheDocument();
  });

  it("renders active badges", () => {
    setupQueries();
    render(<BillingPlansPage />);
    const activeBadges = screen.getAllByText("Active");
    expect(activeBadges.length).toBeGreaterThanOrEqual(2);
  });

  it("renders inactive badge for inactive plan", () => {
    setupQueries();
    render(<BillingPlansPage />);
    expect(screen.getByText("Inactive")).toBeInTheDocument();
  });

  it("renders Edit buttons for plans", () => {
    setupQueries();
    render(<BillingPlansPage />);
    const editBtns = screen.getAllByRole("button", { name: /Edit/i });
    expect(editBtns.length).toBe(3);
  });

  it("renders Deactivate buttons only for active plans", () => {
    setupQueries();
    render(<BillingPlansPage />);
    const deactivateBtns = screen.getAllByRole("button", { name: /Deactivate/i });
    expect(deactivateBtns.length).toBe(2);
  });

  it("renders New Plan button", () => {
    setupQueries();
    render(<BillingPlansPage />);
    expect(screen.getByRole("button", { name: /New Plan/i })).toBeInTheDocument();
  });

  it("renders show inactive checkbox", () => {
    setupQueries();
    render(<BillingPlansPage />);
    expect(screen.getByRole("checkbox", { name: /Show inactive plans/i })).toBeInTheDocument();
  });

  it("opens create modal on New Plan click", () => {
    setupQueries();
    render(<BillingPlansPage />);
    fireEvent.click(screen.getByRole("button", { name: /New Plan/i }));
    expect(screen.getByRole("dialog", { name: "Create Plan" })).toBeInTheDocument();
  });

  it("create modal has code/name/description inputs", () => {
    setupQueries();
    render(<BillingPlansPage />);
    fireEvent.click(screen.getByRole("button", { name: /New Plan/i }));
    expect(screen.getByRole("textbox", { name: /Plan code/i })).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: /Plan name/i })).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: /Plan description/i })).toBeInTheDocument();
  });

  it("create modal Cancel closes modal", () => {
    setupQueries();
    render(<BillingPlansPage />);
    fireEvent.click(screen.getByRole("button", { name: /New Plan/i }));
    fireEvent.click(screen.getByRole("button", { name: /Cancel/i }));
    expect(screen.queryByRole("dialog", { name: "Create Plan" })).not.toBeInTheDocument();
  });

  it("opens edit modal when Edit is clicked", () => {
    setupQueries();
    render(<BillingPlansPage />);
    const editBtns = screen.getAllByRole("button", { name: /Edit/i });
    fireEvent.click(editBtns[0]);
    expect(screen.getByRole("dialog", { name: "Edit Plan" })).toBeInTheDocument();
  });

  it("edit modal shows plan code", () => {
    setupQueries();
    render(<BillingPlansPage />);
    fireEvent.click(screen.getAllByRole("button", { name: /Edit/i })[0]);
    expect(screen.getAllByText("free").length).toBeGreaterThanOrEqual(1);
  });

  it("edit modal has name and description inputs", () => {
    setupQueries();
    render(<BillingPlansPage />);
    fireEvent.click(screen.getAllByRole("button", { name: /Edit/i })[0]);
    expect(screen.getByRole("textbox", { name: /Edit plan name/i })).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: /Edit plan description/i })).toBeInTheDocument();
  });

  it("edit modal Cancel closes modal", () => {
    setupQueries();
    render(<BillingPlansPage />);
    fireEvent.click(screen.getAllByRole("button", { name: /Edit/i })[0]);
    fireEvent.click(screen.getByRole("button", { name: /Cancel/i }));
    expect(screen.queryByRole("dialog", { name: "Edit Plan" })).not.toBeInTheDocument();
  });

  it("shows error state when query fails", () => {
    mockUsePlansQuery.mockReturnValue({ data: null, isLoading: false, error: new Error("fail") });
    mockUsePlanStatsQuery.mockReturnValue({ data: null, isLoading: false, error: null });
    render(<BillingPlansPage />);
    expect(screen.getByText(/Failed to load billing plans/i)).toBeInTheDocument();
  });

  it("shows zero stats when data is absent", () => {
    mockUsePlansQuery.mockReturnValue({ data: { plans: [] }, isLoading: false, error: null });
    mockUsePlanStatsQuery.mockReturnValue({ data: null, isLoading: false, error: null });
    render(<BillingPlansPage />);
    const zeros = screen.getAllByText("0");
    expect(zeros.length).toBeGreaterThanOrEqual(3);
  });
});
