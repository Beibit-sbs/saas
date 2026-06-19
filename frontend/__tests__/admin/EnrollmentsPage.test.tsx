import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import EnrollmentsPage from "../../app/(admin)/console/enrollments/page";

let allowAccess = true;
const useStudentsMock = vi.fn();
const useCoursesMock = vi.fn();
const useSectionsMock = vi.fn();

vi.mock("../../shared/ui/permission-gate", () => ({
  PermissionGate: ({ children }: { children: ReactNode }) =>
    allowAccess ? <>{children}</> : null,
  RequirePermission: ({ children }: { children: ReactNode; permission: string }) =>
    allowAccess ? <>{children}</> : <div>Access Denied</div>,
  AccessDenied: ({ message }: { message?: string }) => (
    <div>{message ?? "Access Denied"}</div>
  ),
}));

vi.mock("../../shared/hooks/use-table-query-state", () => ({
  useTableQueryState: () => ({
    page: 1,
    pageSize: 20,
    filters: { status: "" },
    sort: { key: "enrolled", direction: "desc" as const },
    setFilter: vi.fn(),
    resetFilters: vi.fn(),
    setPage: vi.fn(),
    setPageSize: vi.fn(),
    setSort: vi.fn(),
  }),
}));

vi.mock("../../shared/hooks/use-detail-drawer", () => ({
  useDetailDrawer: () => ({
    isOpen: false,
    selectedId: null,
    open: vi.fn(),
    close: vi.fn(),
  }),
}));

vi.mock("../../shared/hooks/use-mutation-feedback", () => ({
  useMutationFeedback: () => ({
    getHandlers: () => ({ onSuccess: vi.fn(), onError: vi.fn() }),
  }),
}));

vi.mock("../../modules/enrollments/hooks", () => ({
  useEnrollments: () => ({
    data: { items: [], total: 0 },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useDropEnrollment: () => ({ mutate: vi.fn(), isPending: false }),
  useCreateEnrollment: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("../../modules/students/hooks", () => ({
  useStudents: (...args: unknown[]) => useStudentsMock(...args),
}));

vi.mock("../../modules/courses/hooks", () => ({
  useCourses: (...args: unknown[]) => useCoursesMock(...args),
}));

vi.mock("../../modules/scheduling/hooks", () => ({
  useSections: (...args: unknown[]) => useSectionsMock(...args),
}));

vi.mock("../../app/components/LanguageProvider", () => ({
  useLanguage: () => ({
    t: (key: string) => key,
  }),
}));

describe("EnrollmentsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useStudentsMock.mockReturnValue({
      data: {
        items: [
          {
            id: "1001",
            student_number: "S-1001",
            first_name: "Aida",
            last_name: "Karim",
            email: "aida@example.edu",
            status: "active",
            tenant_id: "1",
            program: null,
            enrollment_year: 2026,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          },
        ],
        total: 1,
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    useCoursesMock.mockReturnValue({
      data: {
        courses: [
          {
            id: 22,
            tenant_id: "1",
            course_code: "CS101",
            title: "Intro to Programming",
            credits: 3,
            program_id: 1,
            status: "active",
          },
        ],
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    useSectionsMock.mockReturnValue({
      data: { items: [], total: 0, page: 1, page_size: 100 },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders AccessDenied when enrollments read permission is missing", () => {
    allowAccess = false;

    render(<EnrollmentsPage />);

    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });

  it("uses student and course selectors when creating an enrollment", () => {
    render(<EnrollmentsPage />);

    fireEvent.click(screen.getByRole("button", { name: /enroll student/i }));

    expect(screen.getByTestId("enrollment-student-select")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /S-1001/ })).toBeInTheDocument();
    expect(screen.getByTestId("enrollment-course-select")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /CS101 - Intro to Programming/ })).toBeInTheDocument();
  });

  it("uses scheduling sections when available for enrollment creation", () => {
    useSectionsMock.mockReturnValue({
      data: {
        items: [
          {
            id: 55,
            tenant_id: 1,
            course_id: 22,
            term_id: 7,
            section_code: "CS101-A",
            instructor_id: "faculty-1",
            max_capacity: 30,
            status: "scheduled",
            version: 1,
          },
        ],
        total: 1,
        page: 1,
        page_size: 100,
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<EnrollmentsPage />);

    fireEvent.click(screen.getByRole("button", { name: /enroll student/i }));

    expect(screen.getByTestId("enrollment-section-select")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /CS101-A \/ CS101 - Intro to Programming \/ Term #7/ })).toBeInTheDocument();
  });
});
