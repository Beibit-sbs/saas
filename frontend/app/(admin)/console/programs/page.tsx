"use client";

import { useMemo, useState } from "react";
import { GraduationCap } from "lucide-react";
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
  usePrograms,
  useCreateProgram,
  useUpdateProgram,
  useDeleteProgram,
} from "@/modules/programs/hooks";
import type { Program } from "@/modules/programs/types";

interface ProgramFormState {
  program_code: string;
  title: string;
  degree_type: string;
  faculty: string;
  status: string;
}

const EMPTY_FORM: ProgramFormState = {
  program_code: "",
  title: "",
  degree_type: "",
  faculty: "",
  status: "active",
};

export default function ProgramsPage() {
  const { t } = useLanguage();
  const tAny = (key: string) => t(key as never);
  const { getHandlers } = useMutationFeedback();

  const [createOpen, setCreateOpen] = useState(false);
  const [editProgram, setEditProgram] = useState<Program | null>(null);
  const [form, setForm] = useState<ProgramFormState>(EMPTY_FORM);

  const { data, isLoading, error, refetch } = usePrograms();
  const createProgram = useCreateProgram();
  const updateProgram = useUpdateProgram(editProgram?.id ?? null);
  const deleteProgram = useDeleteProgram();

  const isSubmitting =
    createProgram.isPending || updateProgram.isPending || deleteProgram.isPending;

  const isFormValid = useMemo(
    () =>
      form.program_code.trim().length > 0 &&
      form.title.trim().length > 0 &&
      form.degree_type.trim().length > 0 &&
      form.faculty.trim().length > 0 &&
      form.status.trim().length > 0,
    [form],
  );

  function resetForm() {
    setForm(EMPTY_FORM);
    setEditProgram(null);
  }

  function openCreate() {
    resetForm();
    setCreateOpen(true);
  }

  function openEdit(program: Program) {
    setEditProgram(program);
    setForm({
      program_code: program.program_code,
      title: program.title,
      degree_type: program.degree_type,
      faculty: program.faculty,
      status: program.status,
    });
  }

  if (error) {
    return <ErrorState title="Failed to load programs" onRetry={refetch} />;
  }

  const columns: Column<Program>[] = [
    {
      key: "program_code",
      header: tAny("programCode"),
      cell: (r) => <span className="font-medium">{r.program_code}</span>,
      sortValue: (r) => r.program_code.toLowerCase(),
    },
    {
      key: "title",
      header: tAny("programTitle"),
      cell: (r) => r.title,
      sortValue: (r) => r.title.toLowerCase(),
    },
    {
      key: "degree_type",
      header: tAny("programDegreeType"),
      cell: (r) => r.degree_type,
      sortValue: (r) => r.degree_type.toLowerCase(),
    },
    {
      key: "faculty",
      header: tAny("programFaculty"),
      cell: (r) => r.faculty,
      sortValue: (r) => r.faculty.toLowerCase(),
    },
    {
      key: "status",
      header: tAny("programStatus"),
      cell: (r) => r.status,
      sortValue: (r) => r.status.toLowerCase(),
    },
    {
      key: "actions",
      header: "",
      width: "140px",
      cell: (r) => (
        <PermissionGate permission={PERMISSIONS.PROGRAMS_WRITE}>
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
              disabled={deleteProgram.isPending}
              onClick={(event) => {
                event.stopPropagation();
                deleteProgram.mutate(
                  r.id,
                  getHandlers({ successTitle: tAny("programDeleted") }),
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
    <div className="space-y-4" data-testid="programs-page">
      <PageHeader
        title={t("nav.programs")}
        description={tAny("programsHelp")}
        icon={GraduationCap}
        actions={
          <PermissionGate permission={PERMISSIONS.PROGRAMS_WRITE}>
            <Button size="sm" onClick={openCreate}>
              {tAny("addProgram")}
            </Button>
          </PermissionGate>
        }
      />

      <DataTable
        columns={columns}
        data={data?.programs ?? []}
        isLoading={isLoading}
        getRowKey={(r) => String(r.id)}
        emptyTitle={tAny("noPrograms")}
      />

      <DrawerPanel
        open={createOpen}
        onClose={() => {
          setCreateOpen(false);
          resetForm();
        }}
        title={tAny("addProgram")}
        description={tAny("programsHelp")}
      >
        <ProgramForm
          form={form}
          setForm={setForm}
          disabled={isSubmitting}
          onSave={() => {
            createProgram.mutate(form, {
              ...getHandlers({ successTitle: tAny("programCreated") }),
              onSuccess: () => {
                getHandlers({ successTitle: tAny("programCreated") }).onSuccess(undefined);
                setCreateOpen(false);
                resetForm();
              },
            });
          }}
          canSave={isFormValid}
          saveLabel={tAny("addProgram")}
        />
      </DrawerPanel>

      <DrawerPanel
        open={Boolean(editProgram)}
        onClose={resetForm}
        title={tAny("edit")}
        description={editProgram?.program_code ?? ""}
      >
        <ProgramForm
          form={form}
          setForm={setForm}
          disabled={isSubmitting}
          onSave={() => {
            updateProgram.mutate(form, {
              ...getHandlers({ successTitle: tAny("programUpdated") }),
              onSuccess: () => {
                getHandlers({ successTitle: tAny("programUpdated") }).onSuccess(undefined);
                resetForm();
              },
            });
          }}
          canSave={isFormValid}
          saveLabel={tAny("save")}
        />
      </DrawerPanel>
    </div>
  );
}

function ProgramForm({
  form,
  setForm,
  onSave,
  canSave,
  disabled,
  saveLabel,
}: {
  form: ProgramFormState;
  setForm: (value: ProgramFormState) => void;
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
        <Label htmlFor="program-code">{tAny("programCode")}</Label>
        <Input
          id="program-code"
          value={form.program_code}
          onChange={(e) => setForm({ ...form, program_code: e.target.value })}
          placeholder="CS-BSC"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="program-title">{tAny("programTitle")}</Label>
        <Input
          id="program-title"
          value={form.title}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
          placeholder="Computer Science"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="program-degree">{tAny("programDegreeType")}</Label>
        <Input
          id="program-degree"
          value={form.degree_type}
          onChange={(e) => setForm({ ...form, degree_type: e.target.value })}
          placeholder="Bachelor"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="program-faculty">{tAny("programFaculty")}</Label>
        <Input
          id="program-faculty"
          value={form.faculty}
          onChange={(e) => setForm({ ...form, faculty: e.target.value })}
          placeholder="Engineering"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="program-status">{tAny("programStatus")}</Label>
        <Input
          id="program-status"
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
