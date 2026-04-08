"use client";

import { useMemo, useState } from "react";
import { BookOpen } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { DataTable, type Column } from "@/shared/ui/data-table";
import { DrawerPanel } from "@/shared/ui/drawer-panel";
import { ErrorState } from "@/shared/ui/error-state";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { PageHeader } from "@/shared/ui/page-header";
import { PermissionGate, RequirePermission } from "@/shared/ui/permission-gate";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useLanguage } from "@/app/components/LanguageProvider";
import { PERMISSIONS } from "@/shared/config/permissions";
import {
  useCourses,
  useCreateCourse,
  useUpdateCourse,
  useDeleteCourse,
} from "@/modules/courses/hooks";
import type { Course } from "@/modules/courses/types";

interface CourseFormState {
  course_code: string;
  title: string;
  credits: string;
  program_id: string;
  status: string;
}

const EMPTY_FORM: CourseFormState = {
  course_code: "",
  title: "",
  credits: "3",
  program_id: "",
  status: "active",
};

export default function CoursesPage() {
  const { t } = useLanguage();
  const tAny = (key: string) => t(key as never);
  const { getHandlers } = useMutationFeedback();

  const [createOpen, setCreateOpen] = useState(false);
  const [editCourse, setEditCourse] = useState<Course | null>(null);
  const [form, setForm] = useState<CourseFormState>(EMPTY_FORM);

  const { data, isLoading, error, refetch } = useCourses();
  const createCourse = useCreateCourse();
  const updateCourse = useUpdateCourse(editCourse?.id ?? null);
  const deleteCourse = useDeleteCourse();

  const isSubmitting =
    createCourse.isPending || updateCourse.isPending || deleteCourse.isPending;

  const parsedCredits = Number.parseInt(form.credits, 10);
  const parsedProgramId = Number.parseInt(form.program_id, 10);

  const isFormValid = useMemo(
    () =>
      form.course_code.trim().length > 0 &&
      form.title.trim().length > 0 &&
      Number.isFinite(parsedCredits) &&
      parsedCredits >= 0 &&
      Number.isFinite(parsedProgramId) &&
      parsedProgramId > 0 &&
      form.status.trim().length > 0,
    [form, parsedCredits, parsedProgramId],
  );

  function resetForm() {
    setForm(EMPTY_FORM);
    setEditCourse(null);
  }

  function openCreate() {
    resetForm();
    setCreateOpen(true);
  }

  function openEdit(course: Course) {
    setEditCourse(course);
    setForm({
      course_code: course.course_code,
      title: course.title,
      credits: String(course.credits),
      program_id: String(course.program_id),
      status: course.status,
    });
  }

  if (error) {
    return <ErrorState title="Failed to load courses" onRetry={refetch} />;
  }

  const columns: Column<Course>[] = [
    {
      key: "course_code",
      header: tAny("courseCode"),
      cell: (r) => <span className="font-medium">{r.course_code}</span>,
      sortValue: (r) => r.course_code.toLowerCase(),
    },
    {
      key: "title",
      header: tAny("courseTitle"),
      cell: (r) => r.title,
      sortValue: (r) => r.title.toLowerCase(),
    },
    {
      key: "credits",
      header: tAny("courseCredits"),
      cell: (r) => String(r.credits),
      sortValue: (r) => r.credits,
    },
    {
      key: "program_id",
      header: tAny("courseProgramId"),
      cell: (r) => String(r.program_id),
      sortValue: (r) => r.program_id,
    },
    {
      key: "status",
      header: tAny("courseStatus"),
      cell: (r) => r.status,
      sortValue: (r) => r.status.toLowerCase(),
    },
    {
      key: "actions",
      header: "",
      width: "140px",
      cell: (r) => (
        <PermissionGate permission={PERMISSIONS.COURSES_WRITE}>
          <div className="flex gap-1">
            <Button
              variant="outline"
              size="sm"
              onClick={(event) => {
                event.stopPropagation();
                openEdit(r);
              }}
            >
              {tAny("edit")}
            </Button>
            <Button
              variant="destructive"
              size="sm"
              disabled={deleteCourse.isPending}
              onClick={(event) => {
                event.stopPropagation();
                deleteCourse.mutate(
                  r.id,
                  getHandlers({ successTitle: tAny("courseDeleted") }),
                );
              }}
            >
              {tAny("delete")}
            </Button>
          </div>
        </PermissionGate>
      ),
    },
  ];

  return (
    <RequirePermission permission={PERMISSIONS.COURSES_READ}>
    <div className="space-y-4" data-testid="courses-page">
      <PageHeader
        title={t("nav.courses")}
        description={tAny("coursesHelp")}
        icon={BookOpen}
        actions={
          <PermissionGate permission={PERMISSIONS.COURSES_WRITE}>
            <Button size="sm" onClick={openCreate}>
              {tAny("addCourse")}
            </Button>
          </PermissionGate>
        }
      />

      <DataTable
        columns={columns}
        data={data?.courses ?? []}
        isLoading={isLoading}
        getRowKey={(r) => String(r.id)}
        emptyTitle={tAny("noCourses")}
      />

      <DrawerPanel
        open={createOpen}
        onClose={() => {
          setCreateOpen(false);
          resetForm();
        }}
        title={tAny("addCourse")}
        description={tAny("coursesHelp")}
      >
        <CourseForm
          form={form}
          setForm={setForm}
          disabled={isSubmitting}
          canSave={isFormValid}
          onSave={() => {
            createCourse.mutate(
              {
                course_code: form.course_code.trim(),
                title: form.title.trim(),
                credits: parsedCredits,
                program_id: parsedProgramId,
                status: form.status.trim(),
              },
              {
                ...getHandlers({ successTitle: tAny("courseCreated") }),
                onSuccess: () => {
                  getHandlers({ successTitle: tAny("courseCreated") }).onSuccess(undefined);
                  setCreateOpen(false);
                  resetForm();
                },
              },
            );
          }}
          saveLabel={tAny("addCourse")}
        />
      </DrawerPanel>

      <DrawerPanel
        open={Boolean(editCourse)}
        onClose={resetForm}
        title={tAny("edit")}
        description={editCourse?.course_code ?? ""}
      >
        <CourseForm
          form={form}
          setForm={setForm}
          disabled={isSubmitting}
          canSave={isFormValid}
          onSave={() => {
            updateCourse.mutate(
              {
                course_code: form.course_code.trim(),
                title: form.title.trim(),
                credits: parsedCredits,
                program_id: parsedProgramId,
                status: form.status.trim(),
              },
              {
                ...getHandlers({ successTitle: tAny("courseUpdated") }),
                onSuccess: () => {
                  getHandlers({ successTitle: tAny("courseUpdated") }).onSuccess(undefined);
                  resetForm();
                },
              },
            );
          }}
          saveLabel={tAny("save")}
        />
      </DrawerPanel>
    </div>
  );
}

function CourseForm({
  form,
  setForm,
  onSave,
  canSave,
  disabled,
  saveLabel,
}: {
  form: CourseFormState;
  setForm: (value: CourseFormState) => void;
  onSave: () => void;
  canSave: boolean;
  disabled: boolean;
  saveLabel: string;
}) {
  const { t } = useLanguage();
  const tAny = (key: string) => t(key as never);

  return (
    <div className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="course-code">{tAny("courseCode")}</Label>
        <Input
          id="course-code"
          value={form.course_code}
          onChange={(e) => setForm({ ...form, course_code: e.target.value })}
          placeholder="CS101"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="course-title">{tAny("courseTitle")}</Label>
        <Input
          id="course-title"
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
          placeholder="Introduction to Programming"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="course-credits">{tAny("courseCredits")}</Label>
        <Input
          id="course-credits"
          type="number"
          min={0}
          value={form.credits}
          onChange={(e) => setForm({ ...form, credits: e.target.value })}
          placeholder="3"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="course-program-id">{tAny("courseProgramId")}</Label>
        <Input
          id="course-program-id"
          type="number"
          min={1}
          value={form.program_id}
          onChange={(e) => setForm({ ...form, program_id: e.target.value })}
          placeholder="1"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="course-status">{tAny("courseStatus")}</Label>
        <Input
          id="course-status"
          value={form.status}
          onChange={(e) => setForm({ ...form, status: e.target.value })}
          placeholder="active"
        />
      </div>
      <Button disabled={!canSave || disabled} onClick={onSave}>
        {saveLabel}
      </Button>
    </div>
    </RequirePermission>
  );
}
