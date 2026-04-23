import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import ResearchGrantsPage from "../../app/(admin)/console/research-grants/page";

const useGrantsMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/research-grants/hooks", () => ({
  useResearchGrants: (...args: unknown[]) => useGrantsMock(...args),
  useCreateResearchGrant: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateResearchGrantStatus: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  PermissionGate: ({ children }: { children: React.ReactNode }) =>
    allowAccess ? <>{children}</> : null,
  RequirePermission: ({
    children,
  }: {
    children: React.ReactNode;
    permission: string;
  }) => (allowAccess ? <>{children}</> : <div>Access Denied</div>),
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
  usePathname: () => "/console/research-grants",
  useSearchParams: () => new URLSearchParams(),
}));

const SAMPLE_GRANT = {
  id: 1,
  tenant_id: "1",
  grant_code: "GR-2026-01",
  title: "AI for Education Research",
  pi_faculty_id: "FAC-001",
  deadline: "2026-12-31",
  funding_amount: 150000,
  status: "active",
};

describe("ResearchGrantsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useGrantsMock.mockReturnValue({
      data: { items: [SAMPLE_GRANT] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders page heading", () => {
    render(<ResearchGrantsPage />);
    expect(screen.getByText(/Research Grants Pipeline/i)).toBeInTheDocument();
  });

  it("renders grant row data", () => {
    render(<ResearchGrantsPage />);
    expect(screen.getByText("AI for Education Research")).toBeInTheDocument();
    expect(screen.getByText("GR-2026-01")).toBeInTheDocument();
    expect(screen.getByText("FAC-001")).toBeInTheDocument();
  });

  it("renders status badge", () => {
    render(<ResearchGrantsPage />);
    expect(screen.getByText("active")).toBeInTheDocument();
  });

  it("renders create form fields", () => {
    render(<ResearchGrantsPage />);
    expect(screen.getByLabelText(/Grant Code/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Principal Investigator/i)).toBeInTheDocument();
  });

  it("shows empty state when no grants", () => {
    useGrantsMock.mockReturnValue({
      data: { items: [] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<ResearchGrantsPage />);
    expect(screen.getByText(/No grants found/i)).toBeInTheDocument();
  });

  it("shows access denied without permission", () => {
    allowAccess = false;
    render(<ResearchGrantsPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
