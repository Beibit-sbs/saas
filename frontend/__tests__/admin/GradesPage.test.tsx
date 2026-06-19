import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import GradesPage from "../../app/(admin)/console/grades/page";

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

vi.mock("../../modules/grades/hooks", () => ({
  useGrades: () => ({
    data: { items: [], total: 0 },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useUpsertGrade: () => ({ mutate: vi.fn(), isPending: false }),
  useGradingScales: () => ({
    data: { items: [], total: 0 },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useCreateGradingScale: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("../../modules/enrollments/hooks", () => ({
  useEnrollments: () => ({
    data: { items: [], total: 0 },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
}));

vi.mock("../../modules/students/hooks", () => ({
  useStudents: () => ({
    data: { items: [], total: 0 },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
}));

vi.mock("../../app/components/LanguageProvider", () => ({
  useLanguage: () => ({
    t: (key: string) => key,
  }),
}));

describe("GradesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
  });

  it("renders AccessDenied when grades read permission is missing", () => {
    allowAccess = false;

    render(<GradesPage />);

    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
