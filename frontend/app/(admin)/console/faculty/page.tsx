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
import { PermissionGate, RequirePermission } from "@/shared/ui/permission-gate";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useLanguage } from "@/app/components/LanguageProvider";
import { PERMISSIONS } from "@/shared/config/permissions";
import {
  useFaculty,
  useFacultyContracts,
  useCreateFacultyContract,
  useCreateFaculty,
  useUpdateFaculty,
  useUpdateFacultyContractStatus,
  useDeleteFaculty,
} from "@/modules/faculty/hooks";
import type { FacultyContract, FacultyMember } from "@/modules/faculty/types";

interface FacultyFormState {
  faculty_id: string;
  first_name: string;
  last_name: string;
  department: string;
  email: string;
  status: string;
}

interface FacultyContractFormState {
  faculty_id: string;
  contract_type: string;
  start_date: string;
  end_date: string;
  fte_ratio: string;
  max_credit_hours: string;
  status: string;
  notes: string;
}

const EMPTY_FORM: FacultyFormState = {
  faculty_id: "",
  first_name: "",
  last_name: "",
  department: "",
  email: "",
  status: "active",
};

const EMPTY_CONTRACT_FORM: FacultyContractFormState = {
  faculty_id: "",
  contract_type: "full_time",
  start_date: "",
  end_date: "",
  fte_ratio: "1",
  max_credit_hours: "18",
  status: "draft",
  notes: "",
};

export default function FacultyPage() {
  const { t } = useLanguage();
  const tAny = (key: string) => t(key as never);
  const { getHandlers } = useMutationFeedback();

  const [createOpen, setCreateOpen] = useState(false);
  const [editFaculty, setEditFaculty] = useState<FacultyMember | null>(null);
  const [form, setForm] = useState<FacultyFormState>(EMPTY_FORM);
  const [createContractOpen, setCreateContractOpen] = useState(false);
  const [editContract, setEditContract] = useState<FacultyContract | null>(null);
  const [contractForm, setContractForm] = useState<FacultyContractFormState>(
    EMPTY_CONTRACT_FORM,
  );

  const { data, isLoading, error, refetch } = useFaculty();
  const contractsQuery = useFacultyContracts();
  const createFaculty = useCreateFaculty();
  const updateFaculty = useUpdateFaculty(editFaculty?.id ?? null);
  const deleteFaculty = useDeleteFaculty();
  const createContract = useCreateFacultyContract();
  const updateContractStatus = useUpdateFacultyContractStatus(editContract?.id ?? null);

  const isSubmitting =
    createFaculty.isPending ||
    updateFaculty.isPending ||
    deleteFaculty.isPending ||
    createContract.isPending ||
    updateContractStatus.isPending;

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

  const isContractFormValid = useMemo(() => {
    const fte = Number.parseFloat(contractForm.fte_ratio);
    const maxCredits = Number.parseInt(contractForm.max_credit_hours, 10);
    return (
      contractForm.faculty_id.trim().length > 0 &&
      contractForm.contract_type.trim().length > 0 &&
      contractForm.start_date.trim().length > 0 &&
      contractForm.status.trim().length > 0 &&
      Number.isFinite(fte) &&
      fte > 0 &&
      fte <= 1 &&
      Number.isFinite(maxCredits) &&
      maxCredits >= 1 &&
      maxCredits <= 100
    );
  }, [contractForm]);

  function resetForm() {
    setForm(EMPTY_FORM);
    setEditFaculty(null);
  }

  function openCreate() {
    resetForm();
    setCreateOpen(true);
  }

  function resetContractForm() {
    setContractForm(EMPTY_CONTRACT_FORM);
    setEditContract(null);
  }

  function openCreateContract() {
    resetContractForm();
    setCreateContractOpen(true);
  }

  function openEditContractStatus(contract: FacultyContract) {
    setEditContract(contract);
    setContractForm({
      faculty_id: contract.faculty_id,
      contract_type: contract.contract_type,
      start_date: contract.start_date,
      end_date: contract.end_date ?? "",
      fte_ratio: String(contract.fte_ratio),
      max_credit_hours: String(contract.max_credit_hours),
      status: contract.status,
      notes: contract.notes ?? "",
    });
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

  const contractColumns: Column<FacultyContract>[] = [
    {
      key: "faculty_id",
      header: "Faculty ID",
      cell: (r) => <span className="font-medium">{r.faculty_id}</span>,
      sortValue: (r) => r.faculty_id.toLowerCase(),
    },
    {
      key: "contract_type",
      header: "Contract",
      cell: (r) => r.contract_type,
      sortValue: (r) => r.contract_type.toLowerCase(),
    },
    {
      key: "start_date",
      header: "Start",
      cell: (r) => r.start_date,
      sortValue: (r) => r.start_date,
    },
    {
      key: "end_date",
      header: "End",
      cell: (r) => r.end_date ?? "-",
      sortValue: (r) => (r.end_date ?? "").toLowerCase(),
    },
    {
      key: "status",
      header: "Status",
      cell: (r) => r.status,
      sortValue: (r) => r.status.toLowerCase(),
    },
    {
      key: "actions",
      header: "",
      width: "140px",
      cell: (r) => (
        <PermissionGate permission={PERMISSIONS.FACULTY_WRITE}>
          <Button
            variant="outline"
            size="sm"
            onClick={(event) => {
              event.stopPropagation();
              openEditContractStatus(r);
            }}
          >
            Update status
          </Button>
        </PermissionGate>
      ),
    },
  ];

  return (
    <RequirePermission permission={PERMISSIONS.FACULTY_READ}>
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

      <PageHeader
        title="Faculty Contracts"
        description="Contract lifecycle for faculty workload and appointment planning"
        icon={Users}
        actions={
          <PermissionGate permission={PERMISSIONS.FACULTY_WRITE}>
            <Button size="sm" onClick={openCreateContract}>
              Add contract
            </Button>
          </PermissionGate>
        }
      />

      <DataTable
        columns={contractColumns}
        data={contractsQuery.data?.contracts ?? []}
        isLoading={contractsQuery.isLoading}
        getRowKey={(r) => String(r.id)}
        emptyTitle="No contract records found."
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

      <DrawerPanel
        open={createContractOpen}
        onClose={() => {
          setCreateContractOpen(false);
          resetContractForm();
        }}
        title="Add contract"
        description="Create a faculty contract"
      >
        <FacultyContractForm
          form={contractForm}
          setForm={setContractForm}
          disabled={isSubmitting}
          canSave={isContractFormValid}
          onSave={() => {
            createContract.mutate(
              {
                faculty_id: contractForm.faculty_id.trim(),
                contract_type: contractForm.contract_type.trim(),
                start_date: contractForm.start_date.trim(),
                end_date: contractForm.end_date.trim() || null,
                fte_ratio: Number.parseFloat(contractForm.fte_ratio),
                max_credit_hours: Number.parseInt(contractForm.max_credit_hours, 10),
                status: contractForm.status.trim(),
                notes: contractForm.notes.trim() || null,
              },
              {
                ...getHandlers({ successTitle: "Contract created" }),
                onSuccess: () => {
                  getHandlers({ successTitle: "Contract created" }).onSuccess(undefined);
                  setCreateContractOpen(false);
                  resetContractForm();
                },
              },
            );
          }}
          saveLabel="Add contract"
        />
      </DrawerPanel>

      <DrawerPanel
        open={Boolean(editContract)}
        onClose={resetContractForm}
        title="Update contract status"
        description={editContract?.faculty_id ?? ""}
      >
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="contract-status">Status</Label>
            <Input
              id="contract-status"
              value={contractForm.status}
              onChange={(e) => setContractForm({ ...contractForm, status: e.target.value })}
              placeholder="active"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="contract-notes">Notes</Label>
            <Input
              id="contract-notes"
              value={contractForm.notes}
              onChange={(e) => setContractForm({ ...contractForm, notes: e.target.value })}
              placeholder="Signed and approved"
            />
          </div>
          <Button
            disabled={contractForm.status.trim().length === 0 || isSubmitting}
            onClick={() => {
              updateContractStatus.mutate(
                {
                  status: contractForm.status.trim(),
                  notes: contractForm.notes.trim() || null,
                },
                {
                  ...getHandlers({ successTitle: "Contract updated" }),
                  onSuccess: () => {
                    getHandlers({ successTitle: "Contract updated" }).onSuccess(undefined);
                    resetContractForm();
                  },
                },
              );
            }}
          >
            Save
          </Button>
        </div>
      </DrawerPanel>
    </div>
    </RequirePermission>
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

function FacultyContractForm({
  form,
  setForm,
  onSave,
  canSave,
  disabled,
  saveLabel,
}: {
  form: FacultyContractFormState;
  setForm: (value: FacultyContractFormState) => void;
  onSave: () => void;
  canSave: boolean;
  disabled: boolean;
  saveLabel: string;
}) {
  return (
    <div className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="contract-faculty-id">Faculty ID</Label>
        <Input
          id="contract-faculty-id"
          value={form.faculty_id}
          onChange={(e) => setForm({ ...form, faculty_id: e.target.value })}
          placeholder="FAC-001"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="contract-type">Contract type</Label>
        <Input
          id="contract-type"
          value={form.contract_type}
          onChange={(e) => setForm({ ...form, contract_type: e.target.value })}
          placeholder="full_time"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="contract-start">Start date</Label>
        <Input
          id="contract-start"
          value={form.start_date}
          onChange={(e) => setForm({ ...form, start_date: e.target.value })}
          placeholder="2026-09-01"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="contract-end">End date (optional)</Label>
        <Input
          id="contract-end"
          value={form.end_date}
          onChange={(e) => setForm({ ...form, end_date: e.target.value })}
          placeholder="2027-08-31"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="contract-fte">FTE ratio</Label>
        <Input
          id="contract-fte"
          type="number"
          step="0.05"
          min="0.1"
          max="1"
          value={form.fte_ratio}
          onChange={(e) => setForm({ ...form, fte_ratio: e.target.value })}
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="contract-capacity">Max credit hours</Label>
        <Input
          id="contract-capacity"
          type="number"
          min="1"
          max="100"
          value={form.max_credit_hours}
          onChange={(e) => setForm({ ...form, max_credit_hours: e.target.value })}
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="contract-status-create">Status</Label>
        <Input
          id="contract-status-create"
          value={form.status}
          onChange={(e) => setForm({ ...form, status: e.target.value })}
          placeholder="draft"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="contract-notes-create">Notes</Label>
        <Input
          id="contract-notes-create"
          value={form.notes}
          onChange={(e) => setForm({ ...form, notes: e.target.value })}
          placeholder="Optional notes"
        />
      </div>
      <Button disabled={!canSave || disabled} onClick={onSave}>
        {saveLabel}
      </Button>
    </div>
  );
}
