/**
 * A-016.6 Wave 4 KPI frontend tests.
 * Covers: AcademicIntegrityPage, ExamGovernancePage, ThesisPage, and the
 * dashboard Wave4 section each render Wave1KpiBar with the correct metric keys.
 */
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

const useIntegrityCasesMock = vi.fn(() => ({
  data: { cases: [], total: 0, page: 1, page_size: 20 },
  isLoading: false,
  error: null,
}));

const useExamDashboardSummaryMock = vi.fn(() => ({
  data: {
    total_exams: 0,
    status_breakdown: {},
    proctoring_summary: {},
    accommodation_summary: {},
  },
  isLoading: false,
  isError: false,
}));

const useExamsListMock = vi.fn(() => ({
  data: { items: [], total: 0 },
  isLoading: false,
  refetch: vi.fn(),
}));

const useExamStatisticsMock = vi.fn(() => ({
  data: null,
  isLoading: false,
}));

const useThesisMock = vi.fn(() => ({
  data: { items: [], total: 0 },
  isLoading: false,
  isError: false,
  refetch: vi.fn(),
}));

// ─── shared mock helpers ────────────────────────────────────────────────────

vi.mock("../../modules/platform/kpi/wave1-kpi-bar", () => ({
  Wave1KpiBar: ({ metricKeys, labels }: { metricKeys: string[]; labels: Record<string, string> }) => (
    <div data-testid="wave4-kpi-bar-mock" data-keys={metricKeys.join(",")} />
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
  useLanguage: () => ({ t: (k: string) => k, language: "en" }),
}));

vi.mock("../../shared/providers/LanguageProvider", () => ({
  useLanguage: () => ({ t: (k: string) => k, language: "en" }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  PermissionGate: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("../../shared/auth/permission-gate", () => ({
  RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("../../shared/hooks/use-mutation-feedback", () => ({
  useMutationFeedback: () => ({ getHandlers: () => ({ onSuccess: vi.fn(), onError: vi.fn() }) }),
}));

// ─── AcademicIntegrityPage ───────────────────────────────────────────────────

vi.mock("../../modules/academic-integrity/hooks", () => ({
  useIntegrityCases: () => useIntegrityCasesMock(),
  useCreateIntegrityCase: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useUpdateIntegrityCaseStatus: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

import AcademicIntegrityPage from "../../app/(admin)/console/academic-integrity/page";

describe("AcademicIntegrityPage Wave4 KPI wiring", () => {
  it("renders Wave1KpiBar with academic integrity and case resolution metric keys", () => {
    render(<AcademicIntegrityPage />);
    const bar = screen.getByTestId("wave4-kpi-bar-mock");
    expect(bar).toBeInTheDocument();
    const keys = bar.getAttribute("data-keys") ?? "";
    expect(keys).toContain("academic_integrity_risk_count");
    expect(keys).toContain("academic_integrity_high_risk_count");
    expect(keys).toContain("academic_integrity_cases_pending_review");
    expect(keys).toContain("integrity_cases_open_count");
    expect(keys).toContain("integrity_cases_escalated_count");
    expect(keys).toContain("integrity_cases_resolved_count");
    expect(keys).toContain("integrity_case_resolution_sla_risk_count");
  });

  it("renders Wave4 KPI section with correct data-testid", () => {
    render(<AcademicIntegrityPage />);
    expect(screen.getByTestId("wave4-academic-integrity-kpi-section")).toBeInTheDocument();
  });
});

// ─── ExamGovernancePage ──────────────────────────────────────────────────────

vi.mock("../../modules/exam-governance/hooks", () => ({
  useExamDashboardSummary: () => useExamDashboardSummaryMock(),
  useExamsList: () => useExamsListMock(),
  useExamStatistics: () => useExamStatisticsMock(),
}));

import ExamGovernancePage from "../../app/(admin)/console/exam-governance/page";

describe("ExamGovernancePage Wave4 KPI wiring", () => {
  it("renders Wave1KpiBar with exam proctoring metric keys", () => {
    render(<ExamGovernancePage />);
    const bar = screen.getByTestId("wave4-kpi-bar-mock");
    expect(bar).toBeInTheDocument();
    const keys = bar.getAttribute("data-keys") ?? "";
    expect(keys).toContain("exam_proctoring_violations_count");
    expect(keys).toContain("exam_integrity_reviews_count");
    expect(keys).toContain("exam_integrity_high_risk_count");
    expect(keys).toContain("exam_integrity_requires_approval_count");
  });

  it("renders Wave4 exam proctoring KPI section with correct data-testid", () => {
    render(<ExamGovernancePage />);
    expect(screen.getByTestId("wave4-exam-proctoring-kpi-section")).toBeInTheDocument();
  });

  it("does not crash when optional dashboard fields are missing", () => {
    useExamDashboardSummaryMock.mockReturnValueOnce({
      data: undefined as any,
      isLoading: false,
      isError: false,
    });

    render(<ExamGovernancePage />);
    expect(screen.getByTestId("wave4-exam-proctoring-kpi-section")).toBeInTheDocument();
  });
});

// ─── ThesisPage ──────────────────────────────────────────────────────────────

vi.mock("../../modules/thesis/hooks", () => ({
  useThesis: () => useThesisMock(),
  useCreateThesis: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateThesisStatus: () => ({ mutate: vi.fn(), isPending: false }),
}));

import ThesisPage from "../../app/(admin)/console/thesis/page";

describe("ThesisPage Wave4 KPI wiring", () => {
  it("renders Wave1KpiBar with thesis governance metric keys", () => {
    render(<ThesisPage />);
    const bar = screen.getByTestId("wave4-kpi-bar-mock");
    expect(bar).toBeInTheDocument();
    const keys = bar.getAttribute("data-keys") ?? "";
    expect(keys).toContain("thesis_governance_risk_count");
    expect(keys).toContain("thesis_supervisor_assignment_needed_count");
    expect(keys).toContain("thesis_review_delayed_count");
    expect(keys).toContain("thesis_governance_requires_approval_count");
  });

  it("still includes original thesis completion risk keys", () => {
    render(<ThesisPage />);
    const bar = screen.getByTestId("wave4-kpi-bar-mock");
    const keys = bar.getAttribute("data-keys") ?? "";
    expect(keys).toContain("thesis_completion_risk_count");
    expect(keys).toContain("thesis_intervention_cases_count");
  });

  it("renders safely when thesis list payload is absent", () => {
    useThesisMock.mockReturnValueOnce({
      data: undefined as any,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(<ThesisPage />);
    expect(screen.getByTestId("wave4-kpi-bar-mock")).toBeInTheDocument();
  });
});
