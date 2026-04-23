import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import FacultyPerformanceKpisPage from "../../app/(admin)/console/faculty-performance-kpis/page";

const useKpisMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/faculty-performance-kpis/hooks", () => ({
  useFacultyKpis: (...args: unknown[]) => useKpisMock(...args),
  useCreateFacultyKpi: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateFacultyKpiStatus: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: React.ReactNode; permission: string }) =>
    allowAccess ? <>{children}</> : <div>Access Denied</div>,
}));

vi.mock("../../shared/hooks/use-mutation-feedback", () => ({
  useMutationFeedback: () => ({
    getHandlers: () => ({ onSuccess: vi.fn(), onError: vi.fn() }),
  }),
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

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
  usePathname: () => "/console/faculty-performance-kpis",
  useSearchParams: () => new URLSearchParams(),
}));

const SAMPLE = {
  id: 1,
  tenant_id: "1",
  faculty_id: "FAC-001",
  name: "Dr. Jane Doe",
  department_id: "DEPT-CS",
  kpi_period: "2026-Q2",
  teaching_score: 85,
  research_score: 78,
  service_score: 91,
  overall_score: 84,
  status: "satisfactory",
};

describe("FacultyPerformanceKpisPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useKpisMock.mockReturnValue({
      data: { items: [SAMPLE] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders page heading", () => {
    render(<FacultyPerformanceKpisPage />);
    expect(screen.getByText(/Faculty Performance KPIs/i)).toBeInTheDocument();
  });

  it("renders KPI row", () => {
    render(<FacultyPerformanceKpisPage />);
    expect(screen.getByText("FAC-001")).toBeInTheDocument();
    expect(screen.getByText("Dr. Jane Doe")).toBeInTheDocument();
    expect(screen.getByText("DEPT-CS")).toBeInTheDocument();
  });

  it("renders create form fields", () => {
    render(<FacultyPerformanceKpisPage />);
    expect(screen.getByLabelText(/Faculty ID/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Name$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Overall Score/i)).toBeInTheDocument();
  });

  it("shows empty state", () => {
    useKpisMock.mockReturnValue({
      data: { items: [] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<FacultyPerformanceKpisPage />);
    expect(screen.getByText(/No KPI records found/i)).toBeInTheDocument();
  });

  it("shows access denied", () => {
    allowAccess = false;
    render(<FacultyPerformanceKpisPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
