import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import ProgramsPage from "../../app/(admin)/console/programs/page";

const useProgramsMock = vi.fn();
const useOrgUnitsMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/programs/hooks", () => ({
  usePrograms: (...args: unknown[]) => useProgramsMock(...args),
  useCreateProgram: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateProgram: () => ({ mutate: vi.fn(), isPending: false }),
  useDeleteProgram: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("../../modules/org-units/hooks", () => ({
  useOrgUnits: (...args: unknown[]) => useOrgUnitsMock(...args),
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
  usePathname: () => "/console/programs",
  useSearchParams: () => new URLSearchParams(),
}));

const PROGRAMS = [
  {
    id: 1,
    tenant_id: "1",
    program_code: "CS-BSC",
    title: "Computer Science",
    degree_type: "Bachelor",
    faculty: "Engineering",
    status: "active",
  },
  {
    id: 2,
    tenant_id: "1",
    program_code: "MATH-MSC",
    title: "Applied Mathematics",
    degree_type: "Master",
    faculty: "Science",
    status: "archived",
  },
];

const ORG_UNITS = [
  {
    id: 11,
    tenant_id: 1,
    name: "Faculty of Engineering",
    code: "ENG",
    unit_type: "faculty",
    parent_unit_id: 10,
    active: true,
    head_person_id: null,
    email: null,
    phone: null,
    location: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  },
  {
    id: 12,
    tenant_id: 1,
    name: "Computer Science Department",
    code: "CS",
    unit_type: "department",
    parent_unit_id: 11,
    active: true,
    head_person_id: null,
    email: null,
    phone: null,
    location: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  },
];

describe("ProgramsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useProgramsMock.mockReturnValue({
      data: { programs: PROGRAMS },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    useOrgUnitsMock.mockReturnValue({
      data: ORG_UNITS,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders programs page and rows", () => {
    render(<ProgramsPage />);
    expect(screen.getByTestId("programs-page")).toBeInTheDocument();
    expect(screen.getByText("CS-BSC")).toBeInTheDocument();
    expect(screen.getByText("Applied Mathematics")).toBeInTheDocument();
  });

  it("shows action buttons for writable rows", () => {
    render(<ProgramsPage />);
    expect(screen.getAllByRole("button", { name: /edit|редактировать/i }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole("button", { name: /delete|удалить|жою/i }).length).toBeGreaterThanOrEqual(1);
  });

  it("uses org structure units when creating a program", () => {
    render(<ProgramsPage />);

    fireEvent.click(screen.getByRole("button", { name: /add program/i }));

    expect(screen.getByTestId("program-org-unit-select")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /ENG - Faculty of Engineering/ })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /CS - Computer Science Department/ })).toBeInTheDocument();
  });

  it("shows empty state when programs are missing", () => {
    useProgramsMock.mockReturnValue({
      data: { programs: [] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<ProgramsPage />);
    expect(screen.getByText(/No programs found\./i)).toBeInTheDocument();
  });

  it("shows access denied when read permission is missing", () => {
    allowAccess = false;
    render(<ProgramsPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
