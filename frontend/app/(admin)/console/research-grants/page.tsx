"use client";

import { useMemo, useState } from "react";
import { FlaskConical } from "lucide-react";
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
  useResearchGrants,
  useCreateResearchGrant,
  useUpdateResearchGrantStatus,
} from "@/modules/research-grants/hooks";
import type { ResearchGrant } from "@/modules/research-grants/types";

interface GrantFormState {
  grant_code: string;
  title: string;
  pi_faculty_id: string;
  deadline: string;
  funding_amount: string;
}

const EMPTY_FORM: GrantFormState = {
  grant_code: "",
  title: "",
  pi_faculty_id: "",
  deadline: "",
  funding_amount: "",
};

const STATUS_COLORS: Record<string, string> = {
  planned: "bg-gray-100 text-gray-700",
  active: "bg-blue-100 text-blue-700",
  submitted: "bg-amber-100 text-amber-700",
  delayed: "bg-red-100 text-red-700",
  closed: "bg-green-100 text-green-700",
};

const NEXT_STATUSES: Record<string, string[]> = {
  planned: ["active"],
  active: ["submitted", "delayed"],
  submitted: ["active", "closed"],
  delayed: ["active", "closed"],
  closed: [],
};

export default function ResearchGrantsPage() {
  const { getHandlers } = useMutationFeedback();
  const [form, setForm] = useState<GrantFormState>(EMPTY_FORM);

  const { data, isLoading, error, refetch } = useResearchGrants();
  const createGrant = useCreateResearchGrant();
  const updateStatus = useUpdateResearchGrantStatus();

  const isSubmitting = createGrant.isPending || updateStatus.isPending;
  const canCreate = useMemo(() => {
    const amount = Number(form.funding_amount);
    return (
      form.grant_code.trim().length > 0 &&
      form.title.trim().length > 0 &&
      form.pi_faculty_id.trim().length > 0 &&
      form.deadline.length > 0 &&
      !Number.isNaN(amount) &&
      amount >= 0
    );
  }, [form]);

  if (error) {
    return <ErrorState title="Failed to load research grants" onRetry={refetch} />;
  }

  const columns: Column<ResearchGrant>[] = [
    {
      key: "grant_code",
      header: "Grant Code",
      cell: (row) => <span className="font-mono text-xs">{row.grant_code}</span>,
      sortValue: (row) => row.grant_code,
    },
    {
      key: "title",
      header: "Title",
      cell: (row) => <span className="font-medium">{row.title}</span>,
      sortValue: (row) => row.title.toLowerCase(),
    },
    {
      key: "pi_faculty_id",
      header: "Principal Investigator",
      cell: (row) => row.pi_faculty_id,
      sortValue: (row) => row.pi_faculty_id,
    },
    {
      key: "deadline",
      header: "Deadline",
      cell: (row) => row.deadline,
      sortValue: (row) => row.deadline,
    },
    {
      key: "funding_amount",
      header: "Funding",
      cell: (row) => `$${row.funding_amount.toLocaleString()}`,
      sortValue: (row) => row.funding_amount,
    },
    {
      key: "status",
      header: "Status",
      cell: (row) => (
        <Badge className={STATUS_COLORS[row.status] ?? ""}>{row.status}</Badge>
      ),
      sortValue: (row) => row.status,
    },
    {
      key: "actions",
      header: "Actions",
      cell: (row) => {
        const nexts = NEXT_STATUSES[row.status] ?? [];
        if (nexts.length === 0) return null;
        return (
          <div className="flex gap-1 flex-wrap">
            {nexts.map((next) => (
              <Button
                key={next}
                variant="outline"
                size="sm"
                disabled={isSubmitting}
                onClick={() =>
                  updateStatus.mutate(
                    { grantId: row.id, payload: { status: next as ResearchGrant["status"] } },
                    getHandlers({ successTitle: `Grant moved to ${next}` }),
                  )
                }
              >
                → {next}
              </Button>
            ))}
          </div>
        );
      },
    },
  ];

  const handleSubmit = () => {
    if (!canCreate) return;
    createGrant.mutate(
      {
        grant_code: form.grant_code.trim(),
        title: form.title.trim(),
        pi_faculty_id: form.pi_faculty_id.trim(),
        deadline: form.deadline,
        funding_amount: Number(form.funding_amount),
        status: "planned",
      },
      {
        ...getHandlers({ successTitle: "Grant created" }),
        onSuccess: (...args) => {
          setForm(EMPTY_FORM);
          getHandlers({ successTitle: "Grant created" }).onSuccess?.(args[0]);
        },
      },
    );
  };

  return (
    <RequirePermission permission={PERMISSIONS.RESEARCH_READ}>
      <div className="space-y-8">
        <PageHeader
          title="Research Grants Pipeline"
          description="Manage grant applications, funding, and pipeline stages"
          icon={FlaskConical}
        />

        <RequirePermission permission={PERMISSIONS.RESEARCH_WRITE}>
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-lg font-semibold mb-4">Add Grant</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label htmlFor="grant_code">Grant Code</Label>
                <Input
                  id="grant_code"
                  placeholder="GR-2026-001"
                  value={form.grant_code}
                  onChange={(e) => setForm((f) => ({ ...f, grant_code: e.target.value }))}
                />
              </div>
              <div className="md:col-span-2">
                <Label htmlFor="title">Title</Label>
                <Input
                  id="title"
                  placeholder="Grant title"
                  value={form.title}
                  onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="pi_faculty_id">Principal Investigator ID</Label>
                <Input
                  id="pi_faculty_id"
                  placeholder="FAC-001"
                  value={form.pi_faculty_id}
                  onChange={(e) => setForm((f) => ({ ...f, pi_faculty_id: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="deadline">Deadline</Label>
                <Input
                  id="deadline"
                  type="date"
                  value={form.deadline}
                  onChange={(e) => setForm((f) => ({ ...f, deadline: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="funding_amount">Funding Amount ($)</Label>
                <Input
                  id="funding_amount"
                  type="number"
                  min="0"
                  placeholder="0"
                  value={form.funding_amount}
                  onChange={(e) => setForm((f) => ({ ...f, funding_amount: e.target.value }))}
                />
              </div>
            </div>
            <Button
              className="mt-4"
              disabled={!canCreate || isSubmitting}
              onClick={handleSubmit}
            >
              {createGrant.isPending ? "Creating…" : "Create Grant"}
            </Button>
          </div>
        </RequirePermission>

        <DataTable
          columns={columns}
          data={data?.items ?? []}
          isLoading={isLoading}
          getRowKey={(row) => String(row.id)}
          emptyDescription="No grants found. Create your first grant above."
        />
      </div>
    </RequirePermission>
  );
}
