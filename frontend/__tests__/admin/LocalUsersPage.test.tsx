import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import LocalUsersPage from "../../app/(admin)/console/local-users/page";

const useLocalUsersMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/local-users/hooks", () => ({
  useLocalUsers: (...args: unknown[]) => useLocalUsersMock(...args),
  useCreateLocalUser: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateLocalUser: () => ({ mutate: vi.fn(), isPending: false }),
  useDeleteLocalUser: () => ({ mutate: vi.fn(), isPending: false }),
  useSetLocalUserPassword: () => ({ mutate: vi.fn(), isPending: false }),
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
  usePathname: () => "/console/local-users",
  useSearchParams: () => new URLSearchParams(),
}));

const USERS = [
  {
    user_id: "u-1",
    login: "local.registrar",
    display_name: "Local Registrar",
    roles: ["registrar"],
    default_language: "en",
  },
];

describe("LocalUsersPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useLocalUsersMock.mockReturnValue({
      data: { users: USERS },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders local users table", () => {
    render(<LocalUsersPage />);

    expect(screen.getByTestId("local-users-page")).toBeInTheDocument();
    expect(screen.getByText("local.registrar")).toBeInTheDocument();
    expect(screen.getByText("Local Registrar")).toBeInTheDocument();
  });

  it("shows empty state when no users", () => {
    useLocalUsersMock.mockReturnValue({
      data: { users: [] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<LocalUsersPage />);
    expect(screen.getByText(/no local users/i)).toBeInTheDocument();
  });

  it("shows Add local user button when permitted", () => {
    render(<LocalUsersPage />);
    expect(
      screen.getByRole("button", { name: /add local user/i }),
    ).toBeInTheDocument();
  });
  it("shows access denied when read permission is missing", () => {
    allowAccess = false;
    render(<LocalUsersPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });

});
