"use client";

import { useState, useCallback } from "react";
import { Play, CheckCircle2, SkipForward, XCircle, Activity } from "lucide-react";
import { PageHeader } from "@/shared/ui/page-header";
import { DataTable, type Column } from "@/shared/ui/data-table";
import { FilterBar } from "@/shared/ui/filter-bar";
import { StatusBadge } from "@/shared/ui/status-badge";
import { Button } from "@/shared/ui/button";
import { Label } from "@/shared/ui/label";
import { Input } from "@/shared/ui/input";
import { DrawerPanel } from "@/shared/ui/drawer-panel";
import { DetailList } from "@/shared/ui/detail-list";
import { ErrorState } from "@/shared/ui/error-state";
import { PERMISSIONS } from "@/shared/config/permissions";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import { useTableQueryState } from "@/shared/hooks/use-table-query-state";
import { useDetailDrawer } from "@/shared/hooks/use-detail-drawer";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { formatRelative } from "@/shared/utils/format";
import { useLanguage } from "@/app/components/LanguageProvider";
import {
  usePlaybooks,
  usePlaybookExecutions,
  usePlaybookExecution,
  useStartExecution,
  useAbandonExecution,
  useCompleteStep,
  useSkipStep,
} from "@/modules/platform/interventions/playbook-hooks";
import type {
  PlaybookExecution,
  PlaybookExecutionStatus,
  PlaybookStepExecution,
  PlaybookStepExecutionStatus,
} from "@/modules/platform/interventions/playbook-types";

function StepExecutionRow({
  step,
  executionId,
  onComplete,
  onSkip,
  executionActive,
}: {
  step: PlaybookStepExecution;
  executionId: number;
  onComplete: (stepId: number) => void;
  onSkip: (stepId: number) => void;
  executionActive: boolean;
}) {
  return (
    <li className="flex items-center justify-between gap-3 py-1.5 text-sm border-b last:border-0">
      <div className="flex items-center gap-2 min-w-0">
        <StatusBadge status={step.status} />
        <span className="truncate">Step #{step.id}</span>
        {step.outcome_note && (
          <span className="text-muted-foreground italic truncate text-xs">
            {step.outcome_note}
          </span>
        )}
      </div>
      {executionActive && step.status === "pending" && (
        <RequirePermission permission={PERMISSIONS.INTERVENTIONS_EXECUTE_PLAYBOOK}>
          <div className="flex gap-1 flex-none">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onComplete(step.id)}
              title="Complete step"
            >
              <CheckCircle2 className="h-4 w-4 text-green-600" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onSkip(step.id)}
              title="Skip step"
            >
              <SkipForward className="h-4 w-4 text-muted-foreground" />
            </Button>
          </div>
        </RequirePermission>
      )}
    </li>
  );
}

const FILTER_FIELDS = [
  {
    key: "status",
    label: "Status",
    type: "select" as const,
    options: [
      { label: "Pending", value: "pending" },
      { label: "In Progress", value: "in_progress" },
      { label: "Completed", value: "completed" },
      { label: "Abandoned", value: "abandoned" },
    ],
  },
];

export default function PlaybookExecutionsPage() {
  const { getHandlers } = useMutationFeedback();

  const { filters, setFilter } = useTableQueryState({
    filterKeys: FILTER_FIELDS.map((field) => field.key),
  });
  const { selectedId, open, close } = useDetailDrawer();
  const [showStart, setShowStart] = useState(false);
  const [startPlaybookId, setStartPlaybookId] = useState<string>("");
  const [abandonReason, setAbandonReason] = useState("");
  const [abandonTargetId, setAbandonTargetId] = useState<number | null>(null);

  const status =
    (filters.status as PlaybookExecutionStatus | undefined) || undefined;

  const { data, isLoading, isError } = usePlaybookExecutions({ status });
  const { data: detail } = usePlaybookExecution(
    selectedId !== null ? Number(selectedId) : null,
  );
  const { data: playbooksData } = usePlaybooks({ enabled_only: true });

  const startExecution = useStartExecution();
  const abandonExecution = useAbandonExecution();
  const completeStep = useCompleteStep();
  const skipStep = useSkipStep();

  const handleStart = useCallback(() => {
    if (!startPlaybookId) return;
    startExecution.mutate(
      { playbook_id: Number(startPlaybookId) },
      {
        ...getHandlers({ successTitle: "Execution started" }),
        onSuccess: () => {
          setShowStart(false);
          setStartPlaybookId("");
        },
      },
    );
  }, [startPlaybookId, startExecution, getHandlers]);

  const handleAbandon = useCallback(() => {
    if (!abandonTargetId || !abandonReason.trim()) return;
    abandonExecution.mutate(
      { id: abandonTargetId, payload: { abandon_reason: abandonReason.trim() } },
      {
        ...getHandlers({ successTitle: "Execution abandoned" }),
        onSuccess: () => {
          setAbandonTargetId(null);
          setAbandonReason("");
        },
      },
    );
  }, [abandonTargetId, abandonReason, abandonExecution, getHandlers]);

  const handleCompleteStep = useCallback(
    (executionId: number, stepExecutionId: number) => {
      completeStep.mutate(
        { executionId, stepExecutionId, payload: {} },
        getHandlers({ successTitle: "Step completed" }),
      );
    },
    [completeStep, getHandlers],
  );

  const handleSkipStep = useCallback(
    (executionId: number, stepExecutionId: number) => {
      skipStep.mutate(
        { executionId, stepExecutionId, payload: {} },
        getHandlers({ successTitle: "Step skipped" }),
      );
    },
    [skipStep, getHandlers],
  );

  const columns: Column<PlaybookExecution>[] = [
    {
      key: "id",
      header: "ID",
      cell: (e) => (
        <button
          className="font-mono text-xs hover:underline"
          onClick={() => open(String(e.id))}
        >
          #{e.id}
        </button>
      ),
    },
    {
      key: "playbook_id",
      header: "Playbook",
      cell: (e) => `#${e.playbook_id}`,
    },
    {
      key: "status",
      header: "Status",
      cell: (e) => (
        <StatusBadge status={e.status} />
      ),
    },
    {
      key: "triggered_by",
      header: "Trigger",
      cell: (e) => e.triggered_by,
    },
    {
      key: "started_at",
      header: "Started",
      cell: (e) => formatRelative(e.started_at),
    },
    {
      key: "abandon",
      header: "",
      cell: (e) =>
        e.status === "in_progress" || e.status === "pending" ? (
          <RequirePermission permission={PERMISSIONS.INTERVENTIONS_EXECUTE_PLAYBOOK}>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setAbandonTargetId(e.id)}
              title="Abandon"
            >
              <XCircle className="h-4 w-4 text-destructive" />
            </Button>
          </RequirePermission>
        ) : null,
    },
  ];

  if (isError) return <ErrorState />;

  const items = data?.items ?? [];
  const playbooks = playbooksData?.items ?? [];

  const executionActive =
    detail?.status === "in_progress" || detail?.status === "pending";

  return (
    <div className="space-y-6">
      <PageHeader
        icon={Activity}
        title="Playbook Executions"
        description="Active and completed playbook runs"
        actions={
          <RequirePermission permission={PERMISSIONS.INTERVENTIONS_EXECUTE_PLAYBOOK}>
            <Button size="sm" onClick={() => setShowStart(true)}>
              <Play className="h-4 w-4 mr-1" />
              Start Execution
            </Button>
          </RequirePermission>
        }
      />

      <FilterBar fields={FILTER_FIELDS} values={filters} onChange={setFilter} />

      <DataTable
        columns={columns}
        data={items}
        getRowKey={(row) => String(row.id)}
        isLoading={isLoading}
        emptyDescription="No executions found."
      />

      {/* Start execution drawer */}
      <DrawerPanel
        open={showStart}
        onClose={() => {
          setShowStart(false);
          setStartPlaybookId("");
        }}
        title="Start Playbook Execution"
      >
        <div className="space-y-4 p-4">
          <div className="space-y-1">
            <Label>Playbook</Label>
            <Select value={startPlaybookId} onValueChange={setStartPlaybookId}>
              <SelectTrigger>
                <SelectValue placeholder="Select a playbook…" />
              </SelectTrigger>
              <SelectContent>
                {playbooks.map((p) => (
                  <SelectItem key={p.id} value={String(p.id)}>
                    {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button
            onClick={handleStart}
            disabled={!startPlaybookId || startExecution.isPending}
            className="w-full"
          >
            {startExecution.isPending ? "Starting…" : "Start"}
          </Button>
        </div>
      </DrawerPanel>

      {/* Abandon drawer */}
      <DrawerPanel
        open={abandonTargetId !== null}
        onClose={() => {
          setAbandonTargetId(null);
          setAbandonReason("");
        }}
        title="Abandon Execution"
      >
        <div className="space-y-4 p-4">
          <div className="space-y-1">
            <Label htmlFor="abandon-reason">Reason *</Label>
            <Input
              id="abandon-reason"
              value={abandonReason}
              onChange={(e) => setAbandonReason(e.target.value)}
              placeholder="Reason for abandoning…"
            />
          </div>
          <Button
            variant="destructive"
            onClick={handleAbandon}
            disabled={!abandonReason.trim() || abandonExecution.isPending}
            className="w-full"
          >
            {abandonExecution.isPending ? "Abandoning…" : "Abandon Execution"}
          </Button>
        </div>
      </DrawerPanel>

      {/* Detail drawer with step execution controls */}
      <DrawerPanel
        open={selectedId !== null}
        onClose={close}
        title={detail ? `Execution #${detail.id}` : "Execution"}
      >
        {detail && (
          <div className="space-y-4 p-4">
            <DetailList
              items={[
                { label: "Playbook", value: `#${detail.playbook_id}` },
                { label: "Status", value: detail.status },
                { label: "Trigger", value: detail.triggered_by },
                {
                  label: "Case",
                  value: detail.case_id ? `#${detail.case_id}` : "—",
                },
                {
                  label: "Student",
                  value: detail.student_profile_id
                    ? `#${detail.student_profile_id}`
                    : "—",
                },
                { label: "Started", value: formatRelative(detail.started_at) },
                {
                  label: "Completed",
                  value: detail.completed_at
                    ? formatRelative(detail.completed_at)
                    : "—",
                },
                {
                  label: "ΔScore",
                  value:
                    detail.outcome_delta_score !== null
                      ? String(detail.outcome_delta_score)
                      : "—",
                },
              ]}
            />

            <div>
              <p className="text-sm font-medium mb-2">
                Steps ({detail.step_executions.length})
              </p>
              <ul className="divide-y">
                {detail.step_executions.map((se) => (
                  <StepExecutionRow
                    key={se.id}
                    step={se}
                    executionId={detail.id}
                    executionActive={executionActive ?? false}
                    onComplete={(stepId) =>
                      handleCompleteStep(detail.id, stepId)
                    }
                    onSkip={(stepId) => handleSkipStep(detail.id, stepId)}
                  />
                ))}
              </ul>
            </div>
          </div>
        )}
      </DrawerPanel>
    </div>
  );
}
