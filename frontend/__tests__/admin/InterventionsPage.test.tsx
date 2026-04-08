import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import InterventionsPage from "../../app/(admin)/console/interventions/page";

let allowAccess = true;

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

  it("renders AccessDenied when interventions read permission is missing", () => {
    allowAccess = false;

    render(<InterventionsPage />);

    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
