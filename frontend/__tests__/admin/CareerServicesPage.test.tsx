import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import CareerServicesPage from "../../app/(admin)/console/career-services/page";

const useCareerMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/career_services/hooks", () => ({
  useCareerOpportunities: (...args: unknown[]) => useCareerMock(...args),
  useCreateCareerOpportunity: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateCareerOpportunityStatus: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  PermissionGate: ({ children }: { children: React.ReactNode }) =>
    allowAccess ? <>{children}</> : null,
  RequirePermission: ({ children }: { children: React.ReactNode; permission: string }) =>
    allowAccess ? <>{children}</> : <div>Access Denied</div>,
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
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
  usePathname: () => "/console/career-services",
  useSearchParams: () => new URLSearchParams(),
}));

describe("CareerServicesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useCareerMock.mockReturnValue({
      data: {
        items: [
          {
            id: 1,
            tenant_id: "1",
            student_id: 210,
            title: "Backend Intern",
            company: "Acme Labs",
            opportunity_type: "internship",
            status: "open",
            owner_id: "CAREER-1",
            start_date: "2026-06-01",
            notes: "Strong candidate",
          },
        ],
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders page shell", () => {
    render(<CareerServicesPage />);
    expect(screen.getByTestId("career-services-page")).toBeInTheDocument();
    expect(screen.getByText(/Career Services/i)).toBeInTheDocument();
  });

  it("renders opportunity row", () => {
    render(<CareerServicesPage />);
    expect(screen.getByText("Backend Intern")).toBeInTheDocument();
    expect(screen.getByText("Acme Labs")).toBeInTheDocument();
  });

  it("renders create button", () => {
    render(<CareerServicesPage />);
    expect(screen.getByTestId("create-opportunity-btn")).toBeInTheDocument();
  });

  it("shows access denied without permission", () => {
    allowAccess = false;
    render(<CareerServicesPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
