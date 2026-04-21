import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import HousingPage from "../../app/(admin)/console/housing/page";

const useHousingMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/housing/hooks", () => ({
  useHousingRequests: (...args: unknown[]) => useHousingMock(...args),
  useCreateHousingRequest: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateHousingRequestStatus: () => ({ mutate: vi.fn(), isPending: false }),
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
  usePathname: () => "/console/housing",
  useSearchParams: () => new URLSearchParams(),
}));

describe("HousingPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useHousingMock.mockReturnValue({
      data: {
        items: [
          {
            id: 1,
            tenant_id: "1",
            student_id: 410,
            request_type: "assignment",
            dormitory: "North Hall",
            room_preference: "double",
            status: "submitted",
            manager_id: "HSG-1",
            notes: "Needs quiet floor",
          },
        ],
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders page shell", () => {
    render(<HousingPage />);
    expect(screen.getByTestId("housing-page")).toBeInTheDocument();
    expect(screen.getByText(/Dormitory & Housing/i)).toBeInTheDocument();
  });

  it("renders request row", () => {
    render(<HousingPage />);
    expect(screen.getByText("North Hall")).toBeInTheDocument();
    expect(screen.getByText("assignment")).toBeInTheDocument();
  });

  it("renders create button", () => {
    render(<HousingPage />);
    expect(screen.getByTestId("create-housing-btn")).toBeInTheDocument();
  });

  it("shows access denied without permission", () => {
    allowAccess = false;
    render(<HousingPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
