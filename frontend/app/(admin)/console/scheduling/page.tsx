"use client";

import { useState } from "react";
import { PageHeader } from "@/shared/ui/page-header";
import { DataTable, Column } from "@/shared/ui/data-table";
import { FilterBar } from "@/shared/ui/filter-bar";
import { StatusBadge } from "@/shared/ui/status-badge";
import { ErrorState } from "@/shared/ui/error-state";
import { useTableQueryState } from "@/shared/hooks/use-table-query-state";
import {
  useInterventionRiskSummary,
  useLessonAttendance,
  useSectionLessons,
  useSections,
  useStudentRiskHistory,
  useStudentLatestRisk,
  useUpsertLessonAttendance,
  useAttendanceTrends,
  useCreateSection,
  useCreateSectionLesson,
} from "@/modules/scheduling/hooks";
import { CourseSection } from "@/modules/scheduling/types";
import { useCourses } from "@/modules/courses/hooks";
import { Course } from "@/modules/courses/types";
import { useAcademicTerms, useCreateAcademicTerm } from "@/modules/academic-terms/hooks";
import { AcademicTerm } from "@/modules/academic-terms/types";
import { useEnrollments } from "@/modules/enrollments/hooks";
import { useStudents } from "@/modules/students/hooks";
import { Student } from "@/modules/students/types";
import { Calendar } from "lucide-react";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { PERMISSIONS } from "@/shared/config/permissions";
import { AccessDenied } from "@/shared/ui/permission-gate";
import { useLanguage } from "@/app/components/LanguageProvider";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Button } from "@/shared/ui/button";
import { Label } from "@/shared/ui/label";
import { Badge } from "@/shared/ui/badge";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { Wave1KpiBar } from "@/modules/platform/kpi/wave1-kpi-bar";

const SCHEDULING_KPI_KEYS = [
  "scheduling_conflicts_count",
  "capacity_risk_sections_count",
  "course_fill_rate",
] as const;

const SCHEDULING_KPI_LABELS: Record<string, string> = {
  scheduling_conflicts_count: "Scheduling Conflicts",
  capacity_risk_sections_count: "Capacity-Risk Sections",
  course_fill_rate: "Fill Rate (%)",
};

const FILTER_FIELDS = [
  { key: "semester", label: "Semester", type: "text" as const, placeholder: "e.g. 2024-spring" },
  {
    key: "status",
    label: "Status",
    type: "select" as const,
    options: [
      { label: "Planned", value: "planned" },
      { label: "Scheduled", value: "scheduled" },
      { label: "Cancelled", value: "cancelled" },
    ],
  },
];

function StudentRiskBadge({ studentProfileId }: { studentProfileId: number }) {
  const { data, isLoading, error } = useStudentLatestRisk(studentProfileId);

  if (isLoading) {
    return <span className="text-xs text-muted-foreground">Loading...</span>;
  }
  if (error || !data || data.signal_type !== "attendance_risk") {
    return <span className="text-xs text-muted-foreground">—</span>;
  }

  if (data.severity === "high") {
    return <Badge variant="destructive">High</Badge>;
  }
  if (data.severity === "medium") {
    return <Badge variant="warning">Medium</Badge>;
  }
  return <Badge variant="success">Low</Badge>;
}

function dateInputToIso(value: string) {
  return value.trim() ? `${value.trim()}T00:00:00Z` : null;
}

function formatCourseOption(course: Course) {
  return `${course.course_code} - ${course.title}`;
}

function formatTermOption(term: AcademicTerm) {
  return `${term.term_code} - ${term.term_name}`;
}

function formatStudentOption(student: Student | undefined, fallbackId: string | number | undefined, enrollmentId: string | number) {
  if (student) {
    return `${student.student_number} / ${student.first_name} ${student.last_name} / Enrollment #${enrollmentId}`;
  }
  return `Student #${fallbackId ?? "-"} / Enrollment #${enrollmentId}`;
}

export default function SchedulingPage() {
  const { t } = useLanguage();
  const { hasPermission } = usePermissions();
  const { getHandlers } = useMutationFeedback();
  const table = useTableQueryState({ filterKeys: ["semester", "status"] as const, defaultPageSize: 20, defaultSort: { key: "semester", direction: "desc" } });
  const [sectionInput, setSectionInput] = useState("");
  const [activeSectionId, setActiveSectionId] = useState("");
  const [activeLessonId, setActiveLessonId] = useState("");
  const [lessonDate, setLessonDate] = useState("");
  const [lessonTopic, setLessonTopic] = useState("");
  const [lessonNotes, setLessonNotes] = useState("");
  const [selectedRiskStudentId, setSelectedRiskStudentId] = useState<number | null>(null);
  const [selectedRiskHistoryPage, setSelectedRiskHistoryPage] = useState(1);
  const [selectedRiskHistorySeverityFilter, setSelectedRiskHistorySeverityFilter] = useState<"all" | "high" | "medium" | "low">("all");
  const [studentInput, setStudentInput] = useState("");
  const [attendanceStatus, setAttendanceStatus] = useState<"present" | "absent" | "late" | "excused">("present");
  const [termCode, setTermCode] = useState("");
  const [termName, setTermName] = useState("");
  const [termStartDate, setTermStartDate] = useState("");
  const [termEndDate, setTermEndDate] = useState("");
  const [termAddDropDeadline, setTermAddDropDeadline] = useState("");
  const [sectionCourseId, setSectionCourseId] = useState("");
  const [sectionTermId, setSectionTermId] = useState("");
  const [sectionCode, setSectionCode] = useState("");
  const [sectionInstructorId, setSectionInstructorId] = useState("");
  const [sectionMaxCapacity, setSectionMaxCapacity] = useState("30");

  const { data, isLoading, error, refetch } = useSections({
    page: table.page,
    page_size: table.pageSize,
    semester: table.filters.semester,
    status: table.filters.status,
  });
  const {
    data: lessons,
    isLoading: lessonsLoading,
    error: lessonsError,
    refetch: refetchLessons,
  } = useSectionLessons(activeSectionId.trim());
  const {
    data: attendance,
    isLoading: attendanceLoading,
    error: attendanceError,
    refetch: refetchAttendance,
  } = useLessonAttendance(activeLessonId.trim());
  const {
    data: selectedStudentRiskHistory,
    isLoading: selectedStudentRiskHistoryLoading,
    error: selectedStudentRiskHistoryError,
    refetch: refetchSelectedStudentRiskHistory,
  } = useStudentRiskHistory(selectedRiskStudentId, { page: selectedRiskHistoryPage, page_size: 5 });
  const {
    data: riskSummary,
    isLoading: riskSummaryLoading,
    error: riskSummaryError,
    refetch: refetchRiskSummary,
  } = useInterventionRiskSummary();
  const coursesQuery = useCourses();
  const termsQuery = useAcademicTerms({ page: 1, page_size: 100, status: "active" });
  const studentsQuery = useStudents({ page: 1, page_size: 200, status: "active" });
  const createTerm = useCreateAcademicTerm();
  const createSection = useCreateSection();
  const createLesson = useCreateSectionLesson(activeSectionId.trim());
  const sectionEnrollments = useEnrollments(
    { page: 1, page_size: 200, section_id: activeSectionId.trim(), status: "enrolled" },
    { enabled: !!activeSectionId.trim() },
  );
  const upsertAttendance = useUpsertLessonAttendance(activeLessonId.trim());
  const trends = useAttendanceTrends(activeSectionId.trim(), 4);

  if (!hasPermission(PERMISSIONS.SCHEDULING_READ)) return <AccessDenied />;

  if (error) {
    return <ErrorState title="Failed to load sections" onRetry={refetch} />;
  }

  const columns: Column<CourseSection>[] = [
    { key: "code", header: "Code", cell: (r) => <code className="text-xs">{r.section_code ?? r.code ?? `#${r.id}`}</code>, sortValue: (r) => r.section_code ?? r.code ?? String(r.id) },
    { key: "course", header: "Course", cell: (r) => r.course_name ?? `Course #${r.course_id ?? "-"}`, sortValue: (r) => String(r.course_name ?? r.course_id ?? "").toLowerCase() },
    { key: "instructor", header: "Instructor", cell: (r) => r.instructor ?? r.instructor_id ?? "—", sortValue: (r) => r.instructor ?? r.instructor_id ?? "" },
    { key: "semester", header: "Term", cell: (r) => r.semester ?? `Term #${r.term_id ?? "-"}`, sortValue: (r) => r.semester ?? r.term_id ?? "" },
    { key: "schedule", header: "Schedule", cell: (r) => r.schedule ?? "—" },
    { key: "room", header: "Room", cell: (r) => r.room ?? "—", sortValue: (r) => r.room ?? "" },
    {
      key: "capacity",
      header: "Capacity",
      cell: (r) => `${r.enrolled_count ?? "—"} / ${r.capacity ?? r.max_capacity ?? "—"}`,
      sortValue: (r) => r.enrolled_count ?? 0,
    },
    { key: "status", header: "Status", cell: (r) => <StatusBadge status={r.status} />, sortValue: (r) => r.status },
  ];

  const canWriteAttendance = hasPermission(PERMISSIONS.SCHEDULING_WRITE);
  const sectionRows = data?.items ?? [];
  const courses = coursesQuery.data?.courses ?? [];
  const terms = termsQuery.data?.items ?? [];
  const students = studentsQuery.data?.items ?? [];
  const studentById = new Map(students.map((student) => [String(student.id), student]));
  const parsedStudentId = Number(studentInput.trim());
  const isStudentIdValid = Number.isInteger(parsedStudentId) && parsedStudentId > 0;
  const canSubmitAttendance = canWriteAttendance && !!activeLessonId.trim() && isStudentIdValid;
  const lessonRows = lessons?.items ?? [];
  const enrolledStudentRows = sectionEnrollments.data?.items ?? [];
  const canCreateLesson = canWriteAttendance && !!activeSectionId.trim() && !!lessonDate.trim() && !!lessonTopic.trim();
  const parsedSectionCourseId = Number(sectionCourseId);
  const parsedSectionTermId = Number(sectionTermId);
  const parsedSectionMaxCapacity = Number(sectionMaxCapacity);
  const canCreateTerm = canWriteAttendance && termCode.trim().length > 0 && termName.trim().length > 0;
  const canCreateSection =
    canWriteAttendance &&
    Number.isInteger(parsedSectionCourseId) &&
    parsedSectionCourseId > 0 &&
    Number.isInteger(parsedSectionTermId) &&
    parsedSectionTermId > 0 &&
    sectionCode.trim().length > 0 &&
    Number.isInteger(parsedSectionMaxCapacity) &&
    parsedSectionMaxCapacity >= 0;

  const attendanceRows = attendance?.items ?? [];
  const highSeverityCount = riskSummary?.severity_breakdown.high ?? 0;
  const mediumSeverityCount = riskSummary?.severity_breakdown.medium ?? 0;
  const lowSeverityCount = riskSummary?.severity_breakdown.low ?? 0;
  const severityTotal = highSeverityCount + mediumSeverityCount + lowSeverityCount;
  const atRiskCount = highSeverityCount + mediumSeverityCount;
  const atRiskRatioLabel = severityTotal > 0
    ? `${((atRiskCount / severityTotal) * 100).toFixed(1)}%`
    : "0.0%";
  const selectedRiskHistoryTotalPages = selectedStudentRiskHistory
    ? Math.max(1, Math.ceil(selectedStudentRiskHistory.total / selectedStudentRiskHistory.page_size))
    : 1;
  const canGoRiskHistoryPrev = (selectedStudentRiskHistory?.page ?? 1) > 1;
  const canGoRiskHistoryNext = (selectedStudentRiskHistory?.page ?? 1) < selectedRiskHistoryTotalPages;
  const riskHistoryPageSeverityCounts = selectedStudentRiskHistory
    ? selectedStudentRiskHistory.items.reduce(
      (acc, item) => {
        acc[item.severity] += 1;
        return acc;
      },
      { high: 0, medium: 0, low: 0 },
    )
    : { high: 0, medium: 0, low: 0 };
  const riskHistoryPageHighestSeverity = riskHistoryPageSeverityCounts.high > 0
    ? "High"
    : riskHistoryPageSeverityCounts.medium > 0
      ? "Medium"
      : riskHistoryPageSeverityCounts.low > 0
        ? "Low"
        : "—";
  const filteredRiskHistoryItems = selectedStudentRiskHistory
    ? selectedStudentRiskHistory.items.filter((item) =>
      selectedRiskHistorySeverityFilter === "all" ? true : item.severity === selectedRiskHistorySeverityFilter,
    )
    : [];
  const sortedRiskHistoryItems = [...filteredRiskHistoryItems].sort(
    (a, b) => (b.current_value - b.threshold_value) - (a.current_value - a.threshold_value),
  );

  return (
    <div className="space-y-4">
      <PageHeader
        title={t("nav.scheduling")}
        description={t("console.scheduling.description")}
        icon={Calendar}
      />

      <Wave1KpiBar metricKeys={[...SCHEDULING_KPI_KEYS]} labels={SCHEDULING_KPI_LABELS} />

      <FilterBar
        fields={FILTER_FIELDS}
        values={table.filters}
        onChange={table.setFilter}
        onReset={table.resetFilters}
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        isLoading={isLoading}
        getRowKey={(r) => String(r.id)}
        pagination={{ page: table.page, pageSize: table.pageSize, total: data?.total ?? 0 }}
        pageSizeOptions={[10, 20, 50]}
        onPageChange={table.setPage}
        onPageSizeChange={table.setPageSize}
        sort={table.sort}
        onSortChange={table.setSort}
        emptyTitle="No sections found"
      />

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Academic term and section setup</CardTitle>
          <CardDescription>Create the term and course section that enrollments use.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-5">
            <div className="space-y-1.5">
              <Label htmlFor="academic-term-code">Term code</Label>
              <Input
                id="academic-term-code"
                placeholder="2026-FALL"
                value={termCode}
                onChange={(event) => setTermCode(event.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="academic-term-name">Term name</Label>
              <Input
                id="academic-term-name"
                placeholder="Fall 2026"
                value={termName}
                onChange={(event) => setTermName(event.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="academic-term-start">Start date</Label>
              <Input
                id="academic-term-start"
                type="date"
                value={termStartDate}
                onChange={(event) => setTermStartDate(event.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="academic-term-end">End date</Label>
              <Input
                id="academic-term-end"
                type="date"
                value={termEndDate}
                onChange={(event) => setTermEndDate(event.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="academic-term-deadline">Drop deadline</Label>
              <Input
                id="academic-term-deadline"
                type="date"
                value={termAddDropDeadline}
                onChange={(event) => setTermAddDropDeadline(event.target.value)}
              />
            </div>
          </div>
          <Button
            disabled={!canCreateTerm || createTerm.isPending}
            onClick={() =>
              createTerm.mutate(
                {
                  term_code: termCode.trim(),
                  term_name: termName.trim(),
                  start_date: dateInputToIso(termStartDate),
                  end_date: dateInputToIso(termEndDate),
                  add_drop_deadline: dateInputToIso(termAddDropDeadline),
                  status: "active",
                  metadata_json: { source: "admin_scheduling_page" },
                },
                {
                  ...getHandlers({ successTitle: "Academic term created" }),
                  onSuccess: () => {
                    setTermCode("");
                    setTermName("");
                    setTermStartDate("");
                    setTermEndDate("");
                    setTermAddDropDeadline("");
                  },
                },
              )
            }
          >
            Create term
          </Button>

          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-5">
            <div className="space-y-1.5">
              <Label htmlFor="course-section-course">Course</Label>
              <select
                id="course-section-course"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={sectionCourseId}
                onChange={(event) => setSectionCourseId(event.target.value)}
                data-testid="course-section-course-select"
              >
                <option value="">Select course</option>
                {courses.map((course) => (
                  <option key={course.id} value={course.id}>
                    {formatCourseOption(course)}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="course-section-term">Term</Label>
              <select
                id="course-section-term"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={sectionTermId}
                onChange={(event) => setSectionTermId(event.target.value)}
                data-testid="course-section-term-select"
              >
                <option value="">Select term</option>
                {terms.map((term) => (
                  <option key={term.id} value={term.id}>
                    {formatTermOption(term)}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="course-section-code">Section code</Label>
              <Input
                id="course-section-code"
                placeholder="CS101-A"
                value={sectionCode}
                onChange={(event) => setSectionCode(event.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="course-section-capacity">Capacity</Label>
              <Input
                id="course-section-capacity"
                inputMode="numeric"
                value={sectionMaxCapacity}
                onChange={(event) => setSectionMaxCapacity(event.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="course-section-instructor">Instructor</Label>
              <Input
                id="course-section-instructor"
                placeholder="optional"
                value={sectionInstructorId}
                onChange={(event) => setSectionInstructorId(event.target.value)}
              />
            </div>
          </div>
          <Button
            disabled={!canCreateSection || createSection.isPending}
            onClick={() =>
              createSection.mutate(
                {
                  course_id: parsedSectionCourseId,
                  term_id: parsedSectionTermId,
                  section_code: sectionCode.trim(),
                  instructor_id: sectionInstructorId.trim() || null,
                  max_capacity: parsedSectionMaxCapacity,
                },
                {
                  ...getHandlers({ successTitle: "Course section created" }),
                  onSuccess: () => {
                    setSectionCode("");
                    setSectionInstructorId("");
                    setSectionMaxCapacity("30");
                  },
                },
              )
            }
          >
            Create section
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Attendance risk summary</CardTitle>
          <CardDescription>24h interventions snapshot for attendance and engagement operations.</CardDescription>
        </CardHeader>
        <CardContent>
          {riskSummaryError ? (
            <ErrorState title="Failed to load risk summary" onRetry={refetchRiskSummary} />
          ) : riskSummaryLoading || !riskSummary ? (
            <p className="text-sm text-muted-foreground">Loading risk summary...</p>
          ) : (
            <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6 text-sm">
              <div className="rounded-lg border bg-card p-3">
                <p className="text-xs text-muted-foreground">Open cases</p>
                <p className="text-lg font-semibold">{riskSummary.open_cases_total}</p>
              </div>
              <div className="rounded-lg border bg-card p-3">
                <p className="text-xs text-muted-foreground">Signals (24h)</p>
                <p className="text-lg font-semibold">{riskSummary.signals_last_24h}</p>
              </div>
              <div className="rounded-lg border bg-card p-3">
                <p className="text-xs text-muted-foreground">Auto cases (24h)</p>
                <p className="text-lg font-semibold">{riskSummary.auto_created_cases_last_24h}</p>
              </div>
              <div className="rounded-lg border bg-card p-3">
                <p className="text-xs text-muted-foreground">High severity</p>
                <p className="text-lg font-semibold">{highSeverityCount}</p>
              </div>
              <div className="rounded-lg border bg-card p-3">
                <p className="text-xs text-muted-foreground">Medium severity</p>
                <p className="text-lg font-semibold">{mediumSeverityCount}</p>
              </div>
              <div className="rounded-lg border bg-card p-3">
                <p className="text-xs text-muted-foreground">At-risk ratio (high+medium)</p>
                <p className="text-lg font-semibold">{atRiskRatioLabel}</p>
                <p className="text-xs text-muted-foreground">{atRiskCount}/{severityTotal} signals</p>
              </div>
              <div className="rounded-lg border bg-card p-3">
                <p className="text-xs text-muted-foreground">Low severity</p>
                <p className="text-lg font-semibold">{lowSeverityCount}</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {activeSectionId && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Attendance trends</CardTitle>
            <CardDescription>Historical attendance rate by lesson date.</CardDescription>
          </CardHeader>
          <CardContent>
            {trends.isLoading ? (
              <p className="text-sm text-muted-foreground">Loading trends...</p>
            ) : trends.error ? (
              <ErrorState title="Failed to load attendance trends" onRetry={trends.refetch} />
            ) : trends.data?.data_points && trends.data.data_points.length > 0 ? (
              <div className="space-y-3">
                <p className="text-xs text-muted-foreground">Attendance rate by lesson date (past lessons)</p>
                <div className="space-y-2">
                  {trends.data.data_points.slice(-10).map((point) => (
                    <div key={point.date} className="flex items-center gap-2">
                      <span className="w-24 text-xs text-muted-foreground">{new Date(point.date).toLocaleDateString()}</span>
                      <div className="flex-1 h-6 rounded bg-muted relative overflow-hidden">
                        <div
                          className="h-full bg-green-500 transition-all duration-300"
                          style={{ width: `${Math.max(point.attendance_rate * 100, 2)}%` }}
                        />
                      </div>
                      <span className="w-12 text-right text-xs font-medium">{(point.attendance_rate * 100).toFixed(0)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No attendance data available for this section.</p>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Lesson attendance</CardTitle>
          <CardDescription>Select section, pick lesson, and mark student status using scheduling APIs.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="section-instance-id">Section</Label>
            {sectionRows.length > 0 ? (
              <select
                id="section-instance-id"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={activeSectionId}
                onChange={(event) => {
                  setActiveSectionId(event.target.value);
                  setSectionInput(event.target.value);
                  setActiveLessonId("");
                  setStudentInput("");
                }}
                data-testid="lesson-section-select"
              >
                <option value="">Select section</option>
                {sectionRows.map((section) => (
                  <option key={section.id} value={section.id}>
                    {section.section_code ?? section.code ?? `Section #${section.id}`} / Course #{section.course_id ?? "-"} / Term #{section.term_id ?? "-"}
                  </option>
                ))}
              </select>
            ) : (
              <div className="flex gap-2">
                <Input
                  id="section-instance-id"
                  placeholder="Section ID"
                  value={sectionInput}
                  onChange={(event) => setSectionInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      setActiveSectionId(sectionInput.trim());
                      setActiveLessonId("");
                      setStudentInput("");
                    }
                  }}
                />
                <Button
                  onClick={() => {
                    setActiveSectionId(sectionInput.trim());
                    setActiveLessonId("");
                    setStudentInput("");
                  }}
                >
                  Load lessons
                </Button>
              </div>
            )}
          </div>

          {activeSectionId ? (
            lessonsError ? (
              <ErrorState title="Failed to load section lessons" onRetry={refetchLessons} />
            ) : (
              <div className="space-y-4">
                <div className="text-sm text-muted-foreground">
                  Section #{activeSectionId} · {lessonsLoading ? "loading..." : `lessons: ${lessons?.total ?? 0}`}
                </div>
                {canWriteAttendance ? (
                  <div className="grid gap-3 md:grid-cols-[180px_1fr_1fr_auto]">
                    <div className="space-y-1.5">
                      <Label htmlFor="lesson-scheduled-date">Lesson date</Label>
                      <Input
                        id="lesson-scheduled-date"
                        type="date"
                        value={lessonDate}
                        onChange={(event) => setLessonDate(event.target.value)}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="lesson-topic-title">Topic</Label>
                      <Input
                        id="lesson-topic-title"
                        placeholder="Lecture topic"
                        value={lessonTopic}
                        onChange={(event) => setLessonTopic(event.target.value)}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="lesson-notes">Notes</Label>
                      <Input
                        id="lesson-notes"
                        placeholder="optional"
                        value={lessonNotes}
                        onChange={(event) => setLessonNotes(event.target.value)}
                      />
                    </div>
                    <div className="flex items-end">
                      <Button
                        disabled={!canCreateLesson || createLesson.isPending}
                        onClick={() =>
                          createLesson.mutate(
                            {
                              scheduled_date: lessonDate,
                              topic_title: lessonTopic.trim(),
                              notes: lessonNotes.trim() || null,
                              metadata_json: { source: "admin_scheduling_page" },
                            },
                            {
                              ...getHandlers({ successTitle: "Lesson created" }),
                              onSuccess: (lesson) => {
                                setLessonDate("");
                                setLessonTopic("");
                                setLessonNotes("");
                                setActiveLessonId(String(lesson.id));
                              },
                            },
                          )
                        }
                      >
                        Create lesson
                      </Button>
                    </div>
                  </div>
                ) : null}
                <div className="overflow-x-auto rounded-md border">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left">
                        <th className="p-2 font-medium">Lesson</th>
                        <th className="p-2 font-medium">Scheduled date</th>
                        <th className="p-2 font-medium">Topic</th>
                        <th className="p-2 font-medium">Status</th>
                        <th className="p-2 font-medium">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(lessons?.items ?? []).length === 0 ? (
                        <tr>
                          <td className="p-2 text-muted-foreground" colSpan={5}>No lessons found for this section.</td>
                        </tr>
                      ) : (
                        (lessons?.items ?? []).map((lesson) => (
                          <tr className="border-b last:border-0" key={lesson.id}>
                            <td className="p-2">#{lesson.id}</td>
                            <td className="p-2">{lesson.scheduled_date}</td>
                            <td className="p-2">{lesson.topic_title}</td>
                            <td className="p-2"><StatusBadge status={lesson.status} /></td>
                            <td className="p-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  const selectedId = String(lesson.id);
                                  setActiveLessonId(selectedId);
                                }}
                              >
                                Use lesson
                              </Button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )
          ) : (
            <p className="text-sm text-muted-foreground">Select a section to load lesson instances.</p>
          )}

          <div className="space-y-2">
            <Label htmlFor="lesson-instance-id">Lesson</Label>
            <select
              id="lesson-instance-id"
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={activeLessonId}
              onChange={(event) => setActiveLessonId(event.target.value)}
              disabled={!activeSectionId || lessonRows.length === 0}
              data-testid="attendance-lesson-select"
            >
              <option value="">Select lesson</option>
              {lessonRows.map((lesson) => (
                <option key={lesson.id} value={lesson.id}>
                  #{lesson.id} / {lesson.scheduled_date} / {lesson.topic_title}
                </option>
              ))}
            </select>
          </div>

          {activeLessonId ? (
            attendanceError ? (
              <ErrorState title="Failed to load lesson attendance" onRetry={refetchAttendance} />
            ) : (
              <div className="space-y-3">
                <div className="text-sm text-muted-foreground">
                  Lesson #{activeLessonId} · {attendanceLoading ? "loading..." : `rows: ${attendance?.total ?? 0}`}
                </div>

                <div className="overflow-x-auto rounded-md border">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left">
                        <th className="p-2 font-medium">Student</th>
                        <th className="p-2 font-medium">Status</th>
                        <th className="p-2 font-medium">Attendance risk</th>
                        <th className="p-2 font-medium">Marked by</th>
                        <th className="p-2 font-medium">Risk timeline</th>
                      </tr>
                    </thead>
                    <tbody>
                      {attendanceRows.length === 0 ? (
                        <tr>
                          <td className="p-2 text-muted-foreground" colSpan={5}>No attendance rows found.</td>
                        </tr>
                      ) : (
                        attendanceRows.map((row) => (
                          <tr className="border-b last:border-0" key={row.id}>
                            <td className="p-2">#{row.student_profile_id}</td>
                            <td className="p-2"><StatusBadge status={row.attendance_status} /></td>
                            <td className="p-2"><StudentRiskBadge studentProfileId={row.student_profile_id} /></td>
                            <td className="p-2">{row.marked_by}</td>
                            <td className="p-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  setSelectedRiskStudentId(row.student_profile_id);
                                  setSelectedRiskHistoryPage(1);
                                  setSelectedRiskHistorySeverityFilter("all");
                                }}
                              >
                                History
                              </Button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                {selectedRiskStudentId ? (
                  <Card>
                    <CardHeader>
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <CardTitle className="text-sm">Student risk timeline</CardTitle>
                          <CardDescription>Latest attendance-risk signals for student #{selectedRiskStudentId}.</CardDescription>
                        </div>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            setSelectedRiskStudentId(null);
                            setSelectedRiskHistoryPage(1);
                            setSelectedRiskHistorySeverityFilter("all");
                          }}
                        >
                          Close timeline
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      {selectedStudentRiskHistoryError ? (
                        <ErrorState title="Failed to load student risk history" onRetry={refetchSelectedStudentRiskHistory} />
                      ) : selectedStudentRiskHistoryLoading || !selectedStudentRiskHistory ? (
                        <p className="text-sm text-muted-foreground">Loading student risk history...</p>
                      ) : selectedStudentRiskHistory.items.length === 0 ? (
                        <p className="text-sm text-muted-foreground">No risk history records found.</p>
                      ) : (
                        <div className="space-y-2">
                          <div className="flex flex-col gap-2 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
                            <div className="flex items-center gap-2">
                              <Label htmlFor="risk-history-severity-filter" className="text-xs">Filter severity</Label>
                              <select
                                id="risk-history-severity-filter"
                                className="h-8 rounded-md border bg-background px-2 text-xs"
                                value={selectedRiskHistorySeverityFilter}
                                onChange={(event) =>
                                  setSelectedRiskHistorySeverityFilter(event.target.value as "all" | "high" | "medium" | "low")
                                }
                              >
                                <option value="all">All</option>
                                <option value="high">High</option>
                                <option value="medium">Medium</option>
                                <option value="low">Low</option>
                              </select>
                              <Button
                                size="sm"
                                variant="outline"
                                disabled={selectedRiskHistorySeverityFilter === "all"}
                                onClick={() => setSelectedRiskHistorySeverityFilter("all")}
                              >
                                Reset filter
                              </Button>
                            </div>
                            <span>Active filter: {selectedRiskHistorySeverityFilter}</span>
                            <span>
                              Page severity mix: H {riskHistoryPageSeverityCounts.high} · M {riskHistoryPageSeverityCounts.medium} · L {riskHistoryPageSeverityCounts.low}
                            </span>
                            <span>Highest severity on page: {riskHistoryPageHighestSeverity}</span>
                            <span>Sorted by risk gap: descending</span>
                            <span>Showing {filteredRiskHistoryItems.length} of {selectedStudentRiskHistory.items.length} records on this page</span>
                          </div>
                          <div className="overflow-x-auto rounded-md border">
                            {filteredRiskHistoryItems.length === 0 ? (
                              <p className="p-3 text-sm text-muted-foreground">No records match the selected severity on this page.</p>
                            ) : (
                              <table className="w-full text-sm">
                                <thead>
                                  <tr className="border-b text-left">
                                    <th className="p-2 font-medium">Detected at</th>
                                    <th className="p-2 font-medium">Severity</th>
                                    <th className="p-2 font-medium">Current / threshold</th>
                                    <th className="p-2 font-medium">Risk gap</th>
                                    <th className="p-2 font-medium">Case ID</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {sortedRiskHistoryItems.map((item, index) => (
                                    <tr className="border-b last:border-0" key={`${item.detected_at}-${index}`}>
                                      <td className="p-2">{new Date(item.detected_at).toLocaleString()}</td>
                                      <td className="p-2"><StatusBadge status={item.severity} /></td>
                                      <td className="p-2">{item.current_value} / {item.threshold_value}</td>
                                      <td className="p-2">{item.current_value - item.threshold_value}</td>
                                      <td className="p-2">{item.associated_case_id ?? "—"}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            )}
                          </div>
                          <div className="flex items-center justify-between text-xs text-muted-foreground">
                            <span>
                              Page {selectedStudentRiskHistory.page} of {selectedRiskHistoryTotalPages} · total signals: {selectedStudentRiskHistory.total}
                            </span>
                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                variant="outline"
                                disabled={!canGoRiskHistoryPrev}
                                onClick={() => setSelectedRiskHistoryPage((page) => Math.max(1, page - 1))}
                              >
                                Previous
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                disabled={!canGoRiskHistoryNext}
                                onClick={() => setSelectedRiskHistoryPage((page) => page + 1)}
                              >
                                Next
                              </Button>
                            </div>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ) : null}

                {canWriteAttendance ? (
                  <div className="grid gap-2 sm:grid-cols-3">
                    <div className="space-y-1">
                      <Label htmlFor="attendance-student-id">Student profile ID</Label>
                      {enrolledStudentRows.length > 0 ? (
                        <select
                          id="attendance-student-id"
                          className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                          value={studentInput}
                          onChange={(event) => setStudentInput(event.target.value)}
                          data-testid="attendance-student-select"
                        >
                          <option value="">Select enrolled student</option>
                          {enrolledStudentRows.map((enrollment) => (
                            <option key={enrollment.id} value={enrollment.student_profile_id ?? enrollment.student_id ?? ""}>
                              {formatStudentOption(
                                studentById.get(String(enrollment.student_profile_id ?? enrollment.student_id ?? "")),
                                enrollment.student_profile_id ?? enrollment.student_id,
                                enrollment.id,
                              )}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <Input
                          id="attendance-student-id"
                          placeholder="e.g. 1001"
                          value={studentInput}
                          onChange={(event) => setStudentInput(event.target.value)}
                        />
                      )}
                    </div>
                    <div className="space-y-1">
                      <Label htmlFor="attendance-status">Attendance status</Label>
                      <select
                        id="attendance-status"
                        className="h-10 rounded-md border bg-background px-3 text-sm"
                        value={attendanceStatus}
                        onChange={(event) =>
                          setAttendanceStatus(event.target.value as "present" | "absent" | "late" | "excused")
                        }
                      >
                        <option value="present">Present</option>
                        <option value="absent">Absent</option>
                        <option value="late">Late</option>
                        <option value="excused">Excused</option>
                      </select>
                    </div>
                    <div className="flex items-end">
                      <Button
                        disabled={!canSubmitAttendance || upsertAttendance.isPending}
                        onClick={() => {
                          if (!canSubmitAttendance) return;
                          const feedback = getHandlers({
                            successTitle: "Attendance updated",
                            successDescription: "Student attendance status was saved.",
                            errorTitle: "Failed to update attendance",
                          });

                          upsertAttendance.mutate(
                            {
                              student_profile_id: parsedStudentId,
                              attendance_status: attendanceStatus,
                            },
                            {
                              onSuccess: () => {
                                feedback.onSuccess(undefined);
                                void refetchAttendance();
                              },
                              onError: feedback.onError,
                            },
                          );
                        }}
                      >
                        {upsertAttendance.isPending ? "Saving..." : "Save attendance"}
                      </Button>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Scheduling write permission is required to mark attendance.</p>
                )}
              </div>
            )
          ) : (
            <p className="text-sm text-muted-foreground">Enter a lesson instance ID to work with attendance rows.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
