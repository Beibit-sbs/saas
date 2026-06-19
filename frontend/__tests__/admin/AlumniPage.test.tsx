import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import AlumniPage from "../../app/(admin)/console/alumni/page";

const useAlumniMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/alumni/hooks", () => ({
  useAlumniRecords: (...args: unknown[]) => useAlumniMock(...args),
  useAlumniBrainContext: () => ({
    data: {
      module: "alumni",
      tenant_id: 1,
      total_records: 1,
      by_status: { active: 1, engaged: 0, donor: 0, inactive: 0 },
      by_engagement_type: { event: 1 },
      inactive_count: 0,
      risk_level: "low",
    },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useCreateAlumniRecord: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateAlumniStatus: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("../../modules/students/hooks", () => ({
  useStudents: () => ({
    data: {
      items: [
        {
          id: "510",
          student_number: "S-510",
          first_name: "Aida",
          last_name: "Graduate",
          email: "aida@example.edu",
          status: "graduated",
          current_status: "graduated",
          tenant_id: "1",
          program: null,
          enrollment_year: null,
          version: 2,
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
        },
      ],
      total: 1,
    },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
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
  usePathname: () => "/console/alumni",
  useSearchParams: () => new URLSearchParams(),
}));

describe("AlumniPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useAlumniMock.mockReturnValue({
      data: {
        items: [
          {
            id: 1,
            tenant_id: "1",
            student_id: 510,
            graduation_year: 2024,
            status: "active",
            engagement_type: "event",
            employer: "Contoso",
            contact_email: "alumni510@example.edu",
            notes: "Interested in mentoring",
          },
        ],
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders page shell", () => {
    render(<AlumniPage />);
    expect(screen.getByTestId("alumni-page")).toBeInTheDocument();
    expect(screen.getByText(/Alumni Lifecycle/i)).toBeInTheDocument();
  });

  it("renders alumni row", () => {
    render(<AlumniPage />);
    expect(screen.getByText("Contoso")).toBeInTheDocument();
    expect(screen.getByText("event")).toBeInTheDocument();
  });

  it("renders create button", () => {
    render(<AlumniPage />);
    expect(screen.getByTestId("create-alumni-btn")).toBeInTheDocument();
  });

  it("renders status filter and lifecycle actions", () => {
    render(<AlumniPage />);
    expect(screen.getByTestId("alumni-status-filter")).toBeInTheDocument();
    expect(screen.getByText("Mark donor")).toBeInTheDocument();
    expect(screen.getByText("Mark inactive")).toBeInTheDocument();
  });

  it("shows access denied without permission", () => {
    allowAccess = false;
    render(<AlumniPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
