import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import FinancialAidPage from "../../app/(admin)/console/financial-aid/page";

vi.mock("../../modules/platform/kpi/wave1-kpi-bar", () => ({
  Wave1KpiBar: () => <div data-testid="wave1-kpi-bar-mock" />,
}));

const useAidMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/financial_aid/hooks", () => ({
  useFinancialAidRecords: (...args: unknown[]) => useAidMock(...args),
  useCreateFinancialAidRecord: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateFinancialAidStatus: () => ({ mutate: vi.fn(), isPending: false }),
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
  usePathname: () => "/console/financial-aid",
  useSearchParams: () => new URLSearchParams(),
}));

describe("FinancialAidPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useAidMock.mockReturnValue({
      data: {
        items: [
          {
            id: 1,
            tenant_id: "1",
            student_id: 310,
            aid_type: "scholarship",
            amount: 2500,
            currency: "USD",
            status: "pending",
            term: "2026-FALL",
            reviewer_id: "AID-1",
            notes: "Merit-based",
          },
        ],
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders page shell", () => {
    render(<FinancialAidPage />);
    expect(screen.getByTestId("financial-aid-page")).toBeInTheDocument();
    expect(screen.getByText(/Scholarship & Financial Aid/i)).toBeInTheDocument();
  });

  it("renders aid row", () => {
    render(<FinancialAidPage />);
    expect(screen.getByText("scholarship")).toBeInTheDocument();
    expect(screen.getByText("2026-FALL")).toBeInTheDocument();
  });

  it("renders create button", () => {
    render(<FinancialAidPage />);
    expect(screen.getByTestId("create-aid-btn")).toBeInTheDocument();
  });

  it("shows access denied without permission", () => {
    allowAccess = false;
    render(<FinancialAidPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
