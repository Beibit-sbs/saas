import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import SchedulingPage from "../../app/(admin)/console/scheduling/page";

const hasPermissionMock = vi.fn();
const useSectionsMock = vi.fn();
const useCoursesMock = vi.fn();
const useAcademicTermsMock = vi.fn();
const useEnrollmentsMock = vi.fn();
const useStudentsMock = vi.fn();

vi.mock("../../modules/platform/kpi/wave1-kpi-bar", () => ({
  Wave1KpiBar: () => <div data-testid="wave1-kpi-bar-mock" />,
}));

vi.mock("../../shared/hooks/use-permissions", () => ({
  usePermissions: () => ({
    hasPermission: hasPermissionMock,
    hasAnyPermission: hasPermissionMock,
    roles: [],
  }),
}));

vi.mock("../../shared/hooks/use-table-query-state", () => ({
  useTableQueryState: () => ({
    page: 1,
    pageSize: 20,
    filters: { semester: "", status: "" },
    sort: { key: "semester", direction: "desc" as const },
    setFilter: vi.fn(),
    resetFilters: vi.fn(),
    setPage: vi.fn(),
    setPageSize: vi.fn(),
    setSort: vi.fn(),
  }),
}));

vi.mock("../../modules/scheduling/hooks", () => ({
  useSections: (...args: unknown[]) => useSectionsMock(...args),
  useLessonAttendance: () => ({
    data: {
      total: 1,
      items: [
        {
          id: 1,
          student_profile_id: 1001,
          attendance_status: "present",
          marked_by: "qa.tester",
        },
      ],
    },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useSectionLessons: () => ({
    data: {
      total: 1,
      page: 1,
      page_size: 20,
      items: [
        {
          id: 501,
          section_id: 1,
          scheduled_date: "2026-04-20",
          topic_title: "Attendance checkpoint",
          status: "scheduled",
        },
      ],
    },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useStudentLatestRisk: () => ({
    data: null,
    isLoading: false,
    error: null,
  }),
  useStudentRiskHistory: () => ({
    data: {
      student_profile_id: 1001,
      total: 2,
      page: 1,
      page_size: 5,
      items: [
        {
          signal_type: "attendance_risk",
          severity: "high",
          detected_at: "2026-04-20T08:00:00Z",
          current_value: 4,
          threshold_value: 3,
          associated_case_id: 10,
        },
        {
          signal_type: "attendance_risk",
          severity: "medium",
          detected_at: "2026-04-20T07:00:00Z",
          current_value: 3,
          threshold_value: 3,
          associated_case_id: null,
        },
      ],
    },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useInterventionRiskSummary: () => ({
    data: {
      tenant_id: 1,
      open_cases_total: 0,
      signals_last_24h: 0,
      auto_created_cases_last_24h: 0,
      severity_breakdown: { high: 0, medium: 0, low: 0 },
    },
    isLoading: false,
    error: null,
  }),
  useUpsertLessonAttendance: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
  useCreateSection: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
  useCreateSectionLesson: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
  useAttendanceTrends: () => ({
    data: {
      section_id: 1,
      total_students: 30,
      total_lessons: 5,
      data_points: [
        { date: "2026-04-15", attendance_rate: 0.85 },
        { date: "2026-04-16", attendance_rate: 0.80 },
        { date: "2026-04-17", attendance_rate: 0.90 },
        { date: "2026-04-18", attendance_rate: 0.88 },
      ],
    },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
}));

vi.mock("../../modules/courses/hooks", () => ({
  useCourses: (...args: unknown[]) => useCoursesMock(...args),
}));

vi.mock("../../modules/academic-terms/hooks", () => ({
  useAcademicTerms: (...args: unknown[]) => useAcademicTermsMock(...args),
  useCreateAcademicTerm: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
}));

vi.mock("../../modules/enrollments/hooks", () => ({
  useEnrollments: (...args: unknown[]) => useEnrollmentsMock(...args),
}));

vi.mock("../../modules/students/hooks", () => ({
  useStudents: (...args: unknown[]) => useStudentsMock(...args),
}));

vi.mock("../../shared/hooks/use-mutation-feedback", () => ({
  useMutationFeedback: () => ({
    getHandlers: () => ({
      onSuccess: vi.fn(),
      onError: vi.fn(),
    }),
  }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

vi.mock("../../app/components/LanguageProvider", () => ({
  useLanguage: () => ({
    t: (key: string) => key,
  }),
}));

describe("SchedulingPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    hasPermissionMock.mockReturnValue(true);
    useSectionsMock.mockReturnValue({
      data: { items: [], total: 0 },
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
    useAcademicTermsMock.mockReturnValue({
      data: {
        total: 1,
        page: 1,
        page_size: 100,
        items: [
          {
            id: 7,
            tenant_id: 1,
            term_code: "2026-FALL",
            term_name: "Fall 2026",
            start_date: "2026-09-01T00:00:00Z",
            end_date: "2026-12-20T00:00:00Z",
            add_drop_deadline: "2026-09-15T00:00:00Z",
            status: "active",
            metadata_json: {},
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          },
        ],
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    useEnrollmentsMock.mockReturnValue({
      data: {
        total: 1,
        page: 1,
        page_size: 200,
        items: [
          {
            id: 9001,
            tenant_id: 1,
            student_profile_id: 1001,
            course_id: 22,
            term_id: 7,
            section_id: 55,
            enrollment_status: "enrolled",
            enrolled_at: "2026-09-01T00:00:00Z",
            version: 1,
          },
        ],
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
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
  });

  it("renders scheduling workspace when read permission exists", () => {
    render(<SchedulingPage />);

    expect(screen.getByText("nav.scheduling")).toBeInTheDocument();
    expect(screen.getByText("No sections found")).toBeInTheDocument();
    expect(screen.getByText("Lesson attendance")).toBeInTheDocument();
    expect(screen.getByText("Attendance risk summary")).toBeInTheDocument();
    expect(screen.getByText("Academic term and section setup")).toBeInTheDocument();
    expect(screen.getByText("At-risk ratio (high+medium)")).toBeInTheDocument();
    expect(screen.getByText("Load lessons")).toBeInTheDocument();
  });

  it("renders course and term selectors for section creation", () => {
    render(<SchedulingPage />);

    expect(screen.getByTestId("course-section-course-select")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /CS101 - Intro to Programming/ })).toBeInTheDocument();
    expect(screen.getByTestId("course-section-term-select")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /2026-FALL - Fall 2026/ })).toBeInTheDocument();
  });

  it("uses section and lesson selectors when sections are available", () => {
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
            status: "planned",
            version: 1,
          },
        ],
        total: 1,
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<SchedulingPage />);

    expect(screen.getByTestId("lesson-section-select")).toBeInTheDocument();
    fireEvent.change(screen.getByTestId("lesson-section-select"), { target: { value: "55" } });

    expect(screen.getByText("Section #55 · lessons: 1")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create lesson" })).toBeDisabled();
    expect(screen.getByTestId("attendance-lesson-select")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /#501 \/ 2026-04-20 \/ Attendance checkpoint/ })).toBeInTheDocument();
  });

  it("uses enrolled students as attendance choices", () => {
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
            status: "planned",
            version: 1,
          },
        ],
        total: 1,
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<SchedulingPage />);

    fireEvent.change(screen.getByTestId("lesson-section-select"), { target: { value: "55" } });
    fireEvent.change(screen.getByTestId("attendance-lesson-select"), { target: { value: "501" } });

    expect(screen.getByTestId("attendance-student-select")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /S-1001 \/ Aida Karim \/ Enrollment #9001/ })).toBeInTheDocument();
  });

  it("renders page-level severity filter in student risk timeline", () => {
    render(<SchedulingPage />);

    fireEvent.change(screen.getByPlaceholderText("Section ID"), { target: { value: "1" } });
    fireEvent.click(screen.getByRole("button", { name: "Load lessons" }));
    fireEvent.click(screen.getByRole("button", { name: "Use lesson" }));

    fireEvent.click(screen.getByRole("button", { name: "History" }));

    expect(screen.getByText("Student risk timeline")).toBeInTheDocument();
    expect(screen.getByLabelText("Filter severity")).toBeInTheDocument();
    expect(screen.getByText("Active filter: all")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reset filter" })).toBeDisabled();
    expect(screen.getByText("Page severity mix: H 1 · M 1 · L 0")).toBeInTheDocument();
    expect(screen.getByText("Highest severity on page: High")).toBeInTheDocument();
    expect(screen.getByText("Sorted by risk gap: descending")).toBeInTheDocument();
    expect(screen.getByText("Risk gap")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("Showing 2 of 2 records on this page")).toBeInTheDocument();
  });

  it("resets active severity filter to all", () => {
    render(<SchedulingPage />);

    fireEvent.change(screen.getByPlaceholderText("Section ID"), { target: { value: "1" } });
    fireEvent.click(screen.getByRole("button", { name: "Load lessons" }));
    fireEvent.click(screen.getByRole("button", { name: "Use lesson" }));

    fireEvent.click(screen.getByRole("button", { name: "History" }));
    fireEvent.change(screen.getByLabelText("Filter severity"), { target: { value: "high" } });

    expect(screen.getByText("Active filter: high")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reset filter" })).toBeEnabled();

    fireEvent.click(screen.getByRole("button", { name: "Reset filter" }));
    expect(screen.getByText("Active filter: all")).toBeInTheDocument();
  });

  it("allows closing the opened student risk timeline panel", () => {
    render(<SchedulingPage />);

    fireEvent.change(screen.getByPlaceholderText("Section ID"), { target: { value: "1" } });
    fireEvent.click(screen.getByRole("button", { name: "Load lessons" }));
    fireEvent.click(screen.getByRole("button", { name: "Use lesson" }));

    fireEvent.click(screen.getByRole("button", { name: "History" }));
    expect(screen.getByText("Student risk timeline")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Close timeline" }));
    expect(screen.queryByText("Student risk timeline")).not.toBeInTheDocument();
  });

  it("renders AccessDenied when scheduling read permission is missing", () => {
    hasPermissionMock.mockReturnValue(false);

    render(<SchedulingPage />);

    expect(hasPermissionMock).toHaveBeenCalled();
    expect(screen.getByText("Access Denied")).toBeInTheDocument();
  });

  it("displays attendance trends when section is selected", () => {
    render(<SchedulingPage />);

    // Load lessons requires section input
    const sectionInput = screen.getByPlaceholderText("Section ID");
    fireEvent.change(sectionInput, { target: { value: "1" } });
    fireEvent.click(screen.getByRole("button", { name: "Load lessons" }));

    // Wait for trends to appear (they're shown when activeSectionId is set)
    expect(screen.getByText("Attendance trends")).toBeInTheDocument();
    expect(screen.getByText(/Historical attendance rate by lesson date/)).toBeInTheDocument();
    expect(screen.getByText("85%")).toBeInTheDocument();
    expect(screen.getByText("80%")).toBeInTheDocument();
    expect(screen.getByText("90%")).toBeInTheDocument();
  });
});
