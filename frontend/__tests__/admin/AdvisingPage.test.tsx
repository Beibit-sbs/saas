import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import AdvisingPage from "../../app/(admin)/console/advising/page";

const useAdvisingMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/advising/hooks", () => ({
  useAdvisingSessions: (...args: unknown[]) => useAdvisingMock(...args),
  useCreateAdvisingSession: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateAdvisingSessionStatus: () => ({ mutate: vi.fn(), isPending: false }),
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
  usePathname: () => "/console/advising",
  useSearchParams: () => new URLSearchParams(),
}));

describe("AdvisingPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useAdvisingMock.mockReturnValue({
      data: {
        items: [
          {
            id: 1,
            tenant_id: "1",
            student_id: 101,
            advisor_id: "FAC-101",
            session_type: "academic",
            status: "scheduled",
            scheduled_at: "2026-05-01T10:00",
            notes: "Discuss Q3 grades",
            outcome: null,
          },
        ],
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders the advising page with title", () => {
    render(<AdvisingPage />);
    expect(screen.getByTestId("advising-page")).toBeInTheDocument();
    expect(screen.getByText(/Advising & Mentoring/i)).toBeInTheDocument();
  });

  it("renders sessions table with data", () => {
    render(<AdvisingPage />);
    expect(screen.getByText("FAC-101")).toBeInTheDocument();
    expect(screen.getByText("101")).toBeInTheDocument();
  });

  it("renders Schedule session button", () => {
    render(<AdvisingPage />);
    expect(screen.getByTestId("create-session-btn")).toBeInTheDocument();
  });

  it("displays session status badge", () => {
    render(<AdvisingPage />);
    expect(screen.getByText("scheduled")).toBeInTheDocument();
  });

  it("renders session type column", () => {
    render(<AdvisingPage />);
    expect(screen.getByText("academic")).toBeInTheDocument();
  });

  it("shows access denied without permission", () => {
    allowAccess = false;
    render(<AdvisingPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
