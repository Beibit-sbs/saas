import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import FederationPage from "../../app/(admin)/console/federation/page";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

const useInstitutionsMock = vi.fn();
const useInstitutionOverviewMock = vi.fn();

vi.mock("../../modules/platform/federation/use-federation", () => ({
  useInstitutions: (...args: unknown[]) => useInstitutionsMock(...args),
  useInstitutionOverview: (...args: unknown[]) => useInstitutionOverviewMock(...args),
  useInstitution: vi.fn(() => ({ data: undefined, isLoading: false, isError: false })),
  useCreateInstitution: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
  useLinkTenant: vi.fn(() => ({ mutate: vi.fn(), isPending: false })),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: ReactNode }) => <>{children}</>,
  PermissionGate: ({ children }: { children: ReactNode }) => <>{children}</>,
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

vi.mock("@/app/components/LanguageProvider", async () => {
  const { en: commonEn } = await import("../../i18n/common/en");
  const { en: adminEn } = await import("../../i18n/admin/en");
  const dict = { ...commonEn, ...adminEn } as Record<string, string>;

  return {
    useLanguage: () => ({
      t: (key: string) => dict[key] ?? key,
    }),
  };
});

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const MOCK_INSTITUTIONS = [
  {
    id: 1,
    name: "Alpha University",
    code: "ALPHA",
    country: "Russia",
    type: "university",
    status: "active",
    metadata: {},
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  },
  {
    id: 2,
    name: "Beta College",
    code: "BETA",
    country: "Germany",
    type: "college",
    status: "inactive",
    metadata: {},
    created_at: "2026-01-02T00:00:00Z",
    updated_at: "2026-01-02T00:00:00Z",
  },
];

const MOCK_OVERVIEW = {
  institution: MOCK_INSTITUTIONS[0],
  tenant_count: 3,
  students_total: 1500,
  enrollments_total: 850,
  automation_health: { automation_failures_total: 5 },
  kpi_cards: [
    { metric_key: "institution_students_total", title: "Total Students", value: 1500 },
    { metric_key: "institution_enrollments_total", title: "Total Enrollments", value: 850 },
    { metric_key: "institution_failed_jobs", title: "Failed Jobs", value: 2 },
    { metric_key: "institution_automation_failures", title: "Automation Failures", value: 5 },
  ],
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("FederationPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useInstitutionOverviewMock.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    });
  });

  it("renders the federation page root element", () => {
    useInstitutionsMock.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    });

    render(<FederationPage />);
    expect(screen.getByTestId("federation-page")).toBeInTheDocument();
  });

  it("shows loading state while fetching institutions", () => {
    useInstitutionsMock.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });

    render(<FederationPage />);
    expect(screen.getByText(/loading institutions/i)).toBeInTheDocument();
  });

  it("shows empty state when no institutions registered", () => {
    useInstitutionsMock.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    });

    render(<FederationPage />);
    expect(screen.getByTestId("institution-list")).toBeInTheDocument();
    expect(screen.getByText(/no institutions registered/i)).toBeInTheDocument();
  });

  it("renders institution rows for each institution", () => {
    useInstitutionsMock.mockReturnValue({
      data: MOCK_INSTITUTIONS,
      isLoading: false,
      isError: false,
    });

    render(<FederationPage />);

    expect(screen.getByTestId("institution-row-1")).toBeInTheDocument();
    expect(screen.getByTestId("institution-row-2")).toBeInTheDocument();
    expect(screen.getByText("Alpha University")).toBeInTheDocument();
    expect(screen.getByText("Beta College")).toBeInTheDocument();
  });

  it("shows institution overview when a row is clicked", () => {
    useInstitutionsMock.mockReturnValue({
      data: MOCK_INSTITUTIONS,
      isLoading: false,
      isError: false,
    });
    useInstitutionOverviewMock.mockReturnValue({
      data: MOCK_OVERVIEW,
      isLoading: false,
      isError: false,
    });

    render(<FederationPage />);

    fireEvent.click(screen.getByTestId("institution-row-1"));

    expect(screen.getByTestId("institution-overview-1")).toBeInTheDocument();
  });

  it("renders kpi cards when overview is loaded", () => {
    useInstitutionsMock.mockReturnValue({
      data: MOCK_INSTITUTIONS,
      isLoading: false,
      isError: false,
    });
    useInstitutionOverviewMock.mockReturnValue({
      data: MOCK_OVERVIEW,
      isLoading: false,
      isError: false,
    });

    render(<FederationPage />);
    fireEvent.click(screen.getByTestId("institution-row-1"));

    expect(screen.getByTestId("kpi-card-institution_students_total")).toBeInTheDocument();
    expect(screen.getByTestId("kpi-card-institution_enrollments_total")).toBeInTheDocument();
    expect(screen.getByTestId("kpi-card-institution_failed_jobs")).toBeInTheDocument();
    expect(screen.getByTestId("kpi-card-institution_automation_failures")).toBeInTheDocument();
  });

  it("shows error state when institutions fail to load", () => {
    useInstitutionsMock.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    });

    render(<FederationPage />);
    expect(screen.getByText(/failed to load institutions/i)).toBeInTheDocument();
  });

  it("shows overview loading state when overview not yet fetched", () => {
    useInstitutionsMock.mockReturnValue({
      data: MOCK_INSTITUTIONS,
      isLoading: false,
      isError: false,
    });
    useInstitutionOverviewMock.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });

    render(<FederationPage />);
    fireEvent.click(screen.getByTestId("institution-row-1"));

    expect(screen.getByText(/loading overview/i)).toBeInTheDocument();
  });

  it("deselects institution when clicking the same row again", () => {
    useInstitutionsMock.mockReturnValue({
      data: MOCK_INSTITUTIONS,
      isLoading: false,
      isError: false,
    });
    useInstitutionOverviewMock.mockReturnValue({
      data: MOCK_OVERVIEW,
      isLoading: false,
      isError: false,
    });

    render(<FederationPage />);

    fireEvent.click(screen.getByTestId("institution-row-1"));
    expect(screen.getByTestId("institution-overview-1")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("institution-row-1"));
    expect(screen.queryByTestId("institution-overview-1")).not.toBeInTheDocument();
  });
});
