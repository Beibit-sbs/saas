import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import FacultyPage from "../../app/(admin)/console/faculty/page";

const useFacultyMock = vi.fn();
const useFacultyContractsMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/faculty/hooks", () => ({
  useFaculty: (...args: unknown[]) => useFacultyMock(...args),
  useFacultyContracts: (...args: unknown[]) => useFacultyContractsMock(...args),
  useCreateFaculty: () => ({ mutate: vi.fn(), isPending: false }),
  useCreateFacultyContract: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateFaculty: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateFacultyContractStatus: () => ({ mutate: vi.fn(), isPending: false }),
  useDeleteFaculty: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  PermissionGate: ({ children }: { children: React.ReactNode }) =>
    allowAccess ? <>{children}</> : null,
  RequirePermission: ({ children }: { children: React.ReactNode; permission: string }) =>
    allowAccess ? <>{children}</> : <div>Access Denied</div>,
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
  usePathname: () => "/console/faculty",
  useSearchParams: () => new URLSearchParams(),
}));

const FACULTY = [
  {
    id: 1,
    tenant_id: "1",
    faculty_id: "FAC-001",
    first_name: "Ada",
    last_name: "Lovelace",
    department: "Computer Science",
    email: "ada@example.edu",
    status: "active",
  },
  {
    id: 2,
    tenant_id: "1",
    faculty_id: "FAC-002",
    first_name: "Alan",
    last_name: "Turing",
    department: "Mathematics",
    email: "alan@example.edu",
    status: "active",
  },
];

describe("FacultyPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useFacultyMock.mockReturnValue({
      data: { faculty: FACULTY },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    useFacultyContractsMock.mockReturnValue({
      data: {
        contracts: [
          {
            id: 101,
            faculty_id: "FAC-001",
            contract_type: "full_time",
            start_date: "2026-09-01",
            end_date: "2027-08-31",
            fte_ratio: 1,
            max_credit_hours: 18,
            status: "active",
            notes: "renewed",
          },
        ],
      },
      isLoading: false,
    });
  });

  it("renders faculty page and rows", () => {
    render(<FacultyPage />);
    expect(screen.getByTestId("faculty-page")).toBeInTheDocument();
    expect(screen.getAllByText("FAC-001").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Turing")).toBeInTheDocument();
  });

  it("shows faculty-specific columns", () => {
    render(<FacultyPage />);
    expect(screen.getByText("Computer Science")).toBeInTheDocument();
    expect(screen.getByText("ada@example.edu")).toBeInTheDocument();
    expect(screen.getByText("Faculty Contracts")).toBeInTheDocument();
    expect(screen.getByText("full_time")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /delete|удалить|жою/i }).length).toBeGreaterThanOrEqual(1);
  });

  it("shows empty state when no faculty entries", () => {
    useFacultyMock.mockReturnValue({
      data: { faculty: [] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<FacultyPage />);
    expect(screen.getByText(/No faculty records found\./i)).toBeInTheDocument();
  });

    it("shows access denied when read permission is missing", () => {
      allowAccess = false;
      render(<FacultyPage />);
      expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
    });
});
