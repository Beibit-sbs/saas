import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import AuditPage from "../../app/(admin)/console/audit/page";

const useAuditEventsMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/audit/hooks", () => ({
  useAuditEvents: (...args: unknown[]) => useAuditEventsMock(...args),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

vi.mock("../../shared/hooks/use-permissions", () => ({
  usePermissions: () => ({
    hasPermission: () => allowAccess,
    hasAnyPermission: () => allowAccess,
    roles: allowAccess ? ["admin"] : [],
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
  usePathname: () => "/console/audit",
  useSearchParams: () => new URLSearchParams(),
}));

const EVENTS = [
  {
    event_id: "evt-1",
    timestamp: "2026-04-08T03:00:00Z",
    actor: "owner@example.com",
    action: "rbac.role.assigned",
    entity: "role_assignment",
    path: "/api/admin/rbac/assign",
    ip: "127.0.0.1",
    client_ip: "127.0.0.1",
    result: "success",
    tenant_id: 1,
    correlation_id: "corr-1",
    metadata: {},
  },
];

describe("AuditPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useAuditEventsMock.mockReturnValue({
      data: { events: EVENTS },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders audit events table", () => {
    render(<AuditPage />);

    expect(screen.getByTestId("audit-page")).toBeInTheDocument();
    expect(screen.getByText("owner@example.com")).toBeInTheDocument();
    expect(screen.getByText("rbac.role.assigned")).toBeInTheDocument();
  });

  it("opens export link for csv", () => {
    const openSpy = vi.spyOn(window, "open").mockImplementation(() => null);

    render(<AuditPage />);
    fireEvent.click(screen.getByRole("button", { name: /export csv/i }));

    expect(openSpy).toHaveBeenCalledWith(
      expect.stringContaining("/api/bff/admin/audit/export?"),
      "_blank",
      "noopener,noreferrer",
    );
  });

  it("renders access denied without permission", () => {
    allowAccess = false;

    render(<AuditPage />);
    expect(screen.getByText("Access Denied")).toBeInTheDocument();
  });
});
