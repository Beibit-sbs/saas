import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import CoursesPage from "../../app/(admin)/console/courses/page";

const useCoursesMock = vi.fn();
let allowAccess = true;

vi.mock("../../modules/courses/hooks", () => ({
  useCourses: (...args: unknown[]) => useCoursesMock(...args),
  useCreateCourse: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateCourse: () => ({ mutate: vi.fn(), isPending: false }),
  useDeleteCourse: () => ({ mutate: vi.fn(), isPending: false }),
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
  usePathname: () => "/console/courses",
  useSearchParams: () => new URLSearchParams(),
}));

const COURSES = [
  {
    id: 1,
    tenant_id: "1",
    course_code: "CS101",
    title: "Intro to Programming",
    credits: 3,
    program_id: 1,
    status: "active",
  },
  {
    id: 2,
    tenant_id: "1",
    course_code: "MATH201",
    title: "Linear Algebra",
    credits: 4,
    program_id: 2,
    status: "active",
  },
];

describe("CoursesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useCoursesMock.mockReturnValue({
      data: { courses: COURSES },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders courses page and rows", () => {
    render(<CoursesPage />);
    expect(screen.getByTestId("courses-page")).toBeInTheDocument();
    expect(screen.getByText("CS101")).toBeInTheDocument();
    expect(screen.getByText("Linear Algebra")).toBeInTheDocument();
  });

  it("shows course specific columns", () => {
    render(<CoursesPage />);
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /delete|удалить|жою/i }).length).toBeGreaterThanOrEqual(1);
  });

  it("shows empty state when no courses", () => {
    useCoursesMock.mockReturnValue({
      data: { courses: [] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<CoursesPage />);
    expect(screen.getByText(/No courses found\./i)).toBeInTheDocument();
  });

  it("shows access denied when read permission is missing", () => {
    allowAccess = false;
    render(<CoursesPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
