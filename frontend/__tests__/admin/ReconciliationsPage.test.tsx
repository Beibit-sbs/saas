import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import ReconciliationsPage from "../../app/(admin)/console/billing/reconciliations/page";

// --- navigation mock ---
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/console/billing/reconciliations",
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
const mockUseRecsQuery = vi.fn();
const mockCancelMutate = vi.fn();
const mockAutoMutate = vi.fn();

vi.mock("@tanstack/react-query", async (importActual) => {
  const actual = await importActual<typeof import("@tanstack/react-query")>();
  return {
    ...actual,
    useQuery: (...args: Parameters<typeof actual.useQuery>) => {
      const opts = args[0] as { queryKey: unknown[] };
      if (Array.isArray(opts.queryKey)) {
        if (opts.queryKey[0] === "tenants") return mockUseTenantsQuery();
        if (opts.queryKey[0] === "reconciliations") return mockUseRecsQuery();
      }
      return { data: undefined, isLoading: false, error: null };
    },
    useMutation: (...args: Parameters<typeof actual.useMutation>) => {
      const opts = args[0] as { mutationFn: (v: unknown) => unknown };
      const fn = opts?.mutationFn?.toString() ?? "";
      if (fn.includes("/cancel")) {
        return { mutate: mockCancelMutate, isPending: false };
      }
      return { mutate: mockAutoMutate, isPending: false };
    },
    useQueryClient: () => ({ invalidateQueries: vi.fn() }),
  };
});

// --- api mock ---
vi.mock("../../shared/api/client", () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
}));

// --- fixtures ---

const TENANTS = [{ id: 5, slug: "alpha", name: "Alpha University" }];

const REC_ACTIVE: import("../../app/(admin)/console/billing/reconciliations/page").Reconciliation =
  {
    id: "rec-0001-aaaa-bbbb-cccc",
    tenant_id: 5,
    payment_id: "pay-001",
    invoice_id: "inv-001",
    status: "active",
    notes: "Matched automatically",
    created_at: "2026-06-01T08:00:00Z",
    cancelled_at: null,
    cancel_reason: null,
  };

const REC_CANCELLED: import("../../app/(admin)/console/billing/reconciliations/page").Reconciliation =
  {
    id: "rec-0002-aaaa-bbbb-dddd",
    tenant_id: 5,
    payment_id: "pay-002",
    invoice_id: "inv-002",
    status: "cancelled",
    notes: "",
    created_at: "2026-05-15T10:00:00Z",
    cancelled_at: "2026-05-20T12:00:00Z",
    cancel_reason: "Duplicate entry",
  };

function setupTenants() {
  mockUseTenantsQuery.mockReturnValue({
    data: { tenants: TENANTS },
    isLoading: false,
    error: null,
  });
}

function setupRecs(recs = [REC_ACTIVE, REC_CANCELLED]) {
  mockUseRecsQuery.mockReturnValue({
    data: { reconciliations: recs },
    isLoading: false,
    error: null,
  });
}

function setupEmpty() {
  mockUseTenantsQuery.mockReturnValue({
    data: { tenants: [] },
    isLoading: false,
    error: null,
  });
  mockUseRecsQuery.mockReturnValue({
    data: { reconciliations: [] },
    isLoading: false,
    error: null,
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  setupTenants();
  setupRecs();
});

// --- helpers ---
function renderPage() {
  return render(<ReconciliationsPage />);
}

function selectTenant() {
  const sel = screen.getByRole("combobox", { name: /select tenant/i });
  fireEvent.change(sel, { target: { value: "5" } });
}

// ----------------------------------------------------------------
describe("ReconciliationsPage — Phase LXXII", () => {
  // 1. Page header
  it("renders page header title", () => {
    renderPage();
    expect(screen.getByText("Payment Reconciliations")).toBeTruthy();
  });

  // 2. Tenant selector present
  it("renders tenant selector", () => {
    renderPage();
    expect(screen.getByRole("combobox", { name: /select tenant/i })).toBeTruthy();
  });

  // 3. Tenant option visible
  it("lists tenant options", () => {
    renderPage();
    expect(screen.getByText("Alpha University")).toBeTruthy();
  });

  // 4. No stats before tenant selected
  it("does not show stat cards before tenant is selected", () => {
    renderPage();
    expect(screen.queryByText("Total")).toBeNull();
  });

  // 5. Stat cards appear after tenant select
  it("shows stat cards after selecting tenant", () => {
    renderPage();
    selectTenant();
    expect(screen.getByText("Total")).toBeTruthy();
    // Active/Cancelled appear in filter options + stat card + badge; use getAllByText
    expect(screen.getAllByText("Active").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Cancelled").length).toBeGreaterThanOrEqual(1);
  });

  // 6. Correct totals
  it("shows correct stat counts", () => {
    renderPage();
    selectTenant();
    // total=2, active=1, cancelled=1
    const twos = screen.getAllByText("2");
    expect(twos.length).toBeGreaterThanOrEqual(1);
    const ones = screen.getAllByText("1");
    expect(ones.length).toBeGreaterThanOrEqual(2);
  });

  // 7. DataTable renders payment_id column
  it("renders payment IDs in table", () => {
    renderPage();
    selectTenant();
    expect(screen.getByText("pay-001")).toBeTruthy();
    expect(screen.getByText("pay-002")).toBeTruthy();
  });

  // 8. DataTable renders invoice_id column
  it("renders invoice IDs in table", () => {
    renderPage();
    selectTenant();
    expect(screen.getByText("inv-001")).toBeTruthy();
    expect(screen.getByText("inv-002")).toBeTruthy();
  });

  // 9. Active badge visible
  it("shows Active status badge for active reconciliation", () => {
    renderPage();
    selectTenant();
    // Active appears in filter option, stat card label, and badge
    expect(screen.getAllByText("Active").length).toBeGreaterThanOrEqual(2);
  });

  // 10. Cancelled badge visible
  it("shows Cancelled status badge for cancelled reconciliation", () => {
    renderPage();
    selectTenant();
    // Cancelled appears in filter option, stat card label, and badge
    expect(screen.getAllByText("Cancelled").length).toBeGreaterThanOrEqual(2);
  });

  // 11. Cancel button visible only for active
  it("shows Cancel button only for active reconciliations", () => {
    renderPage();
    selectTenant();
    const cancelButtons = screen.getAllByRole("button", { name: /cancel/i });
    // Only one active rec → one cancel button
    expect(cancelButtons.length).toBe(1);
  });

  // 12. Cancel modal opens on Cancel click
  it("opens cancel modal when Cancel button is clicked", () => {
    renderPage();
    selectTenant();
    const [cancelBtn] = screen.getAllByRole("button", { name: /cancel/i });
    fireEvent.click(cancelBtn);
    expect(screen.getByRole("dialog", { name: /cancel reconciliation/i })).toBeTruthy();
  });

  // 13. Back button closes cancel modal
  it("closes cancel modal on Back click", () => {
    renderPage();
    selectTenant();
    const [cancelBtn] = screen.getAllByRole("button", { name: /cancel/i });
    fireEvent.click(cancelBtn);
    fireEvent.click(screen.getByRole("button", { name: /back/i }));
    expect(screen.queryByRole("dialog", { name: /cancel reconciliation/i })).toBeNull();
  });

  // 14. Auto Reconcile button appears after tenant selected
  it("shows Auto Reconcile button after tenant selection", () => {
    renderPage();
    selectTenant();
    expect(screen.getByRole("button", { name: /auto reconcile/i })).toBeTruthy();
  });

  // 15. Auto-reconcile modal opens
  it("opens auto-reconcile modal when button clicked", () => {
    renderPage();
    selectTenant();
    fireEvent.click(screen.getByRole("button", { name: /auto reconcile/i }));
    expect(screen.getByRole("dialog", { name: /auto reconcile/i })).toBeTruthy();
  });

  // 16. Auto-reconcile modal closes on Back
  it("closes auto-reconcile modal on Back click", () => {
    renderPage();
    selectTenant();
    fireEvent.click(screen.getByRole("button", { name: /auto reconcile/i }));
    fireEvent.click(screen.getByRole("button", { name: /back/i }));
    expect(screen.queryByRole("dialog", { name: /auto reconcile/i })).toBeNull();
  });

  // 17. Status filter combobox present
  it("renders status filter combobox", () => {
    renderPage();
    expect(screen.getByRole("combobox", { name: /filter by status/i })).toBeTruthy();
  });

  // 18. Notes rendered in table
  it("renders notes in table", () => {
    renderPage();
    selectTenant();
    expect(screen.getByText("Matched automatically")).toBeTruthy();
  });

  // 19. Empty notes shows dash
  it("shows dash for empty notes", () => {
    setupRecs([REC_CANCELLED]);
    renderPage();
    selectTenant();
    const dashes = screen.getAllByText("—");
    expect(dashes.length).toBeGreaterThanOrEqual(1);
  });

  // 20. Empty tenant list shows default option only
  it("shows default option when no tenants", () => {
    setupEmpty();
    renderPage();
    expect(screen.getByText("— Select tenant —")).toBeTruthy();
  });
});
