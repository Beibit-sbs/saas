import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import UsagePage from "../../app/(admin)/console/billing/usage/page";

// --- navigation mock ---
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/console/billing/usage",
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
const mockUseTenantsQuery = vi.fn();
const mockUseEventsQuery = vi.fn();
const mockUseSumQuery = vi.fn();
const mockRecordMutate = vi.fn();

vi.mock("@tanstack/react-query", async (importActual) => {
  const actual = await importActual<typeof import("@tanstack/react-query")>();
  return {
    ...actual,
    useQuery: (...args: Parameters<typeof actual.useQuery>) => {
      const opts = args[0] as { queryKey: unknown[] };
      if (Array.isArray(opts.queryKey)) {
        if (opts.queryKey[0] === "tenants") return mockUseTenantsQuery();
        if (opts.queryKey[0] === "usage-events") return mockUseEventsQuery();
        if (opts.queryKey[0] === "usage-sum") return mockUseSumQuery();
      }
      return { data: undefined, isLoading: false, error: null };
    },
    useMutation: () => ({ mutate: mockRecordMutate, isPending: false }),
    useQueryClient: () => ({ invalidateQueries: vi.fn() }),
  };
});

vi.mock("../../shared/api/client", () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
}));

// --- fixtures ---

const TENANTS = [{ id: 7, slug: "beta", name: "Beta College" }];

const EVENT_1: import("../../app/(admin)/console/billing/usage/page").UsageEvent =
  {
    id: 1,
    tenant_id: 7,
    metric: "ai_requests",
    value: 5,
    created_at: "2026-06-01T10:00:00Z",
  };

const EVENT_2: import("../../app/(admin)/console/billing/usage/page").UsageEvent =
  {
    id: 2,
    tenant_id: 7,
    metric: "logins",
    value: 3,
    created_at: "2026-05-15T09:00:00Z",
  };

// --- helpers ---

function renderPage() {
  mockUseTenantsQuery.mockReturnValue({
    data: { tenants: TENANTS },
    isLoading: false,
    error: null,
  });
  mockUseEventsQuery.mockReturnValue({
    data: { events: [EVENT_1, EVENT_2] },
    isLoading: false,
    error: null,
  });
  mockUseSumQuery.mockReturnValue({
    data: undefined,
    isLoading: false,
    error: null,
  });
  render(<UsagePage />);
}

function selectTenant() {
  fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
    target: { value: "7" },
  });
}

// =============================================================================
describe("UsagePage — Phase LXXIV", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // 1
  it("renders page title", () => {
    renderPage();
    expect(screen.getByText("Usage Tracking")).toBeTruthy();
  });

  // 2
  it("renders tenant selector", () => {
    renderPage();
    expect(
      screen.getByRole("combobox", { name: /select tenant/i })
    ).toBeTruthy();
  });

  // 3
  it("renders tenant name in selector", () => {
    renderPage();
    expect(screen.getByText("Beta College")).toBeTruthy();
  });

  // 4
  it("does not show stat cards before tenant selection", () => {
    renderPage();
    expect(screen.queryByText("Total Events")).toBeNull();
  });

  // 5
  it("shows stat cards after selecting tenant", () => {
    renderPage();
    selectTenant();
    expect(screen.getByText("Total Events")).toBeTruthy();
    expect(screen.getByText("Unique Metrics")).toBeTruthy();
    expect(screen.getByText("Total Value")).toBeTruthy();
  });

  // 6
  it("shows correct total events count", () => {
    renderPage();
    selectTenant();
    // 2 events
    const twos = screen.getAllByText("2");
    expect(twos.length).toBeGreaterThanOrEqual(1);
  });

  // 7
  it("shows correct unique metrics count", () => {
    renderPage();
    selectTenant();
    // 2 unique metrics: ai_requests + logins
    const twos = screen.getAllByText("2");
    expect(twos.length).toBeGreaterThanOrEqual(1);
  });

  // 8
  it("shows correct total value", () => {
    renderPage();
    selectTenant();
    // total = 5 + 3 = 8
    expect(screen.getByText("8")).toBeTruthy();
  });

  // 9
  it("renders metric column in table", () => {
    renderPage();
    selectTenant();
    expect(screen.getByText("ai_requests")).toBeTruthy();
    expect(screen.getByText("logins")).toBeTruthy();
  });

  // 10
  it("renders value column in table", () => {
    renderPage();
    selectTenant();
    expect(screen.getByText("5")).toBeTruthy();
    expect(screen.getByText("3")).toBeTruthy();
  });

  // 11
  it("renders metric filter input", () => {
    renderPage();
    expect(
      screen.getByRole("textbox", { name: /filter by metric/i })
    ).toBeTruthy();
  });

  // 12
  it("renders metric-for-sum input after tenant selected", () => {
    renderPage();
    selectTenant();
    expect(
      screen.getByRole("textbox", { name: /metric for sum/i })
    ).toBeTruthy();
  });

  // 13
  it("shows Record Event button after tenant selected", () => {
    renderPage();
    selectTenant();
    expect(
      screen.getByRole("button", { name: /record event/i })
    ).toBeTruthy();
  });

  // 14
  it("does not show Record Event button before tenant selected", () => {
    renderPage();
    expect(
      screen.queryByRole("button", { name: /record event/i })
    ).toBeNull();
  });

  // 15
  it("opens record event modal when button is clicked", () => {
    renderPage();
    selectTenant();
    fireEvent.click(screen.getByRole("button", { name: /record event/i }));
    expect(
      screen.getByRole("dialog", { name: /record usage event/i })
    ).toBeTruthy();
  });

  // 16
  it("closes record event modal on Back click", () => {
    renderPage();
    selectTenant();
    fireEvent.click(screen.getByRole("button", { name: /record event/i }));
    fireEvent.click(screen.getByRole("button", { name: /back/i }));
    expect(
      screen.queryByRole("dialog", { name: /record usage event/i })
    ).toBeNull();
  });

  // 17
  it("modal has metric and value inputs", () => {
    renderPage();
    selectTenant();
    fireEvent.click(screen.getByRole("button", { name: /record event/i }));
    expect(screen.getByRole("textbox", { name: /event metric/i })).toBeTruthy();
    expect(screen.getByRole("spinbutton", { name: /event value/i })).toBeTruthy();
  });

  // 18
  it("submit button calls recordMutation", () => {
    mockRecordMutate.mockImplementation(
      (_data: unknown, { onSuccess }: { onSuccess: () => void }) => {
        onSuccess();
      }
    );
    renderPage();
    selectTenant();
    fireEvent.click(screen.getByRole("button", { name: /record event/i }));
    fireEvent.change(screen.getByRole("textbox", { name: /event metric/i }), {
      target: { value: "ai_requests" },
    });
    fireEvent.click(screen.getByRole("button", { name: /submit/i }));
    expect(mockRecordMutate).toHaveBeenCalled();
  });

  // 19
  it("shows sum result when sumData is available", () => {
    mockUseTenantsQuery.mockReturnValue({
      data: { tenants: TENANTS },
      isLoading: false,
      error: null,
    });
    mockUseEventsQuery.mockReturnValue({
      data: { events: [] },
      isLoading: false,
      error: null,
    });
    mockUseSumQuery.mockReturnValue({
      data: { tenant_id: 7, metric: "ai_requests", total: 42 },
      isLoading: false,
      error: null,
    });
    render(<UsagePage />);
    fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
      target: { value: "7" },
    });
    expect(screen.getByText("42")).toBeTruthy();
  });

  // 20
  it("shows error state when events query fails", () => {
    mockUseTenantsQuery.mockReturnValue({
      data: { tenants: TENANTS },
      isLoading: false,
      error: null,
    });
    mockUseEventsQuery.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error("network error"),
    });
    mockUseSumQuery.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });
    render(<UsagePage />);
    fireEvent.change(screen.getByRole("combobox", { name: /select tenant/i }), {
      target: { value: "7" },
    });
    expect(screen.getByText(/failed to load usage events/i)).toBeTruthy();
  });
});
