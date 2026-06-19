import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import OrgUnitsPage from "../../app/(admin)/console/org-units/page";

const useOrgUnitsMock = vi.fn();
const useOrgUnitsTreeMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/org-units/hooks", () => ({
  useOrgUnits: (...args: unknown[]) => useOrgUnitsMock(...args),
  useOrgUnitsTree: (...args: unknown[]) => useOrgUnitsTreeMock(...args),
  useCreateOrgUnit: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateOrgUnit: () => ({ mutate: vi.fn(), isPending: false }),
  useDeactivateOrgUnit: () => ({ mutate: vi.fn(), isPending: false }),
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
  usePathname: () => "/console/org-units",
  useSearchParams: () => new URLSearchParams(),
}));

const UNITS = [
  {
    id: 1,
    tenant_id: 1,
    name: "Faculty of Engineering",
    code: "ENG",
    unit_type: "faculty",
    parent_unit_id: null,
    active: true,
    head_person_id: null,
    email: null,
    phone: null,
    location: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  },
];

const TREE = [
  {
    id: 10,
    name: "Root Flow University",
    code: "ROOT",
    unit_type: "university",
    active: true,
    children: [
      {
        id: 11,
        name: "Faculty of Engineering",
        code: "ENG",
        unit_type: "faculty",
        active: true,
        children: [
          {
            id: 12,
            name: "Computer Science Department",
            code: "CS",
            unit_type: "department",
            active: true,
            children: [],
          },
        ],
      },
    ],
  },
];

describe("OrgUnitsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useOrgUnitsMock.mockReturnValue({
      data: UNITS,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    useOrgUnitsTreeMock.mockReturnValue({
      data: TREE,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders org units table", () => {
    render(<OrgUnitsPage />);

    expect(screen.getByTestId("org-units-page")).toBeInTheDocument();
    expect(screen.getAllByText("Faculty of Engineering").length).toBeGreaterThan(0);
    expect(screen.getByText("ENG")).toBeInTheDocument();
  });

  it("renders the tenant organization tree", () => {
    render(<OrgUnitsPage />);

    expect(screen.getByTestId("org-units-tree-section")).toBeInTheDocument();
    expect(screen.getByText("Root Flow University")).toBeInTheDocument();
    expect(screen.getByText("Computer Science Department")).toBeInTheDocument();
  });

  it("shows empty state when no units", () => {
    useOrgUnitsMock.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<OrgUnitsPage />);
    expect(screen.getByText(/no org units/i)).toBeInTheDocument();
  });

  it("shows Add unit button when permitted", () => {
    render(<OrgUnitsPage />);
    expect(
      screen.getByRole("button", { name: /add unit/i }),
    ).toBeInTheDocument();
  });

  it("uses existing units as parent choices when creating a unit", () => {
    render(<OrgUnitsPage />);

    fireEvent.click(screen.getByRole("button", { name: /add unit/i }));

    expect(screen.getByLabelText("Parent unit ID")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /Faculty of Engineering/ })).toBeInTheDocument();
  });

  it("shows access denied when read permission is missing", () => {
    allowAccess = false;
    render(<OrgUnitsPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });

});
