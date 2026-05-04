import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import InterventionsPage from "../../app/(admin)/console/interventions/page";

let allowAccess = true;

vi.mock("../../modules/platform/kpi/wave1-kpi-bar", () => ({
  Wave1KpiBar: () => <div data-testid="wave1-kpi-bar-mock" />,
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  PermissionGate: ({ children }: { children: ReactNode }) =>
    allowAccess ? <>{children}</> : null,
  RequirePermission: ({ children }: { children: ReactNode; permission: string }) =>
    allowAccess ? <>{children}</> : <div>Access Denied</div>,
  AccessDenied: ({ message }: { message?: string }) => (
    <div>{message ?? "Access Denied"}</div>
  ),
}));

vi.mock("../../shared/hooks/use-table-query-state", () => ({
  useTableQueryState: () => ({
    page: 1,
    pageSize: 20,
    filters: { status: "", severity: "", assignee_ref: "", overdue_only: "" },
    sort: { key: "updated", direction: "desc" as const },
    setFilter: vi.fn(),
    resetFilters: vi.fn(),
    setPage: vi.fn(),
    setPageSize: vi.fn(),
    setSort: vi.fn(),
  }),
}));

vi.mock("../../shared/hooks/use-detail-drawer", () => ({
  useDetailDrawer: () => ({
    isOpen: false,
    selectedId: null,
    open: vi.fn(),
    close: vi.fn(),
  }),
}));

vi.mock("../../shared/hooks/use-mutation-feedback", () => ({
  useMutationFeedback: () => ({
    getHandlers: () => ({ onSuccess: vi.fn(), onError: vi.fn() }),
  }),
}));

vi.mock("../../modules/platform/interventions/hooks", () => ({
  useInterventionCases: () => ({
    data: { items: [], total: 0 },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useInterventionCase: () => ({ data: null, isLoading: false, error: null }),
  useInterventionActions: () => ({ data: { items: [] }, isLoading: false, error: null }),
  useAssignInterventionCase: () => ({ mutate: vi.fn(), isPending: false }),
  useTakeInterventionCase: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateInterventionStatus: () => ({ mutate: vi.fn(), isPending: false }),
  useAddInterventionAction: () => ({ mutate: vi.fn(), isPending: false }),
  useStudentName: () => ({ name: null, email: null, isLoading: false }),
}));

vi.mock("../../modules/platform/interventions/summary-stats", () => ({
  InterventionsSummaryStats: () => <div>summary</div>,
}));

vi.mock("../../app/components/LanguageProvider", () => ({
  useLanguage: () => ({
    t: (key: string) => key,
  }),
}));

describe("InterventionsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
  });

  it("renders interventions workspace when read permission exists", () => {
    render(<InterventionsPage />);

    expect(screen.getByText("nav.interventions")).toBeInTheDocument();
    expect(screen.getByText("intervention.action.exportCsv")).toBeInTheDocument();
    expect(screen.getByText("summary")).toBeInTheDocument();
  });

  it("renders AccessDenied when interventions read permission is missing", () => {
    allowAccess = false;

    render(<InterventionsPage />);

    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
