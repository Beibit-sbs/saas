"use client";

import { useMemo, useState } from "react";
import { Users } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { DataTable, type Column } from "@/shared/ui/data-table";
import { DrawerPanel } from "@/shared/ui/drawer-panel";
import { ErrorState } from "@/shared/ui/error-state";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { PageHeader } from "@/shared/ui/page-header";
import { PermissionGate } from "@/shared/ui/permission-gate";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useLanguage } from "@/app/components/LanguageProvider";
import { PERMISSIONS } from "@/shared/config/permissions";
import {
  useFaculty,
  useCreateFaculty,
  useUpdateFaculty,
  useDeleteFaculty,
} from "@/modules/faculty/hooks";
import type { FacultyMember } from "@/modules/faculty/types";

interface FacultyFormState {
  faculty_id: string;
  first_name: string;
  last_name: string;
  department: string;
  email: string;
  status: string;
}

const EMPTY_FORM: FacultyFormState = {
  faculty_id: "",
  first_name: "",
  last_name: "",
  department: "",
  email: "",
  status: "active",
};

export default function FacultyPage() {
  const { t } = useLanguage();
  const tAny = (key: string) => t(key as never);
  const { getHandlers } = useMutationFeedback();

  const [createOpen, setCreateOpen] = useState(false);
  const [editFaculty, setEditFaculty] = useState<FacultyMember | null>(null);
  const [form, setForm] = useState<FacultyFormState>(EMPTY_FORM);

  const { data, isLoading, error, refetch } = useFaculty();
  const createFaculty = useCreateFaculty();
  const updateFaculty = useUpdateFaculty(editFaculty?.id ?? null);
  const deleteFaculty = useDeleteFaculty();

  const isSubmitting =
    createFaculty.isPending || updateFaculty.isPending || deleteFaculty.isPending;

  const isFormValid = useMemo(
    () =>
      form.faculty_id.trim().length > 0 &&
      form.first_name.trim().length > 0 &&
      form.last_name.trim().length > 0 &&
      form.department.trim().length > 0 &&
      form.email.trim().length >= 3 &&
      form.status.trim().length > 0,
    [form],
  );

  function resetForm() {
    setForm(EMPTY_FORM);
    setEditFaculty(null);
  }

  function openCreate() {
    resetForm();
    setCreateOpen(true);
  }

  function openEdit(member: FacultyMember) {
    setEditFaculty(member);
    setForm({
      faculty_id: member.faculty_id,
      first_name: member.first_name,
      last_name: member.last_name,
      department: member.department,
      email: member.email,
      status: member.status,
    });
  }

  if (error) {
    return <ErrorState title="Failed to load faculty" onRetry={refetch} />;
  }

  const columns: Column<FacultyMember>[] = [
    {
      key: "faculty_id",
      header: tAny("facultyCode"),
      cell: (r) => <span className="font-medium">{r.faculty_id}</span>,
      sortValue: (r) => r.faculty_id.toLowerCase(),
    },
    {
      key: "first_name",
      header: tAny("facultyFirstName"),
      cell: (r) => r.first_name,
      sortValue: (r) => r.first_name.toLowerCase(),
    },
    {
      key: "last_name",
      header: tAny("facultyLastName"),
      cell: (r) => r.last_name,
      sortValue: (r) => r.last_name.toLowerCase(),
    },
    {
      key: "department",
      header: tAny("facultyDepartment"),
      cell: (r) => r.department,
      sortValue: (r) => r.department.toLowerCase(),
    },
    {
      key: "email",
      header: tAny("facultyEmail"),
      cell: (r) => r.email,
      sortValue: (r) => r.email.toLowerCase(),
    },
    {
      key: "status",
      header: tAny("facultyStatus"),
      cell: (r) => r.status,
      sortValue: (r) => r.status.toLowerCase(),
    },
    {
      key: "actions",
      header: "",
      width: "140px",
      cell: (r) => (
        <PermissionGate permission={PERMISSIONS.FACULTY_WRITE}>
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
              disabled={deleteFaculty.isPending}
              onClick={(event) => {
                event.stopPropagation();
                deleteFaculty.mutate(
                  r.id,
                  getHandlers({ successTitle: tAny("facultyDeleted") }),
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
    <div className="space-y-4" data-testid="faculty-page">
      <PageHeader
        title={t("nav.faculty")}
        description={tAny("facultyHelp")}
        icon={Users}
        actions={
          <PermissionGate permission={PERMISSIONS.FACULTY_WRITE}>
            <Button size="sm" onClick={openCreate}>
              {tAny("addFaculty")}
            </Button>
          </PermissionGate>
        }
      />

      <DataTable
        columns={columns}
        data={data?.faculty ?? []}
        isLoading={isLoading}
        getRowKey={(r) => String(r.id)}
        emptyTitle={tAny("noFaculty")}
      />

      <DrawerPanel
        open={createOpen}
        onClose={() => {
          setCreateOpen(false);
          resetForm();
        }}
        title={tAny("addFaculty")}
        description={tAny("facultyHelp")}
      >
        <FacultyForm
          form={form}
          setForm={setForm}
          disabled={isSubmitting}
          canSave={isFormValid}
          onSave={() => {
            createFaculty.mutate(
              {
                faculty_id: form.faculty_id.trim(),
                first_name: form.first_name.trim(),
                last_name: form.last_name.trim(),
                department: form.department.trim(),
                email: form.email.trim(),
                status: form.status.trim(),
              },
              {
                ...getHandlers({ successTitle: tAny("facultyCreated") }),
                onSuccess: () => {
                  getHandlers({ successTitle: tAny("facultyCreated") }).onSuccess(undefined);
                  setCreateOpen(false);
                  resetForm();
                },
              },
            );
          }}
          saveLabel={tAny("addFaculty")}
        />
      </DrawerPanel>

      <DrawerPanel
        open={Boolean(editFaculty)}
        onClose={resetForm}
        title={tAny("edit")}
        description={editFaculty?.faculty_id ?? ""}
      >
        <FacultyForm
          form={form}
          setForm={setForm}
          disabled={isSubmitting}
          canSave={isFormValid}
          onSave={() => {
            updateFaculty.mutate(
              {
                faculty_id: form.faculty_id.trim(),
                first_name: form.first_name.trim(),
                last_name: form.last_name.trim(),
                department: form.department.trim(),
                email: form.email.trim(),
                status: form.status.trim(),
              },
              {
                ...getHandlers({ successTitle: tAny("facultyUpdated") }),
                onSuccess: () => {
                  getHandlers({ successTitle: tAny("facultyUpdated") }).onSuccess(undefined);
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

function FacultyForm({
  form,
  setForm,
  onSave,
  canSave,
  disabled,
  saveLabel,
}: {
  form: FacultyFormState;
  setForm: (value: FacultyFormState) => void;
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
        <Label htmlFor="faculty-id">{tAny("facultyCode")}</Label>
        <Input
          id="faculty-id"
          value={form.faculty_id}
          onChange={(e) => setForm({ ...form, faculty_id: e.target.value })}
          placeholder="FAC-001"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="faculty-first-name">{tAny("facultyFirstName")}</Label>
        <Input
          id="faculty-first-name"
          value={form.first_name}
          onChange={(e) => setForm({ ...form, first_name: e.target.value })}
          placeholder="Ada"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="faculty-last-name">{tAny("facultyLastName")}</Label>
        <Input
          id="faculty-last-name"
          value={form.last_name}
          onChange={(e) => setForm({ ...form, last_name: e.target.value })}
          placeholder="Lovelace"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="faculty-department">{tAny("facultyDepartment")}</Label>
        <Input
          id="faculty-department"
          value={form.department}
          onChange={(e) => setForm({ ...form, department: e.target.value })}
          placeholder="Computer Science"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="faculty-email">{tAny("facultyEmail")}</Label>
        <Input
          id="faculty-email"
          type="email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          placeholder="ada@example.edu"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="faculty-status">{tAny("facultyStatus")}</Label>
        <Input
          id="faculty-status"
          value={form.status}
          onChange={(e) => setForm({ ...form, status: e.target.value })}
          placeholder="active"
        />
      </div>
      <Button disabled={!canSave || disabled} onClick={onSave}>
        {saveLabel}
      </Button>
    </div>
  );
}
