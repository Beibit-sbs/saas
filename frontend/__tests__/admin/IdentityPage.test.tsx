import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import IdentityPage from "../../app/(admin)/console/identity/page";

let allowAccess = true;

const useIdentityProvidersMock = vi.fn();
const useDirectoryProvidersMock = vi.fn();
const useIdentityMappingsMock = vi.fn();

vi.mock("../../modules/identity-admin/hooks", () => ({
  useIdentityProviders: (...args: unknown[]) =>
    useIdentityProvidersMock(...args),
  useDirectoryProviders: (...args: unknown[]) =>
    useDirectoryProvidersMock(...args),
  useIdentityMappings: (...args: unknown[]) => useIdentityMappingsMock(...args),
  useTestDirectoryProvider: () => ({ mutate: vi.fn(), isPending: false }),
  useCreateIdentityMapping: () => ({ mutate: vi.fn(), isPending: false }),
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
  usePathname: () => "/console/identity",
  useSearchParams: () => new URLSearchParams(),
}));

describe("IdentityPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useIdentityProvidersMock.mockReturnValue({
      data: {
        providers: [{ provider: "oidc", type: "oidc", enabled: true }],
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    useDirectoryProvidersMock.mockReturnValue({
      data: {
        providers: [
          { id: 1, name: "Campus LDAP", type: "ldap", is_enabled: true },
        ],
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    useIdentityMappingsMock.mockReturnValue({
      data: {
        mappings: [
          {
            id: 1,
            provider_id: 1,
            external_group: "cn=registrar",
            platform_role: "registrar",
          },
        ],
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders identity page sections", () => {
    render(<IdentityPage />);
    expect(screen.getByTestId("identity-page")).toBeInTheDocument();
    expect(screen.getByText("Identity providers")).toBeInTheDocument();
    expect(screen.getByText("Identity mappings")).toBeInTheDocument();
  });

  it("renders providers and mappings rows", () => {
    render(<IdentityPage />);
    expect(screen.getAllByText("oidc").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Campus LDAP")).toBeInTheDocument();
    expect(screen.getByText("cn=registrar")).toBeInTheDocument();
  });

  it("shows empty states when lists are empty", () => {
    useIdentityProvidersMock.mockReturnValue({
      data: { providers: [] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    useDirectoryProvidersMock.mockReturnValue({
      data: { providers: [] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    useIdentityMappingsMock.mockReturnValue({
      data: { mappings: [] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<IdentityPage />);
    expect(
      screen.getAllByText(/No providers found\./i).length,
    ).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/No mappings found\./i)).toBeInTheDocument();
  });
});
