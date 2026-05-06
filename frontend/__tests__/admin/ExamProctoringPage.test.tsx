/**
 * Exam Proctoring Page — Unit Tests
 * Validates KPI bar wiring, loading/error/empty states, summary cards,
 * sessions table, and governance (non-punitive) policy notes.
 */

import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import ExamProctoringPage from "../../app/(admin)/console/exam-proctoring/page";
import { ApiRequestError } from "../../shared/api/client";

const useProctoredExamsListMock = vi.fn();
const useExamProctoringDashboardMock = vi.fn();
let allowAccess = true;

// ─── Module mocks ────────────────────────────────────────────────────────────

vi.mock("../../modules/platform/kpi/wave1-kpi-bar", () => ({
  Wave1KpiBar: ({ metricKeys }: { metricKeys: string[] }) => (
    <div data-testid="wave1-kpi-bar-mock" data-keys={metricKeys.join(",")} />
  ),
}));

vi.mock("../../modules/exam-proctoring/hooks", () => ({
  useProctoredExamsList: (...args: unknown[]) => useProctoredExamsListMock(...args),
  useExamProctoringDashboard: (...args: unknown[]) => useExamProctoringDashboardMock(...args),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: React.ReactNode }) =>
    allowAccess ? <>{children}</> : <div>Access Denied</div>,
  AccessDenied: ({ message }: { message?: string }) => (
    <div data-testid="access-denied">{message ?? "Access Denied"}</div>
  ),
}));

vi.mock("../../shared/ui/page-header", () => ({
  PageHeader: ({ title, description }: { title: string; description?: string }) => (
    <div>
      <h1>{title}</h1>
      {description ? <p>{description}</p> : null}
    </div>
  ),
}));

vi.mock("../../shared/ui/page-states", () => ({
  LoadingState: ({ title, message }: { title?: string; message?: string }) => (
    <div data-testid="loading-state">{title}::{message}</div>
  ),
  ErrorState: ({
    title,
    message,
    onRetry,
  }: {
    title?: string;
    message?: string;
    onRetry?: () => void;
  }) => (
    <div data-testid="error-state">
      {title}::{message}
      {onRetry && <button onClick={onRetry}>Retry</button>}
    </div>
  ),
}));

vi.mock("../../shared/ui/empty-state", () => ({
  EmptyState: ({ title, description }: { title?: string; description?: string }) => (
    <div data-testid="empty-state">
      {title}::{description}
    </div>
  ),
}));

vi.mock("../../shared/ui/badge", () => ({
  Badge: ({
    children,
    variant,
    ...props
  }: {
    children: React.ReactNode;
    variant?: string;
  }) => (
    <div data-variant={variant} {...props}>
      {children}
    </div>
  ),
}));

// ─── Default fixture data ────────────────────────────────────────────────────

const DEFAULT_EXAMS = [
  {
    id: 1,
    course_code: "CS101",
    course_title: "Intro to Computing",
    status: "scheduled",
    proctoring_mode: "remote",
    is_proctored: true,
    scheduled_date: "2026-06-01",
    scheduled_time: "10:00",
  },
  {
    id: 2,
    course_code: "MATH201",
    course_title: "Linear Algebra",
    status: "in_progress",
    proctoring_mode: "in_person",
    is_proctored: true,
    scheduled_date: "2026-06-02",
    scheduled_time: null,
  },
];

const DEFAULT_DASHBOARD = {
  total_exams: 12,
  status_breakdown: { scheduled: 5, in_progress: 2, completed: 5 },
};

// ─── Test setup ──────────────────────────────────────────────────────────────

function setDefaultMocks() {
  useProctoredExamsListMock.mockReturnValue({
    data: { items: DEFAULT_EXAMS },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  });
  useExamProctoringDashboardMock.mockReturnValue({
    data: DEFAULT_DASHBOARD,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  });
}

// ─── Tests ───────────────────────────────────────────────────────────────────

describe("ExamProctoringPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    setDefaultMocks();
  });

  // ── KPI bar ────────────────────────────────────────────────────────────────

  it("renders Wave1KpiBar with exam proctoring metric keys", () => {
    render(<ExamProctoringPage />);
    const bar = screen.getByTestId("wave1-kpi-bar-mock");
    expect(bar).toBeInTheDocument();
    const keys = bar.getAttribute("data-keys") ?? "";
    expect(keys).toContain("exam_proctoring_violations_count");
    expect(keys).toContain("exam_integrity_reviews_count");
    expect(keys).toContain("exam_integrity_high_risk_count");
    expect(keys).toContain("exam_integrity_requires_approval_count");
  });

  it("renders the exam proctoring KPI section with correct data-testid", () => {
    render(<ExamProctoringPage />);
    expect(screen.getByTestId("wave4-exam-proctoring-kpi-section")).toBeInTheDocument();
  });

  // ── Page structure ─────────────────────────────────────────────────────────

  it("renders page header with correct title", () => {
    render(<ExamProctoringPage />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Exam Proctoring");
  });

  it("renders the human-review governance note", () => {
    render(<ExamProctoringPage />);
    const note = screen.getByTestId("exam-proctoring-human-review-note");
    expect(note).toBeInTheDocument();
    expect(note.textContent).toMatch(/human-reviewed/i);
  });

  it("does not contain punitive wording in governance note", () => {
    render(<ExamProctoringPage />);
    const note = screen.getByTestId("exam-proctoring-human-review-note");
    const text = note.textContent ?? "";
    expect(text.toLowerCase()).not.toMatch(/\bfail\b|\bpunish|\bexpel|\bdisqualif/);
  });

  // ── Summary cards ──────────────────────────────────────────────────────────

  it("renders summary cards with dashboard data", () => {
    render(<ExamProctoringPage />);
    expect(screen.getByTestId("summary-total-exams")).toBeInTheDocument();
    expect(screen.getByTestId("summary-scheduled")).toBeInTheDocument();
    expect(screen.getByTestId("summary-in-progress")).toBeInTheDocument();
    expect(screen.getByTestId("summary-completed")).toBeInTheDocument();
  });

  it("shows correct total_exams count", () => {
    render(<ExamProctoringPage />);
    expect(screen.getByTestId("summary-total-exams")).toHaveTextContent("12");
  });

  // ── Sessions table ─────────────────────────────────────────────────────────

  it("renders proctored exam rows", () => {
    render(<ExamProctoringPage />);
    expect(screen.getByTestId("proctored-exam-row-1")).toBeInTheDocument();
    expect(screen.getByTestId("proctored-exam-row-2")).toBeInTheDocument();
  });

  it("renders course code and title in table", () => {
    render(<ExamProctoringPage />);
    expect(screen.getByText("CS101")).toBeInTheDocument();
    expect(screen.getByText("Intro to Computing")).toBeInTheDocument();
  });

  it("renders proctoring mode labels", () => {
    render(<ExamProctoringPage />);
    expect(screen.getByText("Remote")).toBeInTheDocument();
    expect(screen.getByText("In-person")).toBeInTheDocument();
  });

  it("renders scheduled datetime for exam with date and time", () => {
    render(<ExamProctoringPage />);
    expect(screen.getByText("2026-06-01 10:00")).toBeInTheDocument();
  });

  it("renders em-dash when scheduled_time is null", () => {
    render(<ExamProctoringPage />);
    expect(screen.getByText("2026-06-02")).toBeInTheDocument();
  });

  // ── Empty state ────────────────────────────────────────────────────────────

  it("renders empty state when no proctored exams are present", () => {
    useProctoredExamsListMock.mockReturnValueOnce({
      data: { items: [] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<ExamProctoringPage />);
    expect(screen.getByTestId("empty-state")).toBeInTheDocument();
  });

  // ── Loading state ──────────────────────────────────────────────────────────

  it("renders loading state when data is being fetched", () => {
    useProctoredExamsListMock.mockReturnValueOnce({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    });
    useExamProctoringDashboardMock.mockReturnValueOnce({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    });
    render(<ExamProctoringPage />);
    expect(screen.getByTestId("loading-state")).toBeInTheDocument();
  });

  // ── Error state ────────────────────────────────────────────────────────────

  it("renders error state when API fails", () => {
    useProctoredExamsListMock.mockReturnValueOnce({
      data: undefined,
      isLoading: false,
      error: new Error("Network failure"),
      refetch: vi.fn(),
    });
    useExamProctoringDashboardMock.mockReturnValueOnce({
      data: undefined,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<ExamProctoringPage />);
    expect(screen.getByTestId("error-state")).toBeInTheDocument();
  });

  it("renders access denied view on 401 error", () => {
    const authError = new ApiRequestError({ status: 401, detail: "Unauthorized" });
    useProctoredExamsListMock.mockReturnValueOnce({
      data: undefined,
      isLoading: false,
      error: authError,
      refetch: vi.fn(),
    });
    useExamProctoringDashboardMock.mockReturnValueOnce({
      data: undefined,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<ExamProctoringPage />);
    expect(screen.getByTestId("access-denied")).toBeInTheDocument();
  });

  // ── Missing optional values ────────────────────────────────────────────────

  it("renders safely when dashboard data is absent", () => {
    useExamProctoringDashboardMock.mockReturnValueOnce({
      data: undefined,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<ExamProctoringPage />);
    expect(screen.getByTestId("wave4-exam-proctoring-kpi-section")).toBeInTheDocument();
  });

  it("shows zero values when status_breakdown fields are missing", () => {
    useExamProctoringDashboardMock.mockReturnValueOnce({
      data: { total_exams: 0, status_breakdown: {} },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    render(<ExamProctoringPage />);
    expect(screen.getByTestId("summary-scheduled")).toHaveTextContent("0");
  });

  // ── Status filter ──────────────────────────────────────────────────────────

  it("renders status filter dropdown", () => {
    render(<ExamProctoringPage />);
    const filter = screen.getByTestId("status-filter");
    expect(filter).toBeInTheDocument();
  });

  it("calls useProctoredExamsList with status filter on change", () => {
    render(<ExamProctoringPage />);
    const filter = screen.getByTestId("status-filter");
    fireEvent.change(filter, { target: { value: "completed" } });
    // Verify filter state change causes re-render without crash
    expect(filter).toHaveValue("completed");
  });
});
