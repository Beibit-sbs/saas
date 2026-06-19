"use client";

import { useMemo, useState } from "react";
import { GraduationCap } from "lucide-react";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { DataTable, type Column } from "@/shared/ui/data-table";
import { ErrorState } from "@/shared/ui/error-state";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { usePermissions } from "@/shared/hooks/use-permissions";
import {
  useAlumniBrainContext,
  useAlumniRecords,
  useCreateAlumniRecord,
  useUpdateAlumniStatus,
} from "@/modules/alumni/hooks";
import type { AlumniRecord, AlumniStatus } from "@/modules/alumni/types";
import { useStudents } from "@/modules/students/hooks";

interface AlumniFormState {
  student_id: string;
  graduation_year: string;
  engagement_type: string;
  employer: string;
  contact_email: string;
  notes: string;
}

const EMPTY_FORM: AlumniFormState = {
  student_id: "",
  graduation_year: "",
  engagement_type: "event",
  employer: "",
  contact_email: "",
  notes: "",
};

const STATUS_COLORS: Record<string, string> = {
  active: "bg-blue-100 text-blue-700",
  engaged: "bg-green-100 text-green-700",
  donor: "bg-amber-100 text-amber-700",
  inactive: "bg-gray-100 text-gray-700",
};

const STATUS_OPTIONS: Array<AlumniStatus | "all"> = ["all", "active", "engaged", "donor", "inactive"];

const STATUS_TRANSITIONS: Record<AlumniStatus, AlumniStatus[]> = {
  active: ["engaged", "donor", "inactive"],
  engaged: ["donor", "inactive"],
  donor: ["engaged", "inactive"],
  inactive: ["active"],
};

const STATUS_ACTION_LABELS: Record<AlumniStatus, string> = {
  active: "Reactivate",
  engaged: "Mark engaged",
  donor: "Mark donor",
  inactive: "Mark inactive",
};

export default function AlumniPage() {
  const { getHandlers } = useMutationFeedback();
  const { hasPermission } = usePermissions();
  const [form, setForm] = useState<AlumniFormState>(EMPTY_FORM);
  const [statusFilter, setStatusFilter] = useState<AlumniStatus | "all">("all");

  const canWrite = hasPermission(PERMISSIONS.ALUMNI_WRITE);
  const { data, isLoading, error, refetch } = useAlumniRecords(
    statusFilter === "all" ? undefined : statusFilter,
  );
  const brainContext = useAlumniBrainContext();
  const graduatedStudentsQuery = useStudents({ page: 1, page_size: 200, status: "graduated" });
  const createRecord = useCreateAlumniRecord();
  const updateStatus = useUpdateAlumniStatus();

  const isSubmitting = createRecord.isPending || updateStatus.isPending;
  const graduatedStudents = graduatedStudentsQuery.data?.items ?? [];
  const canCreate = useMemo(() => {
    const studentId = Number(form.student_id);
    const year = Number(form.graduation_year);
    return Number.isInteger(studentId) && studentId > 0 && Number.isInteger(year) && year > 1950;
  }, [form]);

  if (error) {
    return <ErrorState title="Failed to load alumni records" onRetry={refetch} />;
  }

  const columns: Column<AlumniRecord>[] = [
    {
      key: "student_id",
      header: "Student ID",
      cell: (row) => <span className="font-medium">{row.student_id}</span>,
      sortValue: (row) => row.student_id,
    },
    {
      key: "graduation_year",
      header: "Grad Year",
      cell: (row) => String(row.graduation_year),
      sortValue: (row) => row.graduation_year,
    },
    {
      key: "engagement_type",
      header: "Engagement",
      cell: (row) => row.engagement_type,
      sortValue: (row) => row.engagement_type,
    },
    {
      key: "employer",
      header: "Employer",
      cell: (row) => row.employer ?? "—",
      sortValue: (row) => row.employer ?? "",
    },
    {
      key: "status",
      header: "Status",
      cell: (row) => <Badge className={STATUS_COLORS[row.status] ?? ""}>{row.status}</Badge>,
      sortValue: (row) => row.status,
    },
    {
      key: "actions",
      header: "",
      width: "330px",
      cell: (row) => {
        const nextStatuses = STATUS_TRANSITIONS[row.status] ?? [];
        return (
          <div className="flex flex-wrap gap-2">
            {nextStatuses.map((nextStatus) => (
              <Button
                key={nextStatus}
                variant={nextStatus === "inactive" ? "outline" : "default"}
                size="sm"
                disabled={!canWrite || isSubmitting}
                onClick={(event) => {
                  event.stopPropagation();
                  updateStatus.mutate(
                    {
                      recordId: row.id,
                      payload: {
                        status: nextStatus,
                        notes: `Status changed from ${row.status} to ${nextStatus}.`,
                      },
                    },
                    getHandlers({ successTitle: "Alumni status updated" }),
                  );
                }}
              >
                {STATUS_ACTION_LABELS[nextStatus]}
              </Button>
            ))}
          </div>
        );
      },
    },
  ];

  return (
    <RequirePermission permission={PERMISSIONS.ALUMNI_READ}>
      <div className="space-y-4" data-testid="alumni-page">
        <PageHeader
          title="Alumni Lifecycle"
          description="Manage alumni engagement, mentoring, and donor lifecycle."
          icon={GraduationCap}
        />

        <div className="grid gap-3 md:grid-cols-4">
          <div className="rounded-lg border p-3">
            <p className="text-xs text-muted-foreground">Records</p>
            <p className="text-xl font-semibold">{brainContext.data?.total_records ?? 0}</p>
          </div>
          <div className="rounded-lg border p-3">
            <p className="text-xs text-muted-foreground">Engaged</p>
            <p className="text-xl font-semibold">{brainContext.data?.by_status?.engaged ?? 0}</p>
          </div>
          <div className="rounded-lg border p-3">
            <p className="text-xs text-muted-foreground">Donors</p>
            <p className="text-xl font-semibold">{brainContext.data?.by_status?.donor ?? 0}</p>
          </div>
          <div className="rounded-lg border p-3">
            <p className="text-xs text-muted-foreground">Risk</p>
            <p className="text-xl font-semibold capitalize">{brainContext.data?.risk_level ?? "low"}</p>
          </div>
        </div>

        <div className="grid gap-3 rounded-lg border p-4 md:grid-cols-3">
          <div className="space-y-1">
            <Label htmlFor="student-id">Graduated student</Label>
            {graduatedStudents.length > 0 ? (
              <select
                id="student-id"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={form.student_id}
                onChange={(e) => setForm((prev) => ({ ...prev, student_id: e.target.value }))}
              >
                <option value="">Select graduate</option>
                {graduatedStudents.map((student) => (
                  <option key={student.id} value={student.id}>
                    {student.student_number} / {student.first_name} {student.last_name} (#{student.id})
                  </option>
                ))}
              </select>
            ) : (
              <Input
                id="student-id"
                value={form.student_id}
                onChange={(e) => setForm((prev) => ({ ...prev, student_id: e.target.value }))}
                placeholder="510"
              />
            )}
          </div>
          <div className="space-y-1">
            <Label htmlFor="graduation-year">Graduation year</Label>
            <Input
              id="graduation-year"
              value={form.graduation_year}
              onChange={(e) => setForm((prev) => ({ ...prev, graduation_year: e.target.value }))}
              placeholder="2024"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="engagement-type">Engagement type</Label>
            <Input
              id="engagement-type"
              value={form.engagement_type}
              onChange={(e) => setForm((prev) => ({ ...prev, engagement_type: e.target.value }))}
              placeholder="event"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="employer">Employer</Label>
            <Input
              id="employer"
              value={form.employer}
              onChange={(e) => setForm((prev) => ({ ...prev, employer: e.target.value }))}
              placeholder="Contoso"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="contact-email">Contact email</Label>
            <Input
              id="contact-email"
              value={form.contact_email}
              onChange={(e) => setForm((prev) => ({ ...prev, contact_email: e.target.value }))}
              placeholder="alumni@example.edu"
            />
          </div>
          <div className="space-y-1 md:col-span-3">
            <Label htmlFor="notes">Notes</Label>
            <Input
              id="notes"
              value={form.notes}
              onChange={(e) => setForm((prev) => ({ ...prev, notes: e.target.value }))}
              placeholder="Interested in mentoring"
            />
          </div>

          <div className="md:col-span-3">
            <Button
              size="sm"
              data-testid="create-alumni-btn"
              disabled={!canWrite || !canCreate || isSubmitting}
              onClick={() => {
                createRecord.mutate(
                  {
                    student_id: Number(form.student_id),
                    graduation_year: Number(form.graduation_year),
                    engagement_type: form.engagement_type.trim() as AlumniRecord["engagement_type"],
                    employer: form.employer.trim() || undefined,
                    contact_email: form.contact_email.trim() || undefined,
                    notes: form.notes.trim() || undefined,
                  },
                  {
                    ...getHandlers({ successTitle: "Alumni record created" }),
                    onSuccess: () => {
                      getHandlers({ successTitle: "Alumni record created" }).onSuccess(undefined);
                      setForm(EMPTY_FORM);
                    },
                  },
                );
              }}
            >
              Create alumni record
            </Button>
          </div>
        </div>

        <div className="flex flex-wrap gap-2" data-testid="alumni-status-filter">
          {STATUS_OPTIONS.map((status) => (
            <Button
              key={status}
              type="button"
              size="sm"
              variant={statusFilter === status ? "default" : "outline"}
              onClick={() => setStatusFilter(status)}
            >
              {status === "all" ? "All" : status}
            </Button>
          ))}
        </div>

        <DataTable
          columns={columns}
          data={data?.items ?? []}
          isLoading={isLoading}
          getRowKey={(row) => String(row.id)}
          emptyTitle="No alumni records found."
        />
      </div>
    </RequirePermission>
  );
}
