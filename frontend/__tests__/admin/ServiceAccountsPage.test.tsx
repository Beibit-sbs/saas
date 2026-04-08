import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import ServiceAccountsPage from "../../app/(admin)/console/service-accounts/page";

const useServiceAccountsMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/service-accounts/hooks", () => ({
  useServiceAccounts: (...args: unknown[]) => useServiceAccountsMock(...args),
  useCreateServiceAccount: () => ({ mutate: vi.fn(), isPending: false }),
  useIssueServiceToken: () => ({ mutate: vi.fn(), isPending: false }),
  useRevokeServiceAccount: () => ({ mutate: vi.fn(), isPending: false }),
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
  usePathname: () => "/console/service-accounts",
  useSearchParams: () => new URLSearchParams(),
}));

const ACCOUNTS = [
  {
    account_id: "sa-001",
    name: "analytics-reader",
    permissions: ["analytics.read"],
    platform_global: false,
    revoked: false,
    tenant_id: 1,
    created_at: "2026-01-01T00:00:00Z",
  },
  {
    account_id: "sa-002",
    name: "old-service",
    permissions: ["students.read"],
    platform_global: false,
    revoked: true,
    tenant_id: 1,
    created_at: "2026-01-01T00:00:00Z",
  },
];

describe("ServiceAccountsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useServiceAccountsMock.mockReturnValue({
      data: { accounts: ACCOUNTS },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders page with service accounts table", () => {
    render(<ServiceAccountsPage />);
    expect(screen.getByTestId("service-accounts-page")).toBeInTheDocument();
    expect(screen.getByText("analytics-reader")).toBeInTheDocument();
    expect(screen.getByText("old-service")).toBeInTheDocument();
  });

  it("shows data for an active service account", () => {
    render(<ServiceAccountsPage />);
    expect(screen.getByText("sa-001")).toBeInTheDocument();
    expect(screen.getByText("analytics.read")).toBeInTheDocument();
    const revokeButtons = screen.getAllByRole("button", {
      name: /Revoke|Отозвать|Жою/,
    });
    expect(revokeButtons.length).toBeGreaterThanOrEqual(1);
  });

  it("shows empty state when no accounts", () => {
    useServiceAccountsMock.mockReturnValue({
      data: { accounts: [] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<ServiceAccountsPage />);
    expect(
      screen.getByText(/No service accounts found\./i),
    ).toBeInTheDocument();
  });
});
