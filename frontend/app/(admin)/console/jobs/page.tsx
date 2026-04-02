"use client";

import { useState } from "react";
import { PageHeader } from "@/shared/ui/page-header";
import { DataTable, Column } from "@/shared/ui/data-table";
import { FilterBar } from "@/shared/ui/filter-bar";
import { StatusBadge } from "@/shared/ui/status-badge";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { DrawerPanel } from "@/shared/ui/drawer-panel";
import { DetailList } from "@/shared/ui/detail-list";
import { ErrorState } from "@/shared/ui/error-state";
import { PermissionGate } from "@/shared/ui/permission-gate";
import { useDetailDrawer } from "@/shared/hooks/use-detail-drawer";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useTableQueryState } from "@/shared/hooks/use-table-query-state";
import { useJobs, useRetryJob, useCancelJob, useTriggerJob } from "@/modules/platform/jobs/hooks";
import { Job } from "@/modules/platform/jobs/types";
import { formatRelative } from "@/shared/utils/format";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useLanguage } from "@/app/components/LanguageProvider";
import { Cog } from "lucide-react";

const FILTER_FIELDS = [
  {
    key: "status",
    label: "Status",
    type: "select" as const,
    options: [
      { label: "Queued", value: "queued" },
      { label: "Running", value: "running" },
      { label: "Completed", value: "completed" },
      { label: "Failed", value: "failed" },
      { label: "Cancelled", value: "cancelled" },
    ],
  },
  { key: "job_type", label: "Type", type: "text" as const, placeholder: "Filter type…" },
];

export default function JobsPage() {
  const { t } = useLanguage();
  const table = useTableQueryState({ filterKeys: ["status", "job_type"] as const, defaultPageSize: 20, defaultSort: { key: "created", direction: "desc" } });
  const detail = useDetailDrawer({ paramKey: "job" });
  const { getHandlers } = useMutationFeedback();
  const [runDrawerOpen, setRunDrawerOpen] = useState(false);
  const [jobType, setJobType] = useState("");
  const [tenantId, setTenantId] = useState("");

  const { data, isLoading, error, refetch } = useJobs({ page: table.page, page_size: table.pageSize, status: table.filters.status, job_type: table.filters.job_type });
  const retry = useRetryJob();
  const cancel = useCancelJob();
  const trigger = useTriggerJob();
  const rows = Array.isArray(data?.items) ? data.items : [];
  const selectedJob = rows.find((item) => item.id === detail.selectedId) ?? null;

  if (error) {
    return <ErrorState title="Failed to load jobs" onRetry={refetch} />;
  }

  const columns: Column<Job>[] = [
    { key: "id", header: "ID", width: "100px", cell: (r) => <code className="text-xs">{r.id.slice(0, 8)}</code>, sortValue: (r) => r.id },
    { key: "type", header: "Type", cell: (r) => r.job_type, sortValue: (r) => r.job_type.toLowerCase() },
    { key: "tenant", header: "University", cell: (r) => r.tenant_id ?? "global", sortValue: (r) => r.tenant_id ?? "global" },
    { key: "status", header: "Status", cell: (r) => <StatusBadge status={r.status} />, sortValue: (r) => r.status },
    {
      key: "progress",
      header: "Progress",
      cell: (r) =>
        r.progress !== null ? (
          <div className="flex items-center gap-2">
            <div className="h-1.5 w-24 rounded bg-muted overflow-hidden">
              <div className="h-full bg-primary" style={{ width: `${r.progress}%` }} />
            </div>
            <span className="text-xs">{r.progress}%</span>
          </div>
        ) : (
          "—"
        ),
      sortValue: (r) => r.progress ?? -1,
    },
    { key: "created", header: "Created", cell: (r) => formatRelative(r.created_at), sortValue: (r) => r.created_at },
    {
      key: "actions",
      header: "",
      width: "130px",
      cell: (r) => (
        <div className="flex gap-1 justify-end" onClick={(event) => event.stopPropagation()}>
          <PermissionGate permission={PERMISSIONS.JOBS_WRITE}>
            {r.status === "failed" && (
              <Button
                variant="outline"
                size="sm"
                disabled={retry.isPending}
                onClick={() =>
                  retry.mutate(r.id, {
                    ...getHandlers({ successTitle: "Job queued for retry" }),
                  })
                }
              >
                Retry
              </Button>
            )}
            {(r.status === "queued" || r.status === "running") && (
              <Button
                variant="outline"
                size="sm"
                disabled={cancel.isPending}
                onClick={() =>
                  cancel.mutate(r.id, {
                    ...getHandlers({ successTitle: "Job cancelled" }),
                  })
                }
              >
                Cancel
              </Button>
            )}
          </PermissionGate>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title={t("nav.jobs")}
        description={t("console.jobs.description")}
        icon={Cog}
        actions={
          <PermissionGate permission={PERMISSIONS.JOBS_WRITE}>
            <Button size="sm" onClick={() => setRunDrawerOpen(true)}>
              Run once
            </Button>
          </PermissionGate>
        }
      />

      <FilterBar
        fields={FILTER_FIELDS}
        values={table.filters}
        onChange={table.setFilter}
        onReset={table.resetFilters}
      />

      <DataTable
        columns={columns}
        data={rows}
        isLoading={isLoading}
        getRowKey={(r) => r.id}
        pagination={{ page: table.page, pageSize: table.pageSize, total: data?.total ?? 0 }}
        pageSizeOptions={[10, 20, 50]}
        onPageChange={table.setPage}
        onPageSizeChange={table.setPageSize}
        sort={table.sort}
        onSortChange={table.setSort}
        onRowClick={(row) => detail.open(row.id)}
        emptyTitle="No jobs found"
      />

      <DrawerPanel
        open={detail.isOpen}
        onClose={detail.close}
        title={selectedJob ? `Job ${selectedJob.id.slice(0, 8)}` : "Job details"}
        description={selectedJob ? selectedJob.job_type : "Select a job from the table."}
        width="lg"
      >
        {selectedJob ? (
          <DetailList
            items={[
              { label: "Status", value: <StatusBadge status={selectedJob.status} /> },
              { label: "University", value: selectedJob.tenant_id ?? "global" },
              { label: "Progress", value: selectedJob.progress !== null ? `${selectedJob.progress}%` : "—" },
              { label: "Created", value: formatRelative(selectedJob.created_at) },
              { label: "Started", value: selectedJob.started_at ? formatRelative(selectedJob.started_at) : "—" },
              { label: "Completed", value: selectedJob.completed_at ? formatRelative(selectedJob.completed_at) : "—" },
              { label: "Error", value: selectedJob.error_message ?? "—" },
              { label: "Metadata", value: <pre className="overflow-x-auto rounded bg-muted p-3 text-xs">{JSON.stringify(selectedJob.metadata, null, 2)}</pre> },
            ]}
          />
        ) : (
          <ErrorState title="Job not found" message="The selected job is not present on this page of results." />
        )}
      </DrawerPanel>

      <DrawerPanel
        open={runDrawerOpen}
        onClose={() => setRunDrawerOpen(false)}
        title="Run job once"
        description="Trigger a one-off background job without leaving the queue view."
      >
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="job-type">Job type</Label>
            <Input id="job-type" value={jobType} onChange={(event) => setJobType(event.target.value)} placeholder="sync_grades" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="tenant-id">Tenant ID</Label>
            <Input id="tenant-id" value={tenantId} onChange={(event) => setTenantId(event.target.value)} placeholder="Optional tenant scope" />
          </div>
          <PermissionGate permission={PERMISSIONS.JOBS_WRITE}>
            <Button
              disabled={!jobType.trim() || trigger.isPending}
              onClick={() =>
                trigger.mutate(
                  { job_type: jobType.trim(), tenant_id: tenantId.trim() || undefined },
                  {
                    ...getHandlers({ successTitle: (job) => `Job ${job.job_type} queued` }),
                    onSuccess: (job) => {
                      getHandlers<Job>({ successTitle: (result) => `Job ${result.job_type} queued` }).onSuccess(job);
                      setRunDrawerOpen(false);
                      setJobType("");
                      setTenantId("");
                    },
                  },
                )
              }
            >
              Run job
            </Button>
          </PermissionGate>
        </div>
      </DrawerPanel>
    </div>
  );
}
