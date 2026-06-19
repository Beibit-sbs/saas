"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/shared/ui/page-header";
import { DataTable, Column } from "@/shared/ui/data-table";
import { FilterBar } from "@/shared/ui/filter-bar";
import { ErrorState } from "@/shared/ui/error-state";
import { Button } from "@/shared/ui/button";
import { DrawerPanel } from "@/shared/ui/drawer-panel";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { PermissionGate, RequirePermission } from "@/shared/ui/permission-gate";
import { useDetailDrawer } from "@/shared/hooks/use-detail-drawer";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useTableQueryState } from "@/shared/hooks/use-table-query-state";
import { useCreateGradingScale, useGrades, useGradingScales, useUpsertGrade } from "@/modules/grades/hooks";
import type { CreateGradingScaleItemPayload, Grade, GradingScale } from "@/modules/grades/types";
import { useEnrollments } from "@/modules/enrollments/hooks";
import type { Enrollment } from "@/modules/enrollments/types";
import { useStudents } from "@/modules/students/hooks";
import type { Student } from "@/modules/students/types";
import { formatDate } from "@/shared/utils/format";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useLanguage } from "@/app/components/LanguageProvider";
import { BarChart2 } from "lucide-react";
import { Wave1KpiBar } from "@/modules/platform/kpi/wave1-kpi-bar";

const GRADES_KPI_KEYS = [
  "grade_decline_risk_count",
  "grade_intervention_cases_count",
] as const;

const GRADES_KPI_LABELS: Record<string, string> = {
  grade_decline_risk_count: "Grade Decline Risk",
  grade_intervention_cases_count: "Intervention Cases",
};

const FILTER_FIELDS = [
  { key: "student_id", label: "Student ID", type: "text" as const, placeholder: "Student ID…" },
  { key: "course_id", label: "Course ID", type: "text" as const, placeholder: "Course ID…" },
  { key: "term_id", label: "Term ID", type: "text" as const, placeholder: "Term ID…" },
  { key: "section_id", label: "Section ID", type: "text" as const, placeholder: "Section ID…" },
];

const DEFAULT_SCALE_ITEMS: CreateGradingScaleItemPayload[] = [
  { grade_code: "A", grade_points: 4, min_percentage: 90, max_percentage: 100 },
  { grade_code: "B", grade_points: 3, min_percentage: 80, max_percentage: 89 },
  { grade_code: "C", grade_points: 2, min_percentage: 70, max_percentage: 79 },
  { grade_code: "D", grade_points: 1, min_percentage: 60, max_percentage: 69 },
  { grade_code: "F", grade_points: 0, min_percentage: 0, max_percentage: 59 },
];

function gradeCode(grade: Grade): string {
  return grade.grade_code ?? grade.grade_value ?? "";
}

function gradePoints(grade: Grade): number | null {
  const value = grade.grade_points ?? grade.numeric_value;
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function gradeDate(grade: Grade): string | null {
  return grade.submitted_at ?? grade.graded_at ?? null;
}

function formatStudentLabel(student: Student | undefined, fallbackId: string | number | undefined): string {
  if (student) {
    return `${student.student_number} / ${student.first_name} ${student.last_name}`;
  }
  return fallbackId ? `Student #${fallbackId}` : "Student";
}

function formatEnrollmentOption(enrollment: Enrollment, student: Student | undefined): string {
  return [
    formatStudentLabel(student, enrollment.student_profile_id ?? enrollment.student_id),
    `Course #${enrollment.course_id ?? "-"}`,
    `Term #${enrollment.term_id ?? "-"}`,
    `Section #${enrollment.section_id ?? "-"}`,
    `Enrollment #${enrollment.id}`,
  ].join(" / ");
}

function formatScaleOption(scale: GradingScale): string {
  const codes = scale.items.map((item) => item.grade_code).join("/");
  return `${scale.name} (#${scale.id})${codes ? ` / ${codes}` : ""}`;
}

export default function GradesPage() {
  const { t } = useLanguage();
  const table = useTableQueryState({ filterKeys: ["student_id", "course_id", "term_id", "section_id"] as const, defaultPageSize: 20, defaultSort: { key: "graded", direction: "desc" } });
  const detail = useDetailDrawer({ paramKey: "grade" });
  const { getHandlers } = useMutationFeedback();
  const [createOpen, setCreateOpen] = useState(false);
  const [scaleOpen, setScaleOpen] = useState(false);
  const [newEnrollmentId, setNewEnrollmentId] = useState("");
  const [newGradingScaleId, setNewGradingScaleId] = useState("1");
  const [newGradeValue, setNewGradeValue] = useState("");
  const [newNumericValue, setNewNumericValue] = useState("");
  const [gradingScaleId, setGradingScaleId] = useState("1");
  const [gradeValue, setGradeValue] = useState("");
  const [numericValue, setNumericValue] = useState("");
  const [scaleName, setScaleName] = useState("Standard 4.0");
  const [scaleDescription, setScaleDescription] = useState("Default A-F grading scale");
  const [scaleItems, setScaleItems] = useState<CreateGradingScaleItemPayload[]>(DEFAULT_SCALE_ITEMS);

  const { data, isLoading, error, refetch } = useGrades({
    page: table.page,
    page_size: table.pageSize,
    student_id: table.filters.student_id,
    course_id: table.filters.course_id,
    term_id: table.filters.term_id,
    section_id: table.filters.section_id,
  });
  const enrollmentOptionsQuery = useEnrollments({ page: 1, page_size: 200, status: "enrolled" });
  const studentsQuery = useStudents({ page: 1, page_size: 200, status: "active" });
  const gradingScalesQuery = useGradingScales({ page: 1, page_size: 100, active_only: true });
  const upsertGrade = useUpsertGrade();
  const createScale = useCreateGradingScale();
  const selectedGrade = data?.items.find((item) => String(item.id) === String(detail.selectedId)) ?? null;
  const enrollmentOptions = enrollmentOptionsQuery.data?.items ?? [];
  const students = studentsQuery.data?.items ?? [];
  const gradingScales = gradingScalesQuery.data?.items ?? [];
  const enrollmentById = new Map(enrollmentOptions.map((enrollment) => [String(enrollment.id), enrollment]));
  const studentById = new Map(students.map((student) => [String(student.id), student]));
  const canCreateGrade = newEnrollmentId.trim().length > 0 && newGradingScaleId.trim().length > 0 && newGradeValue.trim().length > 0;
  const canCreateScale =
    scaleName.trim().length > 0 &&
    scaleItems.every((item) => item.grade_code.trim().length > 0 && Number.isFinite(item.grade_points) && Number.isFinite(item.min_percentage) && Number.isFinite(item.max_percentage));

  useEffect(() => {
    setGradeValue(selectedGrade ? gradeCode(selectedGrade) : "");
    setNumericValue(selectedGrade ? gradePoints(selectedGrade)?.toString() ?? "" : "");
    setGradingScaleId(selectedGrade?.grading_scale_id ? String(selectedGrade.grading_scale_id) : "1");
  }, [selectedGrade]);

  useEffect(() => {
    if (gradingScales.length === 0) return;
    const firstScaleId = String(gradingScales[0].id);
    if (!gradingScales.some((scale) => String(scale.id) === newGradingScaleId)) {
      setNewGradingScaleId(firstScaleId);
    }
    if (!selectedGrade && !gradingScales.some((scale) => String(scale.id) === gradingScaleId)) {
      setGradingScaleId(firstScaleId);
    }
  }, [gradingScales, gradingScaleId, newGradingScaleId, selectedGrade]);

  if (error) {
    return <ErrorState title="Failed to load grades" onRetry={refetch} />;
  }

  const columns: Column<Grade>[] = [
    {
      key: "student",
      header: "Student",
      cell: (r) => {
        const enrollment = enrollmentById.get(String(r.enrollment_id));
        return r.student_name ?? formatStudentLabel(studentById.get(String(enrollment?.student_profile_id)), enrollment?.student_profile_id ?? r.student_id);
      },
      sortValue: (r) => r.student_name ?? String(r.enrollment_id),
    },
    {
      key: "section",
      header: "Section",
      cell: (r) => {
        const enrollment = enrollmentById.get(String(r.enrollment_id));
        return <code className="text-xs">{r.section_code ?? `#${enrollment?.section_id ?? "-"}`}</code>;
      },
      sortValue: (r) => r.section_code ?? String(enrollmentById.get(String(r.enrollment_id))?.section_id ?? ""),
    },
    {
      key: "course",
      header: "Course",
      cell: (r) => r.course_name ?? `Course #${enrollmentById.get(String(r.enrollment_id))?.course_id ?? "-"}`,
      sortValue: (r) => r.course_name ?? String(enrollmentById.get(String(r.enrollment_id))?.course_id ?? ""),
    },
    { key: "grade", header: "Grade", cell: (r) => <span className="font-semibold">{gradeCode(r) || "—"}</span>, sortValue: (r) => gradeCode(r) },
    { key: "numeric", header: "Score", cell: (r) => gradePoints(r)?.toFixed(1) ?? "—", sortValue: (r) => gradePoints(r) ?? -1 },
    { key: "graded", header: "Graded", cell: (r) => (gradeDate(r) ? formatDate(gradeDate(r) as string) : "—"), sortValue: (r) => gradeDate(r) ?? "" },
    {
      key: "actions",
      header: "",
      width: "90px",
      cell: (r) => (
        <PermissionGate permission={PERMISSIONS.GRADES_WRITE}>
          <Button
            variant="ghost"
            size="sm"
            onClick={(event) => {
              event.stopPropagation();
              detail.open(String(r.id));
            }}
          >
            Edit
          </Button>
        </PermissionGate>
      ),
    },
  ];

  return (
    <RequirePermission permission={PERMISSIONS.GRADES_READ}>
    <div className="space-y-4">
      <PageHeader
        title={t("nav.grades")}
        description={t("console.grades.description")}
        icon={BarChart2}
        actions={
          <PermissionGate permission={PERMISSIONS.GRADES_WRITE}>
            <div className="flex flex-wrap gap-2">
              <Button size="sm" variant="outline" onClick={() => setScaleOpen(true)}>
                Add scale
              </Button>
              <Button size="sm" onClick={() => setCreateOpen(true)}>
                Add grade
              </Button>
            </div>
          </PermissionGate>
        }
      />

      <Wave1KpiBar metricKeys={[...GRADES_KPI_KEYS]} labels={GRADES_KPI_LABELS} />

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
        onRowClick={(row) => detail.open(String(row.id))}
        emptyTitle="No grades found"
      />

      <DrawerPanel
        open={detail.isOpen}
        onClose={detail.close}
        title={selectedGrade ? `Update enrollment #${selectedGrade.enrollment_id}` : "Update grade"}
        description={selectedGrade ? `Current version ${selectedGrade.version ?? "-"}` : "Select a grade row to update."}
      >
        {selectedGrade ? (
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="grade-scale-id">Grading scale ID</Label>
              {gradingScales.length > 0 ? (
                <select
                  id="grade-scale-id"
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={gradingScaleId}
                  onChange={(event) => setGradingScaleId(event.target.value)}
                  data-testid="grade-update-scale-select"
                >
                  {gradingScales.map((scale) => (
                    <option key={scale.id} value={scale.id}>
                      {formatScaleOption(scale)}
                    </option>
                  ))}
                </select>
              ) : (
                <Input id="grade-scale-id" value={gradingScaleId} onChange={(event) => setGradingScaleId(event.target.value)} placeholder="1" />
              )}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="grade-value">Letter grade</Label>
              <Input id="grade-value" value={gradeValue} onChange={(event) => setGradeValue(event.target.value)} placeholder="A" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="numeric-value">Numeric score</Label>
              <Input id="numeric-value" value={numericValue} onChange={(event) => setNumericValue(event.target.value)} placeholder="4.0" />
            </div>
            <PermissionGate permission={PERMISSIONS.GRADES_WRITE}>
              <Button
                disabled={!gradeValue.trim() || !gradingScaleId.trim() || !selectedGrade.version || upsertGrade.isPending}
                onClick={() =>
                  upsertGrade.mutate(
                    {
                      enrollment_id: selectedGrade.enrollment_id,
                      grading_scale_id: gradingScaleId.trim(),
                      grade_value: gradeValue.trim(),
                      numeric_value: numericValue.trim() ? Number(numericValue) : undefined,
                      expected_version: selectedGrade.version,
                    },
                    {
                      ...getHandlers({ successTitle: "Grade updated" }),
                      onSuccess: (savedGrade) => {
                        getHandlers<Grade>({ successTitle: "Grade updated" }).onSuccess(savedGrade);
                        detail.close();
                      },
                    },
                  )
                }
              >
                Save grade
              </Button>
            </PermissionGate>
          </div>
        ) : (
          <ErrorState title="Grade not found" message="The selected grade is not present on this page of results." />
        )}
      </DrawerPanel>

      <DrawerPanel
        open={createOpen}
        onClose={() => {
          setCreateOpen(false);
          setNewEnrollmentId("");
          setNewGradingScaleId("1");
          setNewGradeValue("");
          setNewNumericValue("");
        }}
        title="Add grade"
        description="Submit a grade for an enrolled student."
      >
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="new-grade-enrollment-id">Enrollment ID</Label>
            {enrollmentOptions.length > 0 ? (
              <select
                id="new-grade-enrollment-id"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={newEnrollmentId}
                onChange={(event) => setNewEnrollmentId(event.target.value)}
                data-testid="grade-enrollment-select"
              >
                <option value="">Select enrollment</option>
                {enrollmentOptions.map((enrollment) => (
                  <option key={enrollment.id} value={enrollment.id}>
                    {formatEnrollmentOption(enrollment, studentById.get(String(enrollment.student_profile_id)))}
                  </option>
                ))}
              </select>
            ) : (
              <Input
                id="new-grade-enrollment-id"
                value={newEnrollmentId}
                onChange={(event) => setNewEnrollmentId(event.target.value)}
                placeholder="1"
              />
            )}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="new-grade-scale-id">Grading scale ID</Label>
            {gradingScales.length > 0 ? (
              <select
                id="new-grade-scale-id"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={newGradingScaleId}
                onChange={(event) => setNewGradingScaleId(event.target.value)}
                data-testid="grade-scale-select"
              >
                {gradingScales.map((scale) => (
                  <option key={scale.id} value={scale.id}>
                    {formatScaleOption(scale)}
                  </option>
                ))}
              </select>
            ) : (
              <Input
                id="new-grade-scale-id"
                value={newGradingScaleId}
                onChange={(event) => setNewGradingScaleId(event.target.value)}
                placeholder="1"
              />
            )}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="new-grade-value">Letter grade</Label>
            <Input
              id="new-grade-value"
              value={newGradeValue}
              onChange={(event) => setNewGradeValue(event.target.value)}
              placeholder="A"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="new-numeric-value">Numeric score</Label>
            <Input
              id="new-numeric-value"
              value={newNumericValue}
              onChange={(event) => setNewNumericValue(event.target.value)}
              placeholder="4.0"
            />
          </div>
          <PermissionGate permission={PERMISSIONS.GRADES_WRITE}>
            <Button
              disabled={!canCreateGrade || upsertGrade.isPending}
              onClick={() =>
                upsertGrade.mutate(
                  {
                    enrollment_id: newEnrollmentId.trim(),
                    grading_scale_id: newGradingScaleId.trim(),
                    grade_value: newGradeValue.trim(),
                    numeric_value: newNumericValue.trim() ? Number(newNumericValue) : undefined,
                  },
                  {
                    ...getHandlers({ successTitle: "Grade saved" }),
                    onSuccess: () => {
                      setCreateOpen(false);
                      setNewEnrollmentId("");
                      setNewGradingScaleId("1");
                      setNewGradeValue("");
                      setNewNumericValue("");
                    },
                  },
                )
              }
            >
              Save grade
            </Button>
          </PermissionGate>
        </div>
      </DrawerPanel>

      <DrawerPanel
        open={scaleOpen}
        onClose={() => {
          setScaleOpen(false);
          setScaleName("Standard 4.0");
          setScaleDescription("Default A-F grading scale");
          setScaleItems(DEFAULT_SCALE_ITEMS);
        }}
        title="Add grading scale"
        description="Create a tenant grading scale."
      >
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="scale-name">Name</Label>
            <Input id="scale-name" value={scaleName} onChange={(event) => setScaleName(event.target.value)} placeholder="Standard 4.0" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="scale-description">Description</Label>
            <Input id="scale-description" value={scaleDescription} onChange={(event) => setScaleDescription(event.target.value)} placeholder="Default A-F grading scale" />
          </div>
          <div className="space-y-2">
            {scaleItems.map((item, index) => (
              <div key={index} className="grid grid-cols-4 gap-2">
                <Input
                  aria-label={`Grade code ${index + 1}`}
                  value={item.grade_code}
                  onChange={(event) =>
                    setScaleItems((current) =>
                      current.map((row, rowIndex) => rowIndex === index ? { ...row, grade_code: event.target.value.toUpperCase() } : row),
                    )
                  }
                  placeholder="A"
                />
                <Input
                  aria-label={`Grade points ${index + 1}`}
                  value={item.grade_points.toString()}
                  onChange={(event) =>
                    setScaleItems((current) =>
                      current.map((row, rowIndex) => rowIndex === index ? { ...row, grade_points: Number(event.target.value) } : row),
                    )
                  }
                  placeholder="4"
                />
                <Input
                  aria-label={`Minimum percentage ${index + 1}`}
                  value={item.min_percentage.toString()}
                  onChange={(event) =>
                    setScaleItems((current) =>
                      current.map((row, rowIndex) => rowIndex === index ? { ...row, min_percentage: Number(event.target.value) } : row),
                    )
                  }
                  placeholder="90"
                />
                <Input
                  aria-label={`Maximum percentage ${index + 1}`}
                  value={item.max_percentage.toString()}
                  onChange={(event) =>
                    setScaleItems((current) =>
                      current.map((row, rowIndex) => rowIndex === index ? { ...row, max_percentage: Number(event.target.value) } : row),
                    )
                  }
                  placeholder="100"
                />
              </div>
            ))}
          </div>
          <PermissionGate permission={PERMISSIONS.GRADES_WRITE}>
            <Button
              disabled={!canCreateScale || createScale.isPending}
              onClick={() =>
                createScale.mutate(
                  {
                    name: scaleName.trim(),
                    description: scaleDescription.trim() || null,
                    is_active: true,
                    items: scaleItems.map((item) => ({
                      grade_code: item.grade_code.trim().toUpperCase(),
                      grade_points: Number(item.grade_points),
                      min_percentage: Number(item.min_percentage),
                      max_percentage: Number(item.max_percentage),
                    })),
                  },
                  {
                    ...getHandlers({ successTitle: "Grading scale created" }),
                    onSuccess: (scale) => {
                      setNewGradingScaleId(String(scale.id));
                      setGradingScaleId(String(scale.id));
                      setScaleOpen(false);
                      setScaleName("Standard 4.0");
                      setScaleDescription("Default A-F grading scale");
                      setScaleItems(DEFAULT_SCALE_ITEMS);
                    },
                  },
                )
              }
            >
              Save scale
            </Button>
          </PermissionGate>
        </div>
      </DrawerPanel>
    </div>
    </RequirePermission>
  );
}
