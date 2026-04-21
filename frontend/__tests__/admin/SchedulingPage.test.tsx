import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import SchedulingPage from "../../app/(admin)/console/scheduling/page";

const hasPermissionMock = vi.fn();

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
  useSections: () => ({
    data: { items: [], total: 0 },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
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
  });

  it("renders scheduling workspace when read permission exists", () => {
    render(<SchedulingPage />);

    expect(screen.getByText("nav.scheduling")).toBeInTheDocument();
    expect(screen.getByText("No sections found")).toBeInTheDocument();
    expect(screen.getByText("Lesson attendance")).toBeInTheDocument();
    expect(screen.getByText("Attendance risk summary")).toBeInTheDocument();
    expect(screen.getByText("At-risk ratio (high+medium)")).toBeInTheDocument();
    expect(screen.getByText("Load lessons")).toBeInTheDocument();
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
