"use client";

import { useMemo, useState } from "react";
import { ScrollText } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { DataTable, type Column } from "@/shared/ui/data-table";
import { ErrorState } from "@/shared/ui/error-state";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useCreateThesis, useThesis, useUpdateThesisStatus } from "@/modules/thesis/hooks";
import type { ThesisRecord } from "@/modules/thesis/types";

interface ThesisFormState {
  thesis_code: string;
  student_id: string;
  title: string;
  advisor_faculty_id: string;
}

const EMPTY_FORM: ThesisFormState = {
  thesis_code: "",
  student_id: "",
  title: "",
  advisor_faculty_id: "",
};

export default function ThesisPage() {
  const { getHandlers } = useMutationFeedback();
  const [form, setForm] = useState<ThesisFormState>(EMPTY_FORM);

  const { data, isLoading, error, refetch } = useThesis();
  const createThesis = useCreateThesis();
  const updateStatus = useUpdateThesisStatus();

  const isSubmitting = createThesis.isPending || updateStatus.isPending;
  const canCreate = useMemo(() => {
    const studentId = Number(form.student_id);
    return (
      form.thesis_code.trim().length > 0
      && form.title.trim().length >= 3
      && Number.isInteger(studentId)
      && studentId > 0
    );
  }, [form]);

  if (error) {
    return <ErrorState title="Failed to load thesis records" onRetry={refetch} />;
  }

  const columns: Column<ThesisRecord>[] = [
    {
      key: "thesis_code",
      header: "Thesis code",
      cell: (row) => <span className="font-medium">{row.thesis_code}</span>,
      sortValue: (row) => row.thesis_code.toLowerCase(),
    },
    {
      key: "title",
      header: "Title",
      cell: (row) => row.title,
      sortValue: (row) => row.title.toLowerCase(),
    },
    {
      key: "student_id",
      header: "Student",
      cell: (row) => String(row.student_id),
      sortValue: (row) => row.student_id,
    },
    {
      key: "status",
      header: "Status",
      cell: (row) => row.status,
      sortValue: (row) => row.status,
    },
    {
      key: "actions",
      header: "",
      width: "170px",
      cell: (row) => (
        <Button
          variant="outline"
          size="sm"
          disabled={isSubmitting || row.status !== "draft"}
          onClick={(event) => {
            event.stopPropagation();
            updateStatus.mutate(
              { thesisId: row.id, payload: { status: "submitted" } },
              getHandlers({ successTitle: "Thesis submitted" }),
            );
          }}
        >
          Mark submitted
        </Button>
      ),
    },
  ];

  return (
    <RequirePermission permission={PERMISSIONS.TRANSCRIPTS_READ}>
      <div className="space-y-4" data-testid="thesis-page">
        <PageHeader
          title="Thesis Workflow"
          description="Manage thesis lifecycle from draft to defense."
          icon={ScrollText}
        />

        <div className="grid gap-3 rounded-lg border p-4 md:grid-cols-4">
          <div className="space-y-1">
            <Label htmlFor="thesis-code">Thesis code</Label>
            <Input
              id="thesis-code"
              value={form.thesis_code}
              onChange={(event) => setForm((prev) => ({ ...prev, thesis_code: event.target.value }))}
              placeholder="TH-2026-001"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="student-id">Student ID</Label>
            <Input
              id="student-id"
              value={form.student_id}
              onChange={(event) => setForm((prev) => ({ ...prev, student_id: event.target.value }))}
              placeholder="101"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="thesis-title">Title</Label>
            <Input
              id="thesis-title"
              value={form.title}
              onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))}
              placeholder="Adaptive Learning Paths"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="advisor-id">Advisor Faculty ID</Label>
            <Input
              id="advisor-id"
              value={form.advisor_faculty_id}
              onChange={(event) => setForm((prev) => ({ ...prev, advisor_faculty_id: event.target.value }))}
              placeholder="FAC-101"
            />
          </div>

          <div className="md:col-span-4">
            <Button
              size="sm"
              disabled={!canCreate || isSubmitting}
              onClick={() => {
                createThesis.mutate(
                  {
                    thesis_code: form.thesis_code.trim(),
                    student_id: Number(form.student_id),
                    title: form.title.trim(),
                    advisor_faculty_id: form.advisor_faculty_id.trim() || undefined,
                  },
                  {
                    ...getHandlers({ successTitle: "Thesis created" }),
                    onSuccess: () => {
                      getHandlers({ successTitle: "Thesis created" }).onSuccess(undefined);
                      setForm(EMPTY_FORM);
                    },
                  },
                );
              }}
            >
              Create thesis record
            </Button>
          </div>
        </div>

        <DataTable
          columns={columns}
          data={data?.items ?? []}
          isLoading={isLoading}
          getRowKey={(row) => String(row.id)}
          emptyTitle="No thesis records found."
        />
      </div>
    </RequirePermission>
  );
}
