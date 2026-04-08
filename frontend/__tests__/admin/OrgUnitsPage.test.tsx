import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import OrgUnitsPage from "../../app/(admin)/console/org-units/page";

const useOrgUnitsMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/org-units/hooks", () => ({
  useOrgUnits: (...args: unknown[]) => useOrgUnitsMock(...args),
  useOrgUnitsTree: () => ({ data: [], isLoading: false }),
  useCreateOrgUnit: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateOrgUnit: () => ({ mutate: vi.fn(), isPending: false }),
  useDeactivateOrgUnit: () => ({ mutate: vi.fn(), isPending: false }),
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
  });

  it("renders org units table", () => {
    render(<OrgUnitsPage />);

    expect(screen.getByTestId("org-units-page")).toBeInTheDocument();
    expect(screen.getByText("Faculty of Engineering")).toBeInTheDocument();
    expect(screen.getByText("ENG")).toBeInTheDocument();
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
});
