"use client";

import { useMemo, useState } from "react";
import { FileText } from "lucide-react";
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
  useAcademicRecords,
  useCreateAcademicRecord,
  useUpdateAcademicRecord,
  useDeleteAcademicRecord,
} from "@/modules/academic-records/hooks";
import type { AcademicRecord } from "@/modules/academic-records/types";

interface RecordFormState {
  student_id: string;
  course_id: string;
  grade: string;
  semester: string;
  status: string;
}

const EMPTY_FORM: RecordFormState = {
  student_id: "",
  course_id: "",
  grade: "",
  semester: "",
  status: "active",
};

export default function RecordsPage() {
  const { t } = useLanguage();
  const tAny = (key: string) => t(key as never);
  const { getHandlers } = useMutationFeedback();

  const [createOpen, setCreateOpen] = useState(false);
  const [editRecord, setEditRecord] = useState<AcademicRecord | null>(null);
  const [form, setForm] = useState<RecordFormState>(EMPTY_FORM);

  const { data, isLoading, error, refetch } = useAcademicRecords();
  const createRecord = useCreateAcademicRecord();
  const updateRecord = useUpdateAcademicRecord(editRecord?.id ?? null);
  const deleteRecord = useDeleteAcademicRecord();

  const parsedStudentId = Number.parseInt(form.student_id, 10);
  const parsedCourseId = Number.parseInt(form.course_id, 10);

  const isSubmitting =
    createRecord.isPending || updateRecord.isPending || deleteRecord.isPending;

  const isFormValid = useMemo(
    () =>
      Number.isFinite(parsedStudentId) &&
      parsedStudentId > 0 &&
      Number.isFinite(parsedCourseId) &&
      parsedCourseId > 0 &&
      form.grade.trim().length > 0 &&
      form.semester.trim().length > 0 &&
      form.status.trim().length > 0,
    [parsedStudentId, parsedCourseId, form.grade, form.semester, form.status],
  );

  function resetForm() {
    setForm(EMPTY_FORM);
    setEditRecord(null);
  }

  function openCreate() {
    resetForm();
    setCreateOpen(true);
  }

  function openEdit(record: AcademicRecord) {
    setEditRecord(record);
    setForm({
      student_id: String(record.student_id),
      course_id: String(record.course_id),
      grade: record.grade,
      semester: record.semester,
      status: record.status,
    });
  }

  if (error) {
    return <ErrorState title="Failed to load records" onRetry={refetch} />;
  }

  const columns: Column<AcademicRecord>[] = [
    {
      key: "student_id",
      header: tAny("recordStudentId"),
      cell: (r) => String(r.student_id),
      sortValue: (r) => r.student_id,
    },
    {
      key: "course_id",
      header: tAny("recordCourseId"),
      cell: (r) => String(r.course_id),
      sortValue: (r) => r.course_id,
    },
    {
      key: "grade",
      header: tAny("recordGrade"),
      cell: (r) => r.grade,
      sortValue: (r) => r.grade,
    },
    {
      key: "semester",
      header: tAny("recordSemester"),
      cell: (r) => r.semester,
      sortValue: (r) => r.semester,
    },
    {
      key: "status",
      header: tAny("recordStatus"),
      cell: (r) => r.status,
      sortValue: (r) => r.status,
    },
    {
      key: "actions",
      header: "",
      width: "140px",
      cell: (r) => (
        <PermissionGate permission={PERMISSIONS.RECORDS_WRITE}>
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
              disabled={deleteRecord.isPending}
              onClick={(event) => {
                event.stopPropagation();
                deleteRecord.mutate(
                  r.id,
                  getHandlers({ successTitle: tAny("recordDeleted") }),
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
    <RequirePermission permission={PERMISSIONS.RECORDS_READ}>
    <div className="space-y-4" data-testid="records-page">
      <PageHeader
        title={t("nav.records")}
        description={tAny("recordsHelp")}
        icon={FileText}
        actions={
          <PermissionGate permission={PERMISSIONS.RECORDS_WRITE}>
            <Button size="sm" onClick={openCreate}>
              {tAny("addRecord")}
            </Button>
          </PermissionGate>
        }
      />

      <DataTable
        columns={columns}
        data={data?.records ?? []}
        isLoading={isLoading}
        getRowKey={(r) => String(r.id)}
        emptyTitle={tAny("noRecords")}
      />

      <DrawerPanel
        open={createOpen}
        onClose={() => {
          setCreateOpen(false);
          resetForm();
        }}
        title={tAny("addRecord")}
        description={tAny("recordsHelp")}
      >
        <RecordForm
          form={form}
          setForm={setForm}
          disabled={isSubmitting}
          canSave={isFormValid}
          onSave={() => {
            createRecord.mutate(
              {
                student_id: parsedStudentId,
                course_id: parsedCourseId,
                grade: form.grade.trim(),
                semester: form.semester.trim(),
                status: form.status.trim(),
              },
              {
                ...getHandlers({ successTitle: tAny("recordCreated") }),
                onSuccess: () => {
                  getHandlers({ successTitle: tAny("recordCreated") }).onSuccess(undefined);
                  setCreateOpen(false);
                  resetForm();
                },
              },
            );
          }}
          saveLabel={tAny("addRecord")}
        />
      </DrawerPanel>

      <DrawerPanel
        open={Boolean(editRecord)}
        onClose={resetForm}
        title={tAny("edit")}
        description={editRecord ? `${editRecord.student_id}/${editRecord.course_id}` : ""}
      >
        <RecordForm
          form={form}
          setForm={setForm}
          disabled={isSubmitting}
          canSave={isFormValid}
          onSave={() => {
            updateRecord.mutate(
              {
                student_id: parsedStudentId,
                course_id: parsedCourseId,
                grade: form.grade.trim(),
                semester: form.semester.trim(),
                status: form.status.trim(),
              },
              {
                ...getHandlers({ successTitle: tAny("recordUpdated") }),
                onSuccess: () => {
                  getHandlers({ successTitle: tAny("recordUpdated") }).onSuccess(undefined);
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

function RecordForm({
  form,
  setForm,
  onSave,
  canSave,
  disabled,
  saveLabel,
}: {
  form: RecordFormState;
  setForm: (value: RecordFormState) => void;
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
        <Label htmlFor="record-student-id">{tAny("recordStudentId")}</Label>
        <Input
          id="record-student-id"
          type="number"
          min={1}
          value={form.student_id}
          onChange={(e) => setForm({ ...form, student_id: e.target.value })}
          placeholder="1001"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="record-course-id">{tAny("recordCourseId")}</Label>
        <Input
          id="record-course-id"
          type="number"
          min={1}
          value={form.course_id}
          onChange={(e) => setForm({ ...form, course_id: e.target.value })}
          placeholder="2001"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="record-grade">{tAny("recordGrade")}</Label>
        <Input
          id="record-grade"
          value={form.grade}
          onChange={(e) => setForm({ ...form, grade: e.target.value })}
          placeholder="A"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="record-semester">{tAny("recordSemester")}</Label>
        <Input
          id="record-semester"
          value={form.semester}
          onChange={(e) => setForm({ ...form, semester: e.target.value })}
          placeholder="2026-Spring"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="record-status">{tAny("recordStatus")}</Label>
        <Input
          id="record-status"
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
