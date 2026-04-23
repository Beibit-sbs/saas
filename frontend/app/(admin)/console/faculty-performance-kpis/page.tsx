"use client";

import { useMemo, useState } from "react";
import { GaugeCircle } from "lucide-react";
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
  useCreateFacultyKpi,
  useFacultyKpis,
  useUpdateFacultyKpiStatus,
} from "@/modules/faculty-performance-kpis/hooks";
import type { FacultyKpi, FacultyKpiStatus } from "@/modules/faculty-performance-kpis/types";

interface KpiFormState {
  faculty_id: string;
  name: string;
  department_id: string;
  kpi_period: string;
  teaching_score: string;
  research_score: string;
  service_score: string;
  overall_score: string;
}

const EMPTY_FORM: KpiFormState = {
  faculty_id: "",
  name: "",
  department_id: "",
  kpi_period: "",
  teaching_score: "",
  research_score: "",
  service_score: "",
  overall_score: "",
};

const STATUS_COLORS: Record<FacultyKpiStatus, string> = {
  satisfactory: "bg-green-100 text-green-700",
  needs_improvement: "bg-amber-100 text-amber-700",
  on_probation: "bg-red-100 text-red-700",
};

const NEXT_STATUSES: Record<FacultyKpiStatus, FacultyKpiStatus[]> = {
  satisfactory: ["needs_improvement"],
  needs_improvement: ["satisfactory", "on_probation"],
  on_probation: ["needs_improvement"],
};

export default function FacultyPerformanceKpisPage() {
  const { getHandlers } = useMutationFeedback();
  const [form, setForm] = useState<KpiFormState>(EMPTY_FORM);

  const { data, isLoading, error, refetch } = useFacultyKpis();
  const createKpi = useCreateFacultyKpi();
  const updateStatus = useUpdateFacultyKpiStatus();

  const isSubmitting = createKpi.isPending || updateStatus.isPending;

  const canCreate = useMemo(() => {
    const t = Number(form.teaching_score);
    const r = Number(form.research_score);
    const s = Number(form.service_score);
    const o = Number(form.overall_score);
    const inRange = (v: number) => !Number.isNaN(v) && v >= 0 && v <= 100;

    return (
      form.faculty_id.trim().length > 0
      && form.name.trim().length > 0
      && form.department_id.trim().length > 0
      && form.kpi_period.trim().length > 0
      && inRange(t)
      && inRange(r)
      && inRange(s)
      && inRange(o)
    );
  }, [form]);

  if (error) {
    return <ErrorState title="Failed to load faculty KPI records" onRetry={refetch} />;
  }

  const columns: Column<FacultyKpi>[] = [
    {
      key: "faculty_id",
      header: "Faculty ID",
      cell: (row) => <span className="font-mono text-xs">{row.faculty_id}</span>,
      sortValue: (row) => row.faculty_id,
    },
    {
      key: "name",
      header: "Name",
      cell: (row) => <span className="font-medium">{row.name}</span>,
      sortValue: (row) => row.name.toLowerCase(),
    },
    {
      key: "department_id",
      header: "Department",
      cell: (row) => row.department_id,
      sortValue: (row) => row.department_id,
    },
    {
      key: "kpi_period",
      header: "Period",
      cell: (row) => row.kpi_period,
      sortValue: (row) => row.kpi_period,
    },
    {
      key: "overall_score",
      header: "Overall",
      cell: (row) => row.overall_score.toFixed(1),
      sortValue: (row) => row.overall_score,
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
                    { kpiId: row.id, payload: { status: next } },
                    getHandlers(`KPI moved to ${next}`),
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

    createKpi.mutate(
      {
        faculty_id: form.faculty_id.trim(),
        name: form.name.trim(),
        department_id: form.department_id.trim(),
        kpi_period: form.kpi_period.trim(),
        teaching_score: Number(form.teaching_score),
        research_score: Number(form.research_score),
        service_score: Number(form.service_score),
        overall_score: Number(form.overall_score),
        status: "satisfactory",
      },
      {
        ...getHandlers("KPI record created"),
        onSuccess: (...args) => {
          setForm(EMPTY_FORM);
          getHandlers("KPI record created").onSuccess?.(...args);
        },
      },
    );
  };

  return (
    <RequirePermission permission={PERMISSIONS.FACULTY_READ}>
      <div className="space-y-8">
        <PageHeader
          title="Faculty Performance KPIs"
          subtitle="Track teaching, research, and service outcomes with workflow status"
          icon={GaugeCircle}
        />

        <RequirePermission permission={PERMISSIONS.FACULTY_WRITE}>
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-lg font-semibold mb-4">Add KPI Record</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <Label htmlFor="faculty_id">Faculty ID</Label>
                <Input
                  id="faculty_id"
                  placeholder="FAC-001"
                  value={form.faculty_id}
                  onChange={(e) => setForm((f) => ({ ...f, faculty_id: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  placeholder="Dr. Jane Doe"
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="department_id">Department</Label>
                <Input
                  id="department_id"
                  placeholder="DEPT-CS"
                  value={form.department_id}
                  onChange={(e) => setForm((f) => ({ ...f, department_id: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="kpi_period">KPI Period</Label>
                <Input
                  id="kpi_period"
                  placeholder="2026-Q2"
                  value={form.kpi_period}
                  onChange={(e) => setForm((f) => ({ ...f, kpi_period: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="teaching_score">Teaching Score</Label>
                <Input
                  id="teaching_score"
                  type="number"
                  min="0"
                  max="100"
                  value={form.teaching_score}
                  onChange={(e) => setForm((f) => ({ ...f, teaching_score: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="research_score">Research Score</Label>
                <Input
                  id="research_score"
                  type="number"
                  min="0"
                  max="100"
                  value={form.research_score}
                  onChange={(e) => setForm((f) => ({ ...f, research_score: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="service_score">Service Score</Label>
                <Input
                  id="service_score"
                  type="number"
                  min="0"
                  max="100"
                  value={form.service_score}
                  onChange={(e) => setForm((f) => ({ ...f, service_score: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="overall_score">Overall Score</Label>
                <Input
                  id="overall_score"
                  type="number"
                  min="0"
                  max="100"
                  value={form.overall_score}
                  onChange={(e) => setForm((f) => ({ ...f, overall_score: e.target.value }))}
                />
              </div>
            </div>
            <Button className="mt-4" disabled={!canCreate || isSubmitting} onClick={handleSubmit}>
              {createKpi.isPending ? "Creating..." : "Create KPI Record"}
            </Button>
          </div>
        </RequirePermission>

        <DataTable
          columns={columns}
          data={data?.items ?? []}
          isLoading={isLoading}
          getRowKey={(row) => String(row.id)}
          emptyTitle="No KPI records found"
          emptyDescription="Create your first KPI record above."
        />
      </div>
    </RequirePermission>
  );
}
