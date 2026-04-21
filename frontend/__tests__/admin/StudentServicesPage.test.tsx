import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import StudentServicesPage from "../../app/(admin)/console/student-services/page";

const useTicketsMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/student_services/hooks", () => ({
  useStudentServiceTickets: (...args: unknown[]) => useTicketsMock(...args),
  useCreateStudentServiceTicket: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateStudentServiceTicketStatus: () => ({ mutate: vi.fn(), isPending: false }),
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
  usePathname: () => "/console/student-services",
  useSearchParams: () => new URLSearchParams(),
}));

describe("StudentServicesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useTicketsMock.mockReturnValue({
      data: {
        items: [
          {
            id: 1,
            tenant_id: "1",
            student_id: 110,
            category: "registrar",
            subject: "Enrollment certificate",
            description: "Need for embassy",
            priority: "high",
            status: "open",
            owner_id: "STAFF-7",
            channel: "portal",
            resolution_notes: null,
          },
        ],
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders the page shell", () => {
    render(<StudentServicesPage />);
    expect(screen.getByTestId("student-services-page")).toBeInTheDocument();
    expect(screen.getByText(/Student Services/i)).toBeInTheDocument();
  });

  it("renders ticket row", () => {
    render(<StudentServicesPage />);
    expect(screen.getByText("Enrollment certificate")).toBeInTheDocument();
    expect(screen.getByText("registrar")).toBeInTheDocument();
  });

  it("renders create button", () => {
    render(<StudentServicesPage />);
    expect(screen.getByTestId("create-ticket-btn")).toBeInTheDocument();
  });

  it("shows access denied when missing permission", () => {
    allowAccess = false;
    render(<StudentServicesPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
