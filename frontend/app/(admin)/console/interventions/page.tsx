"use client";

import { useMemo, useState, useCallback } from "react";
import { AlertTriangle, Download } from "lucide-react";
import { PageHeader } from "@/shared/ui/page-header";
import { DataTable, type Column } from "@/shared/ui/data-table";
import { FilterBar } from "@/shared/ui/filter-bar";
import { StatusBadge } from "@/shared/ui/status-badge";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { DrawerPanel } from "@/shared/ui/drawer-panel";
import { DetailList } from "@/shared/ui/detail-list";
import { ErrorState } from "@/shared/ui/error-state";
import { PermissionGate } from "@/shared/ui/permission-gate";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/ui/select";
import { useTableQueryState } from "@/shared/hooks/use-table-query-state";
import { useDetailDrawer } from "@/shared/hooks/use-detail-drawer";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { PERMISSIONS } from "@/shared/config/permissions";
import { formatRelative } from "@/shared/utils/format";
import { useLanguage } from "@/app/components/LanguageProvider";
import {
  useAddInterventionAction,
  useAssignInterventionCase,
  useInterventionActions,
  useInterventionCase,
  useInterventionCases,
  useTakeInterventionCase,
  useUpdateInterventionStatus,
  useStudentName,
} from "@/modules/platform/interventions/hooks";
import { InterventionsSummaryStats } from "@/modules/platform/interventions/summary-stats";
import type { InterventionCase, InterventionAction, InterventionActionType } from "@/modules/platform/interventions/types";

function SeverityBadge({ severity }: { severity: InterventionCase["severity"] }) {
  const { t } = useLanguage();
  if (severity === "high") return <Badge variant="destructive">{t("intervention.severity.high")}</Badge>;
  if (severity === "medium") return <Badge variant="warning">{t("intervention.severity.medium")}</Badge>;
  return <Badge variant="success">{t("intervention.severity.low")}</Badge>;
}

export default function InterventionsPage() {
  const { t } = useLanguage();
  const { getHandlers } = useMutationFeedback();

  const FILTER_FIELDS = [
    {
      key: "status",
      label: t("intervention.filter.status"),
      type: "select" as const,
      options: [
        { label: t("intervention.status.open"), value: "open" },
        { label: t("intervention.status.in_progress"), value: "in_progress" },
        { label: t("intervention.status.resolved"), value: "resolved" },
        { label: t("intervention.status.closed"), value: "closed" },
      ],
    },
    {
      key: "severity",
      label: t("intervention.filter.severity"),
      type: "select" as const,
      options: [
        { label: t("intervention.severity.high"), value: "high" },
        { label: t("intervention.severity.medium"), value: "medium" },
        { label: t("intervention.severity.low"), value: "low" },
      ],
    },
    { key: "assignee_ref", label: t("intervention.filter.assignee"), type: "text" as const, placeholder: "registrar.team" },
    {
      key: "overdue_only",
      label: t("intervention.filter.overdue"),
      type: "select" as const,
      options: [{ label: t("intervention.filter.overdueOnly"), value: "true" }],
    },
  ];
  const table = useTableQueryState({
    filterKeys: ["status", "severity", "assignee_ref", "overdue_only"] as const,
    defaultPageSize: 20,
    defaultSort: { key: "updated", direction: "desc" },
  });
  const detail = useDetailDrawer({ paramKey: "case" });

  const listQuery = useInterventionCases({
    page: table.page,
    page_size: table.pageSize,
    status: table.filters.status || undefined,
    severity: table.filters.severity || undefined,
    assignee_ref: table.filters.assignee_ref || undefined,
    overdue_only: table.filters.overdue_only === "true" ? true : undefined,
  });

  const selectedId = detail.selectedId ?? "";
  const caseQuery = useInterventionCase(selectedId);
  const actionsQuery = useInterventionActions(selectedId, 30);

  const assignMutation = useAssignInterventionCase();
  const takeMutation = useTakeInterventionCase();
  const statusMutation = useUpdateInterventionStatus();
  const addActionMutation = useAddInterventionAction();

  const [assigneeType, setAssigneeType] = useState<"user" | "group">("user");
  const [assigneeRef, setAssigneeRef] = useState("");
  const [dueAt, setDueAt] = useState<Date | undefined>(undefined);
  const [nextStatus, setNextStatus] = useState<InterventionCase["status"]>("in_progress");
  const [actionType, setActionType] = useState<InterventionActionType>("note");
  const [actionDescription, setActionDescription] = useState("");

  const rows = Array.isArray(listQuery.data?.items) ? listQuery.data.items : [];
  const selectedCase = caseQuery.data ?? null;
  const selectedActions = Array.isArray(actionsQuery.data?.items) ? actionsQuery.data.items : [];
  const studentInfo = useStudentName(selectedCase?.student_profile_id ?? null);

  const handleExport = useCallback(() => {
    const params = new URLSearchParams();
    if (table.filters.status) params.set("status", table.filters.status);
    if (table.filters.severity) params.set("severity", table.filters.severity);
    if (table.filters.assignee_ref) params.set("assignee_ref", table.filters.assignee_ref);
    if (table.filters.overdue_only === "true") params.set("overdue_only", "true");
    const url = `/api/admin/interventions/cases/export${params.size > 0 ? `?${params.toString()}` : ""}`;
    window.open(url, "_blank", "noopener,noreferrer");
  }, [table.filters]);

  const columns: Column<InterventionCase>[] = useMemo(
    () => [
      {
        key: "id",
        header: t("intervention.col.case"),
        width: "120px",
        cell: (row) => <code className="text-xs">#{row.id}</code>,
        sortValue: (row) => Number(row.id),
      },
      {
        key: "student",
        header: t("intervention.col.student"),
        cell: (row) => (
          <span className="font-mono text-xs text-muted-foreground">#{row.student_profile_id}</span>
        ),
        sortValue: (row) => Number(row.student_profile_id),
      },
      {
        key: "severity",
        header: t("intervention.col.severity"),
        cell: (row) => <SeverityBadge severity={row.severity} />,
        sortValue: (row) => row.severity,
      },
      {
        key: "status",
        header: t("intervention.col.status"),
        cell: (row) => <StatusBadge status={row.status.replace("_", "-")} />,
        sortValue: (row) => row.status,
      },
      {
        key: "assignee",
        header: t("intervention.col.assignee"),
        cell: (row) => (row.assignee_ref ? `${row.assignee_type}:${row.assignee_ref}` : t("intervention.unassigned")),
        sortValue: (row) => row.assignee_ref ?? "",
      },
      {
        key: "due",
        header: t("intervention.col.due"),
        cell: (row) => (row.due_at ? formatRelative(row.due_at) : "—"),
        sortValue: (row) => row.due_at ?? "",
      },
      {
        key: "updated",
        header: t("intervention.col.updated"),
        cell: (row) => formatRelative(row.updated_at),
        sortValue: (row) => row.updated_at,
      },
    ],
    [t],
  );

  if (listQuery.error) {
    return <ErrorState title="Failed to load intervention cases" onRetry={listQuery.refetch} />;
  }

  return (
    <div className="space-y-4">
      <PageHeader
        title={t("nav.interventions")}
        description={t("console.interventions.description")}
        icon={AlertTriangle}
        actions={
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="mr-2 h-4 w-4" />
            {t("intervention.action.exportCsv")}
          </Button>
        }
      />

      <InterventionsSummaryStats />

      <FilterBar fields={FILTER_FIELDS} values={table.filters} onChange={table.setFilter} onReset={table.resetFilters} />

      <DataTable
        columns={columns}
        data={rows}
        isLoading={listQuery.isLoading}
        getRowKey={(row) => row.id}
        pagination={{ page: table.page, pageSize: table.pageSize, total: listQuery.data?.total ?? 0 }}
        pageSizeOptions={[10, 20, 50]}
        onPageChange={table.setPage}
        onPageSizeChange={table.setPageSize}
        sort={table.sort}
        onSortChange={table.setSort}
        onRowClick={(row) => detail.open(row.id)}
        emptyTitle={t("intervention.empty.title")}
        emptyDescription={t("intervention.empty.description")}
      />

      <DrawerPanel
        open={detail.isOpen}
        onClose={detail.close}
        title={selectedCase ? `${t("intervention.drawer.caseTitle")} #${selectedCase.id}` : t("intervention.drawer.defaultTitle")}
        description={selectedCase ? `${t("intervention.drawer.ownerLabel")}: ${selectedCase.owner_type}:${selectedCase.owner_ref}` : t("intervention.drawer.defaultDescription")}
        width="lg"
      >
        {detail.isOpen && caseQuery.isLoading ? (
          <p className="text-sm text-muted-foreground">{t("intervention.drawer.loading")}</p>
        ) : selectedCase ? (
          <div className="space-y-5">
            <DetailList
              items={[
                { label: t("intervention.col.severity"), value: <SeverityBadge severity={selectedCase.severity} /> },
                { label: t("intervention.col.status"), value: <StatusBadge status={selectedCase.status.replace("_", "-")} /> },
                {
                  label: t("intervention.field.studentProfile"),
                  value: studentInfo.isLoading
                    ? <span className="text-muted-foreground text-xs">{t("intervention.field.studentLoading")}</span>
                    : studentInfo.name
                      ? (
                        <span>
                          {studentInfo.name}
                          {studentInfo.email && (
                            <span className="ml-1 text-xs text-muted-foreground">({studentInfo.email})</span>
                          )}
                        </span>
                      )
                      : <span className="font-mono text-xs">#{selectedCase.student_profile_id}</span>,
                },
                { label: t("intervention.col.assignee"), value: selectedCase.assignee_ref ? `${selectedCase.assignee_type}:${selectedCase.assignee_ref}` : t("intervention.unassigned") },
                { label: t("intervention.field.version"), value: String(selectedCase.version) },
                { label: t("intervention.col.updated"), value: formatRelative(selectedCase.updated_at) },
                {
                  label: t("intervention.field.snapshot"),
                  value: selectedCase.recommendation_snapshot ? (
                    <pre className="overflow-x-auto rounded bg-muted p-3 text-xs">{selectedCase.recommendation_snapshot}</pre>
                  ) : (
                    "—"
                  ),
                },
              ]}
            />

            <PermissionGate permission={PERMISSIONS.JOBS_WRITE}>
              <div className="space-y-4 rounded border p-4">
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={takeMutation.isPending}
                    onClick={() =>
                      takeMutation.mutate(
                        { id: selectedCase.id, expectedVersion: selectedCase.version },
                        getHandlers({ successTitle: t("intervention.action.takeCaseSuccess") }),
                      )
                    }
                  >
                    {t("intervention.action.takeCase")}
                  </Button>
                </div>

                <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                  <div className="space-y-1.5">
                    <Label>{t("intervention.field.assigneeType")}</Label>
                    <Select value={assigneeType} onValueChange={(value: "user" | "group") => setAssigneeType(value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="user">{t("intervention.field.assigneeUser")}</SelectItem>
                        <SelectItem value="group">{t("intervention.field.assigneeGroup")}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1.5 md:col-span-2">
                    <Label>{t("intervention.field.assigneeRef")}</Label>
                    <Input value={assigneeRef} onChange={(event) => setAssigneeRef(event.target.value)} placeholder="registrar.team" />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label>{t("intervention.field.dueDate")}</Label>
                  <Input
                    type="date"
                    value={dueAt ? dueAt.toISOString().slice(0, 10) : ""}
                    onChange={(e) => setDueAt(e.target.value ? new Date(e.target.value) : undefined)}
                    className="block"
                  />
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  disabled={!assigneeRef.trim() || assignMutation.isPending}
                  onClick={() => {
                    const handlers = getHandlers<InterventionCase>({ successTitle: t("intervention.action.assignSuccess") });
                    assignMutation.mutate(
                      {
                        id: selectedCase.id,
                        body: {
                          assignee_type: assigneeType,
                          assignee_ref: assigneeRef.trim(),
                          due_at: dueAt ? dueAt.toISOString() : undefined,
                          expected_version: selectedCase.version,
                        },
                      },
                      {
                        ...handlers,
                        onSuccess: (result) => {
                          handlers.onSuccess(result);
                          setAssigneeRef("");
                          setDueAt(undefined);
                        },
                      },
                    );
                  }}
                >
                  {t("intervention.action.assign")}
                </Button>

                <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                  <div className="space-y-1.5">
                    <Label>{t("intervention.action.setStatus")}</Label>
                    <Select value={nextStatus} onValueChange={(value: InterventionCase["status"]) => setNextStatus(value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="open">{t("intervention.status.open")}</SelectItem>
                        <SelectItem value="in_progress">{t("intervention.status.in_progress")}</SelectItem>
                        <SelectItem value="resolved">{t("intervention.status.resolved")}</SelectItem>
                        <SelectItem value="closed">{t("intervention.status.closed")}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1.5 md:col-span-2 flex items-end">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={statusMutation.isPending}
                      onClick={() =>
                        statusMutation.mutate(
                          {
                            id: selectedCase.id,
                            body: { status: nextStatus, expected_version: selectedCase.version },
                          },
                          getHandlers({ successTitle: t("intervention.action.updateStatusSuccess") }),
                        )
                      }
                    >
                      {t("intervention.action.updateStatus")}
                    </Button>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label>{t("intervention.action.actionType")}</Label>
                  <Select value={actionType} onValueChange={(value: InterventionActionType) => setActionType(value)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="note">{t("intervention.actionType.note")}</SelectItem>
                      <SelectItem value="consultation_scheduled">{t("intervention.actionType.consultation_scheduled")}</SelectItem>
                      <SelectItem value="notification_sent">{t("intervention.actionType.notification_sent")}</SelectItem>
                      <SelectItem value="plan_updated">{t("intervention.actionType.plan_updated")}</SelectItem>
                      <SelectItem value="assignment">{t("intervention.actionType.assignment")}</SelectItem>
                      <SelectItem value="status_change">{t("intervention.actionType.status_change")}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label>{t("intervention.action.addNote")}</Label>
                  <Input
                    value={actionDescription}
                    onChange={(event) => setActionDescription(event.target.value)}
                    placeholder={t("intervention.action.notePlaceholder")}
                  />
                </div>
                <Button
                  size="sm"
                  disabled={!actionDescription.trim() || addActionMutation.isPending}
                  onClick={() => {
                    const handlers = getHandlers<{ case: InterventionCase; action: InterventionAction }>({
                      successTitle: t("intervention.action.addActionSuccess"),
                    });
                    addActionMutation.mutate(
                      {
                        id: selectedCase.id,
                        body: {
                          action_type: actionType,
                          description: actionDescription.trim(),
                          expected_version: selectedCase.version,
                        },
                      },
                      {
                        ...handlers,
                        onSuccess: (result) => {
                          handlers.onSuccess(result);
                          setActionDescription("");
                        },
                      },
                    );
                  }}
                >
                  {t("intervention.action.addAction")}
                </Button>
              </div>
            </PermissionGate>

            <div className="space-y-2">
              <h4 className="text-sm font-medium">{t("intervention.actions.title")}</h4>
              {actionsQuery.isLoading ? (
                <p className="text-sm text-muted-foreground">{t("intervention.actions.loading")}</p>
              ) : selectedActions.length === 0 ? (
                <p className="text-sm text-muted-foreground">{t("intervention.actions.empty")}</p>
              ) : (
                <div className="space-y-2">
                  {selectedActions.map((entry) => (
                    <div key={entry.id} className="rounded border p-3">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-medium">{entry.action_type}</span>
                        <span className="text-xs text-muted-foreground">{formatRelative(entry.created_at)}</span>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">{entry.description}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        actor: {entry.actor_type}:{entry.actor_ref}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ) : (
          <ErrorState title={t("intervention.drawer.notFoundTitle")} message={t("intervention.drawer.notFoundMessage")} />
        )}
      </DrawerPanel>
    </div>
  );
}
