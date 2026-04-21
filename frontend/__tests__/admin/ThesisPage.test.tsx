import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import ThesisPage from "../../app/(admin)/console/thesis/page";

const useThesisMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/thesis/hooks", () => ({
  useThesis: (...args: unknown[]) => useThesisMock(...args),
  useCreateThesis: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateThesisStatus: () => ({ mutate: vi.fn(), isPending: false }),
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
  usePathname: () => "/console/thesis",
  useSearchParams: () => new URLSearchParams(),
}));

describe("ThesisPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useThesisMock.mockReturnValue({
      data: {
        items: [
          {
            id: 1,
            tenant_id: "1",
            thesis_code: "TH-2026-001",
            student_id: 101,
            title: "Adaptive Learning Paths",
            advisor_faculty_id: "FAC-101",
            status: "draft",
            defense_date: null,
            repository_url: null,
          },
        ],
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders thesis page and row", () => {
    render(<ThesisPage />);
    expect(screen.getByTestId("thesis-page")).toBeInTheDocument();
    expect(screen.getByText("TH-2026-001")).toBeInTheDocument();
    expect(screen.getByText("Adaptive Learning Paths")).toBeInTheDocument();
  });

  it("shows access denied without permission", () => {
    allowAccess = false;
    render(<ThesisPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
