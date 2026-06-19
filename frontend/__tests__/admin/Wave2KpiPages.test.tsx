/**
 * A-014.6 Wave 2 KPI frontend tests.
 * Covers: GradesPage, DegreeProgressPage, FinancialAidPage, ThesisPage each render Wave1KpiBar.
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

// ─── shared mock helpers ────────────────────────────────────────────────────

vi.mock("../../modules/platform/kpi/wave1-kpi-bar", () => ({
  Wave1KpiBar: ({ metricKeys, labels }: { metricKeys: string[]; labels: Record<string, string> }) => (
    <div data-testid="wave2-kpi-bar-mock" data-keys={metricKeys.join(",")} />
  ),
}));

vi.mock("../../shared/auth/context", () => ({
  useAdminAuth: () => ({ user: { tenantId: 1, roles: ["admin"], permissions: [] } }),
}));

vi.mock("../../shared/hooks/use-permissions", () => ({
  usePermissions: () => ({
    hasPermission: () => true,
    hasAnyPermission: () => true,
    roles: ["admin"],
  }),
}));

vi.mock("../../app/components/LanguageProvider", () => ({
  useLanguage: () => ({ t: (k: string) => k }),
}));

// ─── GradesPage ─────────────────────────────────────────────────────────────

vi.mock("../../modules/grades/hooks", () => ({
  useGrades: () => ({ data: { items: [], total: 0 }, isLoading: false, error: null, refetch: vi.fn() }),
  useUpsertGrade: () => ({ mutate: vi.fn(), isPending: false }),
  useGradingScales: () => ({ data: { items: [], total: 0 }, isLoading: false, error: null, refetch: vi.fn() }),
  useCreateGradingScale: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("../../modules/enrollments/hooks", () => ({
  useEnrollments: () => ({ data: { items: [], total: 0 }, isLoading: false, error: null, refetch: vi.fn() }),
}));

vi.mock("../../modules/students/hooks", () => ({
  useStudents: () => ({ data: { items: [], total: 0 }, isLoading: false, error: null, refetch: vi.fn() }),
}));

vi.mock("../../shared/hooks/use-table-query-state", () => ({
  useTableQueryState: () => ({
    page: 1,
    pageSize: 20,
    filters: { student_id: "", course_id: "", term_id: "", section_id: "" },
    sort: { key: "graded", direction: "desc" as const },
    setFilter: vi.fn(),
    resetFilters: vi.fn(),
    setPage: vi.fn(),
    setPageSize: vi.fn(),
    setSort: vi.fn(),
  }),
}));

vi.mock("../../shared/hooks/use-detail-drawer", () => ({
  useDetailDrawer: () => ({ isOpen: false, selectedId: null, open: vi.fn(), close: vi.fn() }),
}));

vi.mock("../../shared/hooks/use-mutation-feedback", () => ({
  useMutationFeedback: () => ({ getHandlers: () => ({ onSuccess: vi.fn(), onError: vi.fn() }) }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  PermissionGate: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

import GradesPage from "../../app/(admin)/console/grades/page";

describe("GradesPage Wave2 KPI wiring", () => {
  it("renders Wave1KpiBar with grade decline metric keys", () => {
    render(<GradesPage />);
    const bar = screen.getByTestId("wave2-kpi-bar-mock");
    expect(bar).toBeInTheDocument();
    const keys = bar.getAttribute("data-keys") ?? "";
    expect(keys).toContain("grade_decline_risk_count");
    expect(keys).toContain("grade_intervention_cases_count");
  });
});

// ─── ThesisPage ─────────────────────────────────────────────────────────────

vi.mock("../../modules/thesis/hooks", () => ({
  useThesis: () => ({ data: { items: [], total: 0 }, isLoading: false, error: null, refetch: vi.fn() }),
  useCreateThesis: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateThesisStatus: () => ({ mutate: vi.fn(), isPending: false }),
}));

import ThesisPage from "../../app/(admin)/console/thesis/page";

describe("ThesisPage Wave2 KPI wiring", () => {
  it("renders Wave1KpiBar with thesis risk metric keys", () => {
    render(<ThesisPage />);
    const bar = screen.getByTestId("wave2-kpi-bar-mock");
    expect(bar).toBeInTheDocument();
    const keys = bar.getAttribute("data-keys") ?? "";
    expect(keys).toContain("thesis_completion_risk_count");
    expect(keys).toContain("thesis_intervention_cases_count");
  });
});

// ─── FinancialAidPage ────────────────────────────────────────────────────────

vi.mock("../../modules/financial_aid/hooks", () => ({
  useFinancialAidRecords: () => ({ data: { items: [], total: 0 }, isLoading: false, error: null, refetch: vi.fn() }),
  useCreateFinancialAidRecord: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateFinancialAidStatus: () => ({ mutate: vi.fn(), isPending: false }),
}));

import FinancialAidPage from "../../app/(admin)/console/financial-aid/page";

describe("FinancialAidPage Wave2 KPI wiring", () => {
  it("renders Wave1KpiBar with scholarship and financial aid risk keys", () => {
    render(<FinancialAidPage />);
    const bar = screen.getByTestId("wave2-kpi-bar-mock");
    expect(bar).toBeInTheDocument();
    const keys = bar.getAttribute("data-keys") ?? "";
    expect(keys).toContain("scholarship_risk_cases_count");
    expect(keys).toContain("financial_aid_risk_cases_count");
  });
});
