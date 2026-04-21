"use client";

import { useMemo, useState } from "react";
import { Users } from "lucide-react";
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
import {
  useAdvisingSessions,
  useCreateAdvisingSession,
  useUpdateAdvisingSessionStatus,
} from "@/modules/advising/hooks";
import type { AdvisingSession } from "@/modules/advising/types";

interface AdvisingFormState {
  student_id: string;
  advisor_id: string;
  session_type: string;
  scheduled_at: string;
  notes: string;
}

const EMPTY_FORM: AdvisingFormState = {
  student_id: "",
  advisor_id: "",
  session_type: "academic",
  scheduled_at: "",
  notes: "",
};

const STATUS_COLORS: Record<string, string> = {
  scheduled: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  cancelled: "bg-red-100 text-red-700",
  no_show: "bg-yellow-100 text-yellow-700",
};

export default function AdvisingPage() {
  const { getHandlers } = useMutationFeedback();
  const [form, setForm] = useState<AdvisingFormState>(EMPTY_FORM);

  const { data, isLoading, error, refetch } = useAdvisingSessions();
  const createSession = useCreateAdvisingSession();
  const updateStatus = useUpdateAdvisingSessionStatus();

  const isSubmitting = createSession.isPending || updateStatus.isPending;
  const canCreate = useMemo(() => {
    const studentId = Number(form.student_id);
    return (
      form.advisor_id.trim().length > 0 &&
      Number.isInteger(studentId) &&
      studentId > 0
    );
  }, [form]);

  if (error) {
    return <ErrorState title="Failed to load advising sessions" onRetry={refetch} />;
  }

  const columns: Column<AdvisingSession>[] = [
    {
      key: "student_id",
      header: "Student ID",
      cell: (row) => <span className="font-medium">{row.student_id}</span>,
      sortValue: (row) => row.student_id,
    },
    {
      key: "advisor_id",
      header: "Advisor",
      cell: (row) => row.advisor_id,
      sortValue: (row) => row.advisor_id.toLowerCase(),
    },
    {
      key: "session_type",
      header: "Type",
      cell: (row) => row.session_type,
      sortValue: (row) => row.session_type,
    },
    {
      key: "status",
      header: "Status",
      cell: (row) => (
        <Badge className={STATUS_COLORS[row.status] ?? ""}>
          {row.status}
        </Badge>
      ),
      sortValue: (row) => row.status,
    },
    {
      key: "scheduled_at",
      header: "Scheduled",
      cell: (row) => row.scheduled_at ?? "—",
      sortValue: (row) => row.scheduled_at ?? "",
    },
    {
      key: "actions",
      header: "",
      width: "170px",
      cell: (row) => (
        <Button
          variant="outline"
          size="sm"
          disabled={isSubmitting || row.status !== "scheduled"}
          onClick={(event) => {
            event.stopPropagation();
            updateStatus.mutate(
              { sessionId: row.id, payload: { status: "completed" } },
              getHandlers({ successTitle: "Session completed" }),
            );
          }}
        >
          Mark completed
        </Button>
      ),
    },
  ];

  return (
    <RequirePermission permission={PERMISSIONS.ADVISING_READ}>
      <div className="space-y-4" data-testid="advising-page">
        <PageHeader
          title="Advising & Mentoring"
          description="Schedule and track academic advising and mentoring sessions."
          icon={Users}
        />

        <div className="grid gap-3 rounded-lg border p-4 md:grid-cols-4">
          <div className="space-y-1">
            <Label htmlFor="student-id">Student ID</Label>
            <Input
              id="student-id"
              value={form.student_id}
              onChange={(e) => setForm((prev) => ({ ...prev, student_id: e.target.value }))}
              placeholder="101"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="advisor-id">Advisor ID</Label>
            <Input
              id="advisor-id"
              value={form.advisor_id}
              onChange={(e) => setForm((prev) => ({ ...prev, advisor_id: e.target.value }))}
              placeholder="FAC-101"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="session-type">Session type</Label>
            <Input
              id="session-type"
              value={form.session_type}
              onChange={(e) => setForm((prev) => ({ ...prev, session_type: e.target.value }))}
              placeholder="academic"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="scheduled-at">Scheduled at</Label>
            <Input
              id="scheduled-at"
              value={form.scheduled_at}
              onChange={(e) => setForm((prev) => ({ ...prev, scheduled_at: e.target.value }))}
              placeholder="2026-05-01T10:00"
            />
          </div>
          <div className="space-y-1 md:col-span-4">
            <Label htmlFor="notes">Notes</Label>
            <Input
              id="notes"
              value={form.notes}
              onChange={(e) => setForm((prev) => ({ ...prev, notes: e.target.value }))}
              placeholder="Session agenda..."
            />
          </div>

          <div className="md:col-span-4">
            <Button
              size="sm"
              data-testid="create-session-btn"
              disabled={!canCreate || isSubmitting}
              onClick={() => {
                createSession.mutate(
                  {
                    student_id: Number(form.student_id),
                    advisor_id: form.advisor_id.trim(),
                    session_type: form.session_type as AdvisingSession["session_type"],
                    scheduled_at: form.scheduled_at.trim() || undefined,
                    notes: form.notes.trim() || undefined,
                  },
                  {
                    ...getHandlers({ successTitle: "Session created" }),
                    onSuccess: () => {
                      getHandlers({ successTitle: "Session created" }).onSuccess(undefined);
                      setForm(EMPTY_FORM);
                    },
                  },
                );
              }}
            >
              Schedule session
            </Button>
          </div>
        </div>

        <DataTable
          columns={columns}
          data={data?.items ?? []}
          isLoading={isLoading}
          getRowKey={(row) => String(row.id)}
          emptyTitle="No advising sessions found."
        />
      </div>
    </RequirePermission>
  );
}
