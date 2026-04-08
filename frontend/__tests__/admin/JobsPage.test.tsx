import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import JobsPage from "../../app/(admin)/console/jobs/page";

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
    filters: { status: "", job_type: "" },
    sort: { key: "created", direction: "desc" as const },
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

vi.mock("../../modules/platform/jobs/hooks", () => ({
  useJobs: () => ({
    data: { items: [], total: 0 },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useRetryJob: () => ({ mutate: vi.fn(), isPending: false }),
  useCancelJob: () => ({ mutate: vi.fn(), isPending: false }),
  useTriggerJob: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("../../app/components/LanguageProvider", () => ({
  useLanguage: () => ({
    t: (key: string) => key,
  }),
}));

describe("JobsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
  });

  it("renders AccessDenied when jobs read permission is missing", () => {
    allowAccess = false;

    render(<JobsPage />);

    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
