"use client";

import { useState } from "react";
import { PageHeader } from "@/shared/ui/page-header";
import { DataTable, Column } from "@/shared/ui/data-table";
import { FilterBar } from "@/shared/ui/filter-bar";
import { StatusBadge } from "@/shared/ui/status-badge";
import { useEnrollments, useDropEnrollment, useCreateEnrollment } from "@/modules/enrollments/hooks";
import { Enrollment } from "@/modules/enrollments/types";
import { useStudents } from "@/modules/students/hooks";
import { useCourses } from "@/modules/courses/hooks";
import { useSections } from "@/modules/scheduling/hooks";
import { CourseSection } from "@/modules/scheduling/types";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { ConfirmActionDialog } from "@/shared/ui/confirm-action-dialog";
import { DrawerPanel } from "@/shared/ui/drawer-panel";
import { DetailList } from "@/shared/ui/detail-list";
import { ErrorState } from "@/shared/ui/error-state";
import { PermissionGate, RequirePermission } from "@/shared/ui/permission-gate";
import { useDetailDrawer } from "@/shared/hooks/use-detail-drawer";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useTableQueryState } from "@/shared/hooks/use-table-query-state";
import { formatDate } from "@/shared/utils/format";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useLanguage } from "@/app/components/LanguageProvider";
import { BookOpen, Plus } from "lucide-react";

const FILTER_FIELDS = [
  {
    key: "status",
    label: "Status",
    type: "select" as const,
    options: [
      { label: "Enrolled", value: "enrolled" },
      { label: "Dropped", value: "dropped" },
      { label: "Completed", value: "completed" },
      { label: "Waitlisted", value: "waitlisted" },
    ],
  },
];

function formatSectionLabel(section: CourseSection, courseLabel?: string) {
  const sectionCode = section.section_code ?? section.code ?? `Section #${section.id}`;
  const course = courseLabel ?? (section.course_id ? `Course #${section.course_id}` : "Course -");
  const term = section.term_id ? `Term #${section.term_id}` : section.semester ?? "Term -";
  return `${sectionCode} / ${course} / ${term}`;
}

export default function EnrollmentsPage() {
  const { t } = useLanguage();
  const [createOpen, setCreateOpen] = useState(false);
  const [studentProfileId, setStudentProfileId] = useState("");
  const [courseId, setCourseId] = useState("");
  const [termId, setTermId] = useState("");
  const [sectionId, setSectionId] = useState("");
  const table = useTableQueryState({ filterKeys: ["status"] as const, defaultPageSize: 20, defaultSort: { key: "enrolled", direction: "desc" } });
  const detail = useDetailDrawer({ paramKey: "enrollment" });
  const { getHandlers } = useMutationFeedback();

  const { data, isLoading, error, refetch } = useEnrollments({ page: table.page, page_size: table.pageSize, status: table.filters.status });
  const studentsQuery = useStudents({ page: 1, page_size: 100 });
  const coursesQuery = useCourses();
  const sectionsQuery = useSections({ page: 1, page_size: 100 });
  const createEnrollment = useCreateEnrollment();
  const drop = useDropEnrollment();
  const selectedEnrollment = data?.items.find((item) => String(item.id) === detail.selectedId) ?? null;
  const students = studentsQuery.data?.items ?? [];
  const courses = coursesQuery.data?.courses ?? [];
  const sections = sectionsQuery.data?.items ?? [];
  const selectableSections = sections.filter((section) => section.status !== "cancelled");
  const courseById = new Map(courses.map((course) => [Number(course.id), course]));
  const parsedStudentProfileId = Number(studentProfileId);
  const parsedCourseId = Number(courseId);
  const parsedTermId = Number(termId);
  const parsedSectionId = Number(sectionId);
  const canCreate =
    Number.isInteger(parsedStudentProfileId) &&
    parsedStudentProfileId > 0 &&
    Number.isInteger(parsedCourseId) &&
    parsedCourseId > 0 &&
    Number.isInteger(parsedTermId) &&
    parsedTermId > 0 &&
    Number.isInteger(parsedSectionId) &&
    parsedSectionId > 0;

  if (error) {
    return <ErrorState title="Failed to load enrollments" onRetry={refetch} />;
  }

  const columns: Column<Enrollment>[] = [
    {
      key: "student",
      header: "Student",
      cell: (r) => r.student_name ?? `Student #${r.student_profile_id ?? r.student_id ?? "-"}`,
      sortValue: (r) => String(r.student_name ?? r.student_profile_id ?? r.student_id ?? "").toLowerCase(),
    },
    {
      key: "section",
      header: "Section",
      cell: (r) => <code className="text-xs">{r.section_code ?? `#${r.section_id ?? "-"}`}</code>,
      sortValue: (r) => String(r.section_code ?? r.section_id ?? ""),
    },
    {
      key: "course",
      header: "Course",
      cell: (r) => {
        const course = courseById.get(Number(r.course_id ?? 0));
        return r.course_name ?? (course ? `${course.course_code} - ${course.title}` : `Course #${r.course_id ?? "-"}`);
      },
      sortValue: (r) => String(r.course_name ?? r.course_id ?? "").toLowerCase(),
    },
    {
      key: "status",
      header: "Status",
      cell: (r) => <StatusBadge status={r.status ?? r.enrollment_status ?? "enrolled"} />,
      sortValue: (r) => r.status ?? r.enrollment_status ?? "",
    },
    { key: "enrolled", header: "Enrolled", cell: (r) => formatDate(r.enrolled_at), sortValue: (r) => r.enrolled_at },
    {
      key: "actions",
      header: "",
      width: "80px",
      cell: (r) =>
        (r.status ?? r.enrollment_status) === "enrolled" ? (
          <PermissionGate permission={PERMISSIONS.ENROLLMENTS_WRITE}>
            <ConfirmActionDialog
              title="Drop enrollment?"
              description={`${r.student_name ?? `Student #${r.student_profile_id ?? r.student_id ?? "-"}`} will be dropped from ${r.section_code ?? `section #${r.section_id ?? "-"}`}.`}
              variant="destructive"
              onConfirm={() =>
                r.version
                  ? drop.mutate(
                    {
                      id: r.id,
                      payload: {
                        expected_version: r.version,
                        reason: "Dropped from tenant admin console.",
                        metadata_json: { source: "admin_enrollments_page" },
                      },
                    },
                    {
                      ...getHandlers({ successTitle: "Enrollment dropped" }),
                    },
                  )
                  : undefined
              }
              trigger={
                <Button variant="ghost" size="sm" disabled={drop.isPending || !r.version}>
                  Drop
                </Button>
              }
            />
          </PermissionGate>
        ) : null,
    },
  ];

  return (
    <RequirePermission permission={PERMISSIONS.ENROLLMENTS_READ}>
    <div className="space-y-4">
      <PageHeader
        title={t("nav.enrollments")}
        description={t("console.enrollments.description")}
        icon={BookOpen}
        actions={
          <PermissionGate permission={PERMISSIONS.ENROLLMENTS_WRITE}>
            <Button size="sm" onClick={() => setCreateOpen(true)}>
              <Plus className="h-4 w-4 mr-1" />
              Enroll student
            </Button>
          </PermissionGate>
        }
      />

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
        emptyTitle="No enrollments found"
      />

      <DrawerPanel
        open={detail.isOpen}
        onClose={detail.close}
        title={selectedEnrollment?.student_name ?? (selectedEnrollment ? `Student #${selectedEnrollment.student_profile_id ?? selectedEnrollment.student_id ?? "-"}` : "Enrollment summary")}
        description={selectedEnrollment?.section_code ?? (selectedEnrollment ? `Section #${selectedEnrollment.section_id ?? "-"}` : "Select an enrollment from the table.")}
      >
        {selectedEnrollment ? (
          <DetailList
            items={[
              { label: "Course", value: selectedEnrollment.course_name ?? `Course #${selectedEnrollment.course_id ?? "-"}` },
              { label: "Status", value: <StatusBadge status={selectedEnrollment.status ?? selectedEnrollment.enrollment_status ?? "enrolled"} /> },
              { label: "Student ID", value: selectedEnrollment.student_profile_id ?? selectedEnrollment.student_id ?? "-" },
              { label: "Section ID", value: selectedEnrollment.section_id },
              { label: "Term ID", value: selectedEnrollment.term_id ?? "-" },
              { label: "Version", value: selectedEnrollment.version ?? "-" },
              { label: "University", value: selectedEnrollment.tenant_id },
              { label: "Enrolled", value: formatDate(selectedEnrollment.enrolled_at) },
            ]}
          />
        ) : (
          <ErrorState title="Enrollment not found" message="The selected enrollment is not present on this page of results." />
        )}
      </DrawerPanel>

      <DrawerPanel
        open={createOpen}
        onClose={() => {
          setCreateOpen(false);
          setStudentProfileId("");
          setCourseId("");
          setTermId("");
          setSectionId("");
        }}
        title="Enroll student"
        description="Create a new enrollment by student, course, term and section."
      >
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="enrollment-student-id">Student ID</Label>
            {students.length > 0 ? (
              <select
                id="enrollment-student-id"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={studentProfileId}
                onChange={(event) => setStudentProfileId(event.target.value)}
                data-testid="enrollment-student-select"
              >
                <option value="">Select student</option>
                {students.map((student) => (
                  <option key={student.id} value={student.id}>
                    {student.student_number} / {student.first_name} {student.last_name} (#{student.id})
                  </option>
                ))}
              </select>
            ) : (
              <Input
                id="enrollment-student-id"
                value={studentProfileId}
                onChange={(event) => setStudentProfileId(event.target.value)}
                placeholder="1"
              />
            )}
          </div>
          {selectableSections.length > 0 ? (
            <div className="space-y-1.5">
              <Label htmlFor="enrollment-section-id">Section</Label>
              <select
                id="enrollment-section-id"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={sectionId}
                onChange={(event) => {
                  const nextSectionId = event.target.value;
                  const section = selectableSections.find((item) => String(item.id) === nextSectionId);
                  setSectionId(nextSectionId);
                  setCourseId(section?.course_id ? String(section.course_id) : "");
                  setTermId(section?.term_id ? String(section.term_id) : "");
                }}
                data-testid="enrollment-section-select"
              >
                <option value="">Select section</option>
                {selectableSections.map((section) => {
                  const course = section.course_id ? courseById.get(Number(section.course_id)) : undefined;
                  const courseLabel = course ? `${course.course_code} - ${course.title}` : undefined;
                  return (
                    <option key={section.id} value={section.id}>
                      {formatSectionLabel(section, courseLabel)}
                    </option>
                  );
                })}
              </select>
            </div>
          ) : (
            <>
              <div className="space-y-1.5">
                <Label htmlFor="enrollment-course-id">Course ID</Label>
                {courses.length > 0 ? (
                  <select
                    id="enrollment-course-id"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={courseId}
                    onChange={(event) => setCourseId(event.target.value)}
                    data-testid="enrollment-course-select"
                  >
                    <option value="">Select course</option>
                    {courses.map((course) => (
                      <option key={course.id} value={course.id}>
                        {course.course_code} - {course.title} (#{course.id})
                      </option>
                    ))}
                  </select>
                ) : (
                  <Input
                    id="enrollment-course-id"
                    value={courseId}
                    onChange={(event) => setCourseId(event.target.value)}
                    placeholder="1"
                  />
                )}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="enrollment-term-id">Term ID</Label>
                <Input
                  id="enrollment-term-id"
                  value={termId}
                  onChange={(event) => setTermId(event.target.value)}
                  placeholder="1"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="enrollment-section-id">Section ID</Label>
                <Input
                  id="enrollment-section-id"
                  value={sectionId}
                  onChange={(event) => setSectionId(event.target.value)}
                  placeholder="1"
                />
              </div>
            </>
          )}
          <PermissionGate permission={PERMISSIONS.ENROLLMENTS_WRITE}>
            <Button
              disabled={!canCreate || createEnrollment.isPending}
              onClick={() =>
                createEnrollment.mutate(
                  {
                    student_profile_id: parsedStudentProfileId,
                    course_id: parsedCourseId,
                    term_id: parsedTermId,
                    section_id: parsedSectionId,
                  },
                  {
                    ...getHandlers({ successTitle: "Enrollment created" }),
                    onSuccess: () => {
                      setCreateOpen(false);
                      setStudentProfileId("");
                      setCourseId("");
                      setTermId("");
                      setSectionId("");
                    },
                  },
                )
              }
            >
              Create enrollment
            </Button>
          </PermissionGate>
        </div>
      </DrawerPanel>
    </div>
    </RequirePermission>
  );
}
