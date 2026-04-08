import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import RecordsPage from "../../app/(admin)/console/records/page";

const useAcademicRecordsMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/academic-records/hooks", () => ({
  useAcademicRecords: (...args: unknown[]) => useAcademicRecordsMock(...args),
  useCreateAcademicRecord: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateAcademicRecord: () => ({ mutate: vi.fn(), isPending: false }),
  useDeleteAcademicRecord: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  PermissionGate: ({ children }: { children: React.ReactNode }) =>
    allowAccess ? <>{children}</> : null,
  AccessDenied: ({ message }: { message?: string }) => (
    <div>{message ?? "Access Denied"}</div>
  ),
}));

vi.mock("../../shared/hooks/use-permissions", () => ({
  usePermissions: () => ({
    hasPermission: () => allowAccess,
    hasAnyPermission: () => allowAccess,
    roles: allowAccess ? ["admin"] : [],
  }),
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
  usePathname: () => "/console/records",
  useSearchParams: () => new URLSearchParams(),
}));

const RECORDS = [
  {
    id: 1,
    tenant_id: "1",
    student_id: 1001,
    course_id: 2001,
    grade: "A",
    semester: "2026-Spring",
    status: "active",
  },
  {
    id: 2,
    tenant_id: "1",
    student_id: 1002,
    course_id: 2002,
    grade: "B+",
    semester: "2026-Fall",
    status: "active",
  },
];

describe("RecordsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useAcademicRecordsMock.mockReturnValue({
      data: { records: RECORDS },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders records page and rows", () => {
    render(<RecordsPage />);
    expect(screen.getByTestId("records-page")).toBeInTheDocument();
    expect(screen.getByText("2026-Spring")).toBeInTheDocument();
    expect(screen.getByText("B+")).toBeInTheDocument();
  });

  it("shows student and course columns", () => {
    render(<RecordsPage />);
    expect(screen.getByText("1001")).toBeInTheDocument();
    expect(screen.getByText("2002")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /delete|удалить|жою/i }).length).toBeGreaterThanOrEqual(1);
  });

  it("shows empty state when no records", () => {
    useAcademicRecordsMock.mockReturnValue({
      data: { records: [] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<RecordsPage />);
    expect(screen.getByText(/No academic records found\./i)).toBeInTheDocument();
  });
});
