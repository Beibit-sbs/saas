import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import SchedulingPage from "../../app/(admin)/console/scheduling/page";

const hasPermissionMock = vi.fn();

vi.mock("../../shared/hooks/use-permissions", () => ({
  usePermissions: () => ({
    hasPermission: hasPermissionMock,
    hasAnyPermission: hasPermissionMock,
    roles: [],
  }),
}));

vi.mock("../../shared/hooks/use-table-query-state", () => ({
  useTableQueryState: () => ({
    page: 1,
    pageSize: 20,
    filters: { semester: "", status: "" },
    sort: { key: "semester", direction: "desc" as const },
    setFilter: vi.fn(),
    resetFilters: vi.fn(),
    setPage: vi.fn(),
    setPageSize: vi.fn(),
    setSort: vi.fn(),
  }),
}));

vi.mock("../../modules/scheduling/hooks", () => ({
  useSections: () => ({
    data: { items: [], total: 0 },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

vi.mock("../../app/components/LanguageProvider", () => ({
  useLanguage: () => ({
    t: (key: string) => key,
  }),
}));

describe("SchedulingPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders AccessDenied when scheduling read permission is missing", () => {
    hasPermissionMock.mockReturnValue(false);

    render(<SchedulingPage />);

    expect(hasPermissionMock).toHaveBeenCalled();
    expect(screen.getByText("Access Denied")).toBeInTheDocument();
  });
});
