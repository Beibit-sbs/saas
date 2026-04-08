import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import RbacPage from "../../app/(admin)/console/rbac/page";

const useRbacRolesMock = vi.fn();
const useRbacAssignmentsMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/rbac/hooks", () => ({
  useRbacRoles: () => useRbacRolesMock(),
  useRbacAssignments: (...args: unknown[]) =>
    useRbacAssignmentsMock(...args),
  useUpsertRole: () => ({ mutate: vi.fn(), isPending: false }),
  useAssignRole: () => ({ mutate: vi.fn(), isPending: false }),
  useRevokeAssignment: () => ({ mutate: vi.fn(), isPending: false }),
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
  usePathname: () => "/console/rbac",
  useSearchParams: () => new URLSearchParams(),
}));

const ROLES = {
  registrar: ["grades.write", "students.read"],
  auditor: ["admin.audit.read"],
};

const ASSIGNMENTS = [
  { user_id: "user-abc", role: "registrar", tenant_id: 1 },
];

describe("RbacPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useRbacRolesMock.mockReturnValue({
      data: { roles: ROLES },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    useRbacAssignmentsMock.mockReturnValue({
      data: { assignments: ASSIGNMENTS },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders roles and assignments tables", () => {
    render(<RbacPage />);

    expect(screen.getByTestId("rbac-page")).toBeInTheDocument();
      expect(screen.getAllByText("registrar").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("user-abc")).toBeInTheDocument();
  });

  it("shows empty state when no assignments", () => {
    useRbacAssignmentsMock.mockReturnValue({
      data: { assignments: [] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<RbacPage />);
    expect(screen.getByText(/no assignments/i)).toBeInTheDocument();
  });

  it("renders assign role and save role buttons", () => {
    render(<RbacPage />);
    expect(
      screen.getByRole("button", { name: /assign role/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /save role/i }),
    ).toBeInTheDocument();
  });
  it("shows access denied when read permission is missing", () => {
    allowAccess = false;
    render(<RbacPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });

});
