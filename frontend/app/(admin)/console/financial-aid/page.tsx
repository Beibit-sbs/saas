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
  useCreateFinancialAidRecord,
  useFinancialAidRecords,
  useUpdateFinancialAidStatus,
} from "@/modules/financial_aid/hooks";
import type { FinancialAidRecord } from "@/modules/financial_aid/types";

interface AidFormState {
  student_id: string;
  aid_type: string;
  amount: string;
  currency: string;
  term: string;
  reviewer_id: string;
  notes: string;
}

const EMPTY_FORM: AidFormState = {
  student_id: "",
  aid_type: "scholarship",
  amount: "",
  currency: "USD",
  term: "",
  reviewer_id: "",
  notes: "",
};

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-amber-100 text-amber-700",
  approved: "bg-blue-100 text-blue-700",
  disbursed: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
};

export default function FinancialAidPage() {
  const { getHandlers } = useMutationFeedback();
  const [form, setForm] = useState<AidFormState>(EMPTY_FORM);

  const { data, isLoading, error, refetch } = useFinancialAidRecords();
  const createRecord = useCreateFinancialAidRecord();
  const updateStatus = useUpdateFinancialAidStatus();

  const isSubmitting = createRecord.isPending || updateStatus.isPending;
  const canCreate = useMemo(() => {
    const studentId = Number(form.student_id);
    const amount = Number(form.amount);
    return Number.isInteger(studentId) && studentId > 0 && amount > 0 && form.term.trim().length > 0;
  }, [form]);

  if (error) {
    return <ErrorState title="Failed to load financial aid records" onRetry={refetch} />;
  }

  const columns: Column<FinancialAidRecord>[] = [
    {
      key: "student_id",
      header: "Student ID",
      cell: (row) => <span className="font-medium">{row.student_id}</span>,
      sortValue: (row) => row.student_id,
    },
    {
      key: "aid_type",
      header: "Aid type",
      cell: (row) => row.aid_type,
      sortValue: (row) => row.aid_type,
    },
    {
      key: "amount",
      header: "Amount",
      cell: (row) => `${row.amount} ${row.currency}`,
      sortValue: (row) => row.amount,
    },
    {
      key: "term",
      header: "Term",
      cell: (row) => row.term,
      sortValue: (row) => row.term,
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
      width: "170px",
      cell: (row) => (
        <Button
          variant="outline"
          size="sm"
          disabled={isSubmitting || row.status !== "pending"}
          onClick={(event) => {
            event.stopPropagation();
            updateStatus.mutate(
              { recordId: row.id, payload: { status: "approved" } },
              getHandlers({ successTitle: "Aid approved" }),
            );
          }}
        >
          Approve
        </Button>
      ),
    },
  ];

  return (
    <RequirePermission permission={PERMISSIONS.FINANCIAL_AID_READ}>
      <div className="space-y-4" data-testid="financial-aid-page">
        <PageHeader
          title="Scholarship & Financial Aid"
          description="Manage scholarship and aid awards lifecycle by student and term."
          icon={Wallet}
        />

        <div className="grid gap-3 rounded-lg border p-4 md:grid-cols-3">
          <div className="space-y-1">
            <Label htmlFor="student-id">Student ID</Label>
            <Input
              id="student-id"
              value={form.student_id}
              onChange={(e) => setForm((prev) => ({ ...prev, student_id: e.target.value }))}
              placeholder="310"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="aid-type">Aid type</Label>
            <Input
              id="aid-type"
              value={form.aid_type}
              onChange={(e) => setForm((prev) => ({ ...prev, aid_type: e.target.value }))}
              placeholder="scholarship"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="amount">Amount</Label>
            <Input
              id="amount"
              value={form.amount}
              onChange={(e) => setForm((prev) => ({ ...prev, amount: e.target.value }))}
              placeholder="2500"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="currency">Currency</Label>
            <Input
              id="currency"
              value={form.currency}
              onChange={(e) => setForm((prev) => ({ ...prev, currency: e.target.value }))}
              placeholder="USD"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="term">Term</Label>
            <Input
              id="term"
              value={form.term}
              onChange={(e) => setForm((prev) => ({ ...prev, term: e.target.value }))}
              placeholder="2026-FALL"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="reviewer-id">Reviewer ID</Label>
            <Input
              id="reviewer-id"
              value={form.reviewer_id}
              onChange={(e) => setForm((prev) => ({ ...prev, reviewer_id: e.target.value }))}
              placeholder="AID-1"
            />
          </div>
          <div className="space-y-1 md:col-span-3">
            <Label htmlFor="notes">Notes</Label>
            <Input
              id="notes"
              value={form.notes}
              onChange={(e) => setForm((prev) => ({ ...prev, notes: e.target.value }))}
              placeholder="Merit-based scholarship"
            />
          </div>

          <div className="md:col-span-3">
            <Button
              size="sm"
              data-testid="create-aid-btn"
              disabled={!canCreate || isSubmitting}
              onClick={() => {
                createRecord.mutate(
                  {
                    student_id: Number(form.student_id),
                    aid_type: form.aid_type.trim() as FinancialAidRecord["aid_type"],
                    amount: Number(form.amount),
                    currency: form.currency.trim().toUpperCase(),
                    term: form.term.trim(),
                    reviewer_id: form.reviewer_id.trim() || undefined,
                    notes: form.notes.trim() || undefined,
                  },
                  {
                    ...getHandlers({ successTitle: "Aid record created" }),
                    onSuccess: () => {
                      getHandlers({ successTitle: "Aid record created" }).onSuccess(undefined);
                      setForm(EMPTY_FORM);
                    },
                  },
                );
              }}
            >
              Create aid record
            </Button>
          </div>
        </div>

        <DataTable
          columns={columns}
          data={data?.items ?? []}
          isLoading={isLoading}
          getRowKey={(row) => String(row.id)}
          emptyTitle="No aid records found."
        />
      </div>
    </RequirePermission>
  );
}
