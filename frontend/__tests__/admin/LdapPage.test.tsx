import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import LdapPage from "../../app/(admin)/console/ldap/page";

let allowAccess = true;
const useLdapStatusMock = vi.fn();

vi.mock("../../modules/ldap-admin/hooks", () => ({
  useLdapStatus: (...args: unknown[]) => useLdapStatusMock(...args),
  useTestLdapConnection: () => ({ mutate: vi.fn(), isPending: false }),
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
  usePathname: () => "/console/ldap",
  useSearchParams: () => new URLSearchParams(),
}));

describe("LdapPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useLdapStatusMock.mockReturnValue({
      data: {
        ldap: {
          enabled: true,
          host: "ldap.example.edu",
          port: 389,
          base_dn: "dc=example,dc=edu",
          bind_dn: "cn=admin,dc=example,dc=edu",
        },
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders ldap page and status fields", () => {
    render(<LdapPage />);
    expect(screen.getByTestId("ldap-page")).toBeInTheDocument();
    expect(screen.getByText("ldap.example.edu:389")).toBeInTheDocument();
    expect(screen.getByText("dc=example,dc=edu")).toBeInTheDocument();
  });

  it("renders test connection controls", () => {
    render(<LdapPage />);
    expect(screen.getAllByText("Test connection").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByPlaceholderText("LDAP login")).toBeInTheDocument();
  });

  it("shows error state when status query fails", () => {
    useLdapStatusMock.mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error("boom"),
      refetch: vi.fn(),
    });
    render(<LdapPage />);
    expect(screen.getByText("Failed to load LDAP status")).toBeInTheDocument();
  });
});
