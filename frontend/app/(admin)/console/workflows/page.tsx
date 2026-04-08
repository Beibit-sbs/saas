"use client";

import { useMemo, useState } from "react";
import { Network } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { DataTable, type Column } from "@/shared/ui/data-table";
import { ErrorState } from "@/shared/ui/error-state";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { PageHeader } from "@/shared/ui/page-header";
import { PermissionGate, RequirePermission } from "@/shared/ui/permission-gate";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useLanguage } from "@/app/components/LanguageProvider";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useStartWorkflow, useWorkflowInstances, useWorkflowTasks } from "@/modules/workflows-admin/hooks";
import type { WorkflowInstance, WorkflowTask } from "@/modules/workflows-admin/types";

export default function WorkflowsPage() {
  const { t } = useLanguage();
  const tAny = (key: string) => t(key as never);
  const { getHandlers } = useMutationFeedback();

  const [workflowKey, setWorkflowKey] = useState("");
  const [entityType, setEntityType] = useState("");
  const [entityId, setEntityId] = useState("");

  const instancesQuery = useWorkflowInstances();
  const tasksQuery = useWorkflowTasks();
  const startWorkflow = useStartWorkflow();

  const parsedEntityId = Number.parseInt(entityId, 10);
  const canStart = useMemo(
    () => workflowKey.trim().length > 0 && entityType.trim().length > 0 && Number.isFinite(parsedEntityId) && parsedEntityId > 0,
    [workflowKey, entityType, parsedEntityId],
  );

  if (instancesQuery.error || tasksQuery.error) {
    return <ErrorState title="Failed to load workflows" onRetry={() => {
      instancesQuery.refetch();
      tasksQuery.refetch();
    }} />;
  }

  const instanceColumns: Column<WorkflowInstance>[] = [
    { key: "id", header: "ID", cell: (r) => String(r.id), sortValue: (r) => r.id },
    { key: "entity_type", header: tAny("workflowEntityType"), cell: (r) => r.entity_type, sortValue: (r) => r.entity_type },
    { key: "entity_id", header: tAny("workflowEntityId"), cell: (r) => String(r.entity_id), sortValue: (r) => r.entity_id },
    { key: "status", header: tAny("status"), cell: (r) => r.status, sortValue: (r) => r.status },
    { key: "started_at", header: tAny("createdAt"), cell: (r) => r.started_at, sortValue: (r) => r.started_at },
  ];

  const taskColumns: Column<WorkflowTask>[] = [
    { key: "id", header: "ID", cell: (r) => String(r.id), sortValue: (r) => r.id },
    { key: "workflow_instance_id", header: "Instance", cell: (r) => String(r.workflow_instance_id), sortValue: (r) => r.workflow_instance_id },
    { key: "title", header: tAny("title"), cell: (r) => r.title, sortValue: (r) => r.title },
    { key: "assignee_ref", header: tAny("assignee"), cell: (r) => r.assignee_ref, sortValue: (r) => r.assignee_ref },
    { key: "status", header: tAny("status"), cell: (r) => r.status, sortValue: (r) => r.status },
  ];

  return (
    <RequirePermission permission={PERMISSIONS.WORKFLOWS_READ}>
    <div className="space-y-6" data-testid="workflows-page">
      <PageHeader title={t("nav.workflows")} description={tAny("workflowsHelp")} icon={Network} />

      <section className="rounded-lg border bg-card p-4 space-y-3">
        <h2 className="text-sm font-semibold">{tAny("workflowStart")}</h2>
        <div className="grid gap-3 md:grid-cols-3">
          <div className="space-y-1.5">
            <Label htmlFor="workflow-key">{tAny("workflowKey")}</Label>
            <Input id="workflow-key" value={workflowKey} onChange={(e) => setWorkflowKey(e.target.value)} placeholder="admissions.review" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="workflow-entity-type">{tAny("workflowEntityType")}</Label>
            <Input id="workflow-entity-type" value={entityType} onChange={(e) => setEntityType(e.target.value)} placeholder="application" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="workflow-entity-id">{tAny("workflowEntityId")}</Label>
            <Input id="workflow-entity-id" type="number" min={1} value={entityId} onChange={(e) => setEntityId(e.target.value)} placeholder="1" />
          </div>
        </div>
        <PermissionGate permission={PERMISSIONS.WORKFLOWS_WRITE}>
          <Button
            disabled={!canStart || startWorkflow.isPending}
            onClick={() =>
              startWorkflow.mutate(
                {
                  workflow_key: workflowKey.trim(),
                  entity_type: entityType.trim(),
                  entity_id: parsedEntityId,
                },
                {
                  ...getHandlers({ successTitle: tAny("workflowStarted") }),
                  onSuccess: () => {
                    getHandlers({ successTitle: tAny("workflowStarted") }).onSuccess(undefined);
                    setWorkflowKey("");
                    setEntityType("");
                    setEntityId("");
                  },
                },
              )
            }
          >
            {tAny("workflowStart")}
          </Button>
        </PermissionGate>
      </section>

      <section className="rounded-lg border bg-card p-4 space-y-3">
        <h2 className="text-sm font-semibold">{tAny("workflowInstances")}</h2>
        <DataTable
          columns={instanceColumns}
          data={instancesQuery.data?.items ?? []}
          isLoading={instancesQuery.isLoading}
          getRowKey={(r) => String(r.id)}
          emptyTitle={tAny("noWorkflowInstances")}
        />
      </section>

      <section className="rounded-lg border bg-card p-4 space-y-3">
        <h2 className="text-sm font-semibold">{tAny("workflowTasks")}</h2>
        <DataTable
          columns={taskColumns}
          data={tasksQuery.data?.items ?? []}
          isLoading={tasksQuery.isLoading}
          getRowKey={(r) => String(r.id)}
          emptyTitle={tAny("noWorkflowTasks")}
        />
      </section>
    </div>
    </RequirePermission>
  );
}
