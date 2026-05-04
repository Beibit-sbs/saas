"use client";

import { useMemo, useState } from "react";
import { Wallet } from "lucide-react";
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
  useCreateDelinquencyRecord,
  useDelinquencyRecords,
  useUpdateDelinquencyEscalation,
  useUpdateDelinquencyStatus,
} from "@/modules/delinquency-collections/hooks";
import type {
  DelinquencyRecord,
  DelinquencyStatus,
  EscalationStage,
} from "@/modules/delinquency-collections/types";
import { Wave1KpiBar } from "@/modules/platform/kpi/wave1-kpi-bar";

const DELINQUENCY_KPI_KEYS = [
  "delinquency_cases_active",
  "overdue_amount_at_risk",
  "delinquency_recovery_rate",
] as const;

const DELINQUENCY_KPI_LABELS: Record<string, string> = {
  delinquency_cases_active: "Active Cases",
  overdue_amount_at_risk: "At-Risk Amount (cents)",
  delinquency_recovery_rate: "Recovery Rate (%)",
};

interface DelinquencyFormState {
  student_id: string;
  invoice_code: string;
  amount_due: string;
  days_overdue: string;
}

const EMPTY_FORM: DelinquencyFormState = {
  student_id: "",
  invoice_code: "",
  amount_due: "",
  days_overdue: "",
};

const STATUS_COLORS: Record<DelinquencyStatus, string> = {
  open: "bg-yellow-100 text-yellow-700",
  in_review: "bg-blue-100 text-blue-700",
  escalated: "bg-orange-100 text-orange-700",
  resolved: "bg-green-100 text-green-700",
  written_off: "bg-gray-100 text-gray-700",
};

const STAGE_COLORS: Record<EscalationStage, string> = {
  stage_1: "bg-blue-50 text-blue-700",
  stage_2: "bg-indigo-100 text-indigo-700",
  stage_3: "bg-purple-100 text-purple-700",
  legal: "bg-red-100 text-red-700",
};

const NEXT_STATUS: Record<DelinquencyStatus, DelinquencyStatus[]> = {
  open: ["in_review", "resolved"],
  in_review: ["escalated", "resolved"],
  escalated: ["resolved", "written_off"],
  resolved: [],
  written_off: [],
};

const NEXT_STAGE: Record<EscalationStage, EscalationStage[]> = {
  stage_1: ["stage_2"],
  stage_2: ["stage_3"],
  stage_3: ["legal"],
  legal: [],
};

export default function DelinquencyCollectionsPage() {
  const { getHandlers } = useMutationFeedback();
  const [form, setForm] = useState<DelinquencyFormState>(EMPTY_FORM);

  const { data, isLoading, error, refetch } = useDelinquencyRecords();
  const createRecord = useCreateDelinquencyRecord();
  const updateStatus = useUpdateDelinquencyStatus();
  const updateEscalation = useUpdateDelinquencyEscalation();

  const isSubmitting = createRecord.isPending || updateStatus.isPending || updateEscalation.isPending;

  const canCreate = useMemo(() => {
    const amount = Number(form.amount_due);
    const days = Number(form.days_overdue);
    return (
      form.student_id.trim().length > 0
      && form.invoice_code.trim().length > 0
      && !Number.isNaN(amount)
      && amount > 0
      && !Number.isNaN(days)
      && days >= 1
    );
  }, [form]);

  if (error) {
    return <ErrorState title="Failed to load delinquency records" onRetry={refetch} />;
  }

  const columns: Column<DelinquencyRecord>[] = [
    {
      key: "student_id",
      header: "Student ID",
      cell: (row) => <span className="font-mono text-xs">{row.student_id}</span>,
      sortValue: (row) => row.student_id,
    },
    {
      key: "invoice_code",
      header: "Invoice",
      cell: (row) => <span className="font-medium">{row.invoice_code}</span>,
      sortValue: (row) => row.invoice_code,
    },
    {
      key: "amount_due",
      header: "Amount Due",
      cell: (row) => `$${row.amount_due.toLocaleString()}`,
      sortValue: (row) => row.amount_due,
    },
    {
      key: "days_overdue",
      header: "Days Overdue",
      cell: (row) => row.days_overdue,
      sortValue: (row) => row.days_overdue,
    },
    {
      key: "escalation_stage",
      header: "Escalation",
      cell: (row) => (
        <Badge className={STAGE_COLORS[row.escalation_stage]}>{row.escalation_stage}</Badge>
      ),
      sortValue: (row) => row.escalation_stage,
    },
    {
      key: "status",
      header: "Status",
      cell: (row) => <Badge className={STATUS_COLORS[row.status]}>{row.status}</Badge>,
      sortValue: (row) => row.status,
    },
    {
      key: "actions",
      header: "Actions",
      cell: (row) => {
        const statusNext = NEXT_STATUS[row.status] ?? [];
        const stageNext = NEXT_STAGE[row.escalation_stage] ?? [];

        if (statusNext.length === 0 && stageNext.length === 0) return null;

        return (
          <div className="flex gap-1 flex-wrap">
            {statusNext.map((next) => (
              <Button
                key={`status-${next}`}
                variant="outline"
                size="sm"
                disabled={isSubmitting}
                onClick={() =>
                  updateStatus.mutate(
                    { recordId: row.id, payload: { status: next } },
                    getHandlers({ successTitle: `Status moved to ${next}` }),
                  )
                }
              >
                status → {next}
              </Button>
            ))}
            {stageNext.map((next) => (
              <Button
                key={`stage-${next}`}
                variant="outline"
                size="sm"
                disabled={isSubmitting}
                onClick={() =>
                  updateEscalation.mutate(
                    { recordId: row.id, payload: { escalation_stage: next } },
                    getHandlers({ successTitle: `Escalation moved to ${next}` }),
                  )
                }
              >
                stage → {next}
              </Button>
            ))}
          </div>
        );
      },
    },
  ];

  const handleSubmit = () => {
    if (!canCreate) return;

    createRecord.mutate(
      {
        student_id: form.student_id.trim(),
        invoice_code: form.invoice_code.trim(),
        amount_due: Number(form.amount_due),
        days_overdue: Number(form.days_overdue),
        escalation_stage: "stage_1",
        status: "open",
      },
      {
        ...getHandlers({ successTitle: "Delinquency record created" }),
        onSuccess: (...args) => {
          setForm(EMPTY_FORM);
          getHandlers({ successTitle: "Delinquency record created" }).onSuccess?.(args[0]);
        },
      },
    );
  };

  return (
    <RequirePermission permission={PERMISSIONS.FINANCE_READ}>
      <div className="space-y-8">
        <PageHeader
          title="Delinquency & Collections"
          description="Track overdue invoices and escalation workflow"
          icon={Wallet}
        />

        <Wave1KpiBar metricKeys={[...DELINQUENCY_KPI_KEYS]} labels={DELINQUENCY_KPI_LABELS} />

        <RequirePermission permission={PERMISSIONS.FINANCE_WRITE}>
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-lg font-semibold mb-4">Add Delinquency Record</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <Label htmlFor="student_id">Student ID</Label>
                <Input
                  id="student_id"
                  placeholder="STU-001"
                  value={form.student_id}
                  onChange={(e) => setForm((f) => ({ ...f, student_id: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="invoice_code">Invoice Code</Label>
                <Input
                  id="invoice_code"
                  placeholder="INV-2026-009"
                  value={form.invoice_code}
                  onChange={(e) => setForm((f) => ({ ...f, invoice_code: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="amount_due">Amount Due</Label>
                <Input
                  id="amount_due"
                  type="number"
                  min="0"
                  step="0.01"
                  value={form.amount_due}
                  onChange={(e) => setForm((f) => ({ ...f, amount_due: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="days_overdue">Days Overdue</Label>
                <Input
                  id="days_overdue"
                  type="number"
                  min="1"
                  value={form.days_overdue}
                  onChange={(e) => setForm((f) => ({ ...f, days_overdue: e.target.value }))}
                />
              </div>
            </div>
            <Button className="mt-4" disabled={!canCreate || isSubmitting} onClick={handleSubmit}>
              {createRecord.isPending ? "Creating..." : "Create Record"}
            </Button>
          </div>
        </RequirePermission>

        <DataTable
          columns={columns}
          data={data?.items ?? []}
          isLoading={isLoading}
          getRowKey={(row) => String(row.id)}
          emptyTitle="No delinquency records found"
          emptyDescription="Create your first record above."
        />
      </div>
    </RequirePermission>
  );
}
