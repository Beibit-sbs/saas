"use client";

import { useMemo, useState } from "react";
import { Briefcase } from "lucide-react";
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
  useCareerOpportunities,
  useCreateCareerOpportunity,
  useUpdateCareerOpportunityStatus,
} from "@/modules/career_services/hooks";
import type { CareerOpportunity } from "@/modules/career_services/types";

interface CareerFormState {
  student_id: string;
  title: string;
  company: string;
  opportunity_type: string;
  owner_id: string;
  start_date: string;
  notes: string;
}

const EMPTY_FORM: CareerFormState = {
  student_id: "",
  title: "",
  company: "",
  opportunity_type: "internship",
  owner_id: "",
  start_date: "",
  notes: "",
};

const STATUS_COLORS: Record<string, string> = {
  open: "bg-blue-100 text-blue-700",
  in_review: "bg-amber-100 text-amber-700",
  closed: "bg-green-100 text-green-700",
  archived: "bg-gray-100 text-gray-700",
};

export default function CareerServicesPage() {
  const { getHandlers } = useMutationFeedback();
  const [form, setForm] = useState<CareerFormState>(EMPTY_FORM);

  const { data, isLoading, error, refetch } = useCareerOpportunities();
  const createOpportunity = useCreateCareerOpportunity();
  const updateStatus = useUpdateCareerOpportunityStatus();

  const isSubmitting = createOpportunity.isPending || updateStatus.isPending;
  const canCreate = useMemo(() => {
    const studentId = Number(form.student_id);
    return (
      Number.isInteger(studentId) &&
      studentId > 0 &&
      form.title.trim().length > 0 &&
      form.company.trim().length > 0
    );
  }, [form]);

  if (error) {
    return <ErrorState title="Failed to load career opportunities" onRetry={refetch} />;
  }

  const columns: Column<CareerOpportunity>[] = [
    {
      key: "student_id",
      header: "Student ID",
      cell: (row) => <span className="font-medium">{row.student_id}</span>,
      sortValue: (row) => row.student_id,
    },
    {
      key: "title",
      header: "Role",
      cell: (row) => row.title,
      sortValue: (row) => row.title.toLowerCase(),
    },
    {
      key: "company",
      header: "Company",
      cell: (row) => row.company,
      sortValue: (row) => row.company.toLowerCase(),
    },
    {
      key: "opportunity_type",
      header: "Type",
      cell: (row) => row.opportunity_type,
      sortValue: (row) => row.opportunity_type,
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
      width: "150px",
      cell: (row) => (
        <Button
          variant="outline"
          size="sm"
          disabled={isSubmitting || (row.status !== "open" && row.status !== "in_review")}
          onClick={(event) => {
            event.stopPropagation();
            updateStatus.mutate(
              { opportunityId: row.id, payload: { status: "closed" } },
              getHandlers({ successTitle: "Opportunity closed" }),
            );
          }}
        >
          Close
        </Button>
      ),
    },
  ];

  return (
    <RequirePermission permission={PERMISSIONS.CAREER_SERVICES_READ}>
      <div className="space-y-4" data-testid="career-services-page">
        <PageHeader
          title="Career Services"
          description="Manage internships, jobs, and employability pathways for students."
          icon={Briefcase}
        />

        <div className="grid gap-3 rounded-lg border p-4 md:grid-cols-3">
          <div className="space-y-1">
            <Label htmlFor="student-id">Student ID</Label>
            <Input
              id="student-id"
              value={form.student_id}
              onChange={(e) => setForm((prev) => ({ ...prev, student_id: e.target.value }))}
              placeholder="210"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="title">Role title</Label>
            <Input
              id="title"
              value={form.title}
              onChange={(e) => setForm((prev) => ({ ...prev, title: e.target.value }))}
              placeholder="Backend Intern"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="company">Company</Label>
            <Input
              id="company"
              value={form.company}
              onChange={(e) => setForm((prev) => ({ ...prev, company: e.target.value }))}
              placeholder="Acme Labs"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="opportunity-type">Type</Label>
            <Input
              id="opportunity-type"
              value={form.opportunity_type}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, opportunity_type: e.target.value }))
              }
              placeholder="internship"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="owner-id">Owner ID</Label>
            <Input
              id="owner-id"
              value={form.owner_id}
              onChange={(e) => setForm((prev) => ({ ...prev, owner_id: e.target.value }))}
              placeholder="CAREER-1"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="start-date">Start date</Label>
            <Input
              id="start-date"
              value={form.start_date}
              onChange={(e) => setForm((prev) => ({ ...prev, start_date: e.target.value }))}
              placeholder="2026-06-01"
            />
          </div>
          <div className="space-y-1 md:col-span-3">
            <Label htmlFor="notes">Notes</Label>
            <Input
              id="notes"
              value={form.notes}
              onChange={(e) => setForm((prev) => ({ ...prev, notes: e.target.value }))}
              placeholder="Strong portfolio and interview-ready"
            />
          </div>

          <div className="md:col-span-3">
            <Button
              size="sm"
              data-testid="create-opportunity-btn"
              disabled={!canCreate || isSubmitting}
              onClick={() => {
                createOpportunity.mutate(
                  {
                    student_id: Number(form.student_id),
                    title: form.title.trim(),
                    company: form.company.trim(),
                    opportunity_type: form.opportunity_type.trim() as CareerOpportunity["opportunity_type"],
                    owner_id: form.owner_id.trim() || undefined,
                    start_date: form.start_date.trim() || undefined,
                    notes: form.notes.trim() || undefined,
                  },
                  {
                    ...getHandlers({ successTitle: "Opportunity created" }),
                    onSuccess: () => {
                      getHandlers({ successTitle: "Opportunity created" }).onSuccess(undefined);
                      setForm(EMPTY_FORM);
                    },
                  },
                );
              }}
            >
              Create opportunity
            </Button>
          </div>
        </div>

        <DataTable
          columns={columns}
          data={data?.items ?? []}
          isLoading={isLoading}
          getRowKey={(row) => String(row.id)}
          emptyTitle="No career opportunities found."
        />
      </div>
    </RequirePermission>
  );
}
