import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import ProfilesPage from "../../app/(admin)/console/profiles/page";

let allowAccess = true;

const useProfilePeopleMock = vi.fn();
const useProfileDepartmentsMock = vi.fn();

vi.mock("../../modules/profiles-admin/hooks", () => ({
  useProfilePeople: (...args: unknown[]) => useProfilePeopleMock(...args),
  useProfileDepartments: (...args: unknown[]) =>
    useProfileDepartmentsMock(...args),
  useCreateProfilePerson: () => ({ mutate: vi.fn(), isPending: false }),
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
  usePathname: () => "/console/profiles",
  useSearchParams: () => new URLSearchParams(),
}));

describe("ProfilesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useProfilePeopleMock.mockReturnValue({
      data: {
        items: [
          {
            id: 1,
            email: "dean@example.edu",
            first_name: "Dana",
            last_name: "Nurtayeva",
            status: "active",
            version: 1,
            created_at: "2026-01-01T00:00:00Z",
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    useProfileDepartmentsMock.mockReturnValue({
      data: {
        items: [
          {
            id: 5,
            code: "CS",
            name: "Computer Science",
            unit_type: "department",
            status: "active",
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders profiles page sections", () => {
    render(<ProfilesPage />);
    expect(screen.getByTestId("profiles-page")).toBeInTheDocument();
    expect(screen.getByText("Profiles")).toBeInTheDocument();
    expect(screen.getAllByText("Departments").length).toBeGreaterThanOrEqual(1);
  });

  it("renders people and departments rows", () => {
    render(<ProfilesPage />);
    expect(screen.getByText("Dana Nurtayeva")).toBeInTheDocument();
    expect(screen.getByText("dean@example.edu")).toBeInTheDocument();
    expect(screen.getByText("Computer Science")).toBeInTheDocument();
  });

  it("shows empty states when lists are empty", () => {
    useProfilePeopleMock.mockReturnValue({
      data: { items: [], total: 0, page: 1, page_size: 20 },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    useProfileDepartmentsMock.mockReturnValue({
      data: { items: [], total: 0, page: 1, page_size: 20 },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<ProfilesPage />);
    expect(screen.getByText(/No people found\./i)).toBeInTheDocument();
    expect(screen.getByText(/No departments found\./i)).toBeInTheDocument();
  });

  it("shows access denied when read permission is missing", () => {
    allowAccess = false;
    render(<ProfilesPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
