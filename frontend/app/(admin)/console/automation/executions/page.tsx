"use client";

import { useState } from "react";
import { ClipboardList } from "lucide-react";

import { Badge } from "@/shared/ui/badge";
import { DataTable, type Column } from "@/shared/ui/data-table";
import { ErrorState } from "@/shared/ui/error-state";
import { FilterBar } from "@/shared/ui/filter-bar";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { PERMISSIONS } from "@/shared/config/permissions";
import { formatDate } from "@/shared/utils/format";
import { useAdminAuth } from "@/shared/auth/context";
import { useLanguage } from "@/app/components/LanguageProvider";

import { useAutomationExecutions } from "@/modules/platform/automation/use-executions";
import type { AutomationExecution, AutomationExecutionStatus } from "@/modules/platform/automation/types";

// ---------------------------------------------------------------------------
// Status badge helper
// ---------------------------------------------------------------------------

function buildStatusBadge(t: (key: never) => string): Record<AutomationExecutionStatus, JSX.Element> {
  return {
    pending: <Badge variant="warning">{t("automation.executions.status.pending" as never)}</Badge>,
    completed: <Badge variant="success">{t("automation.executions.status.completed" as never)}</Badge>,
    failed: <Badge variant="destructive">{t("automation.executions.status.failed" as never)}</Badge>,
  };
}

function buildColumns(t: (key: never) => string): Column<AutomationExecution>[] {
  const statusBadge = buildStatusBadge(t);
  return [
    {
      key: "id",
      header: "ID",
      width: "64px",
      cell: (row) => <span className="tabular-nums text-xs text-muted-foreground">{row.id}</span>,
      sortValue: (row) => row.id,
    },
    {
      key: "rule_id",
      header: t("automation.executions.ruleId" as never),
      width: "80px",
      cell: (row) => <span className="tabular-nums text-xs">{row.rule_id}</span>,
      sortValue: (row) => row.rule_id,
    },
    {
      key: "event_id",
      header: t("automation.executions.eventId" as never),
      width: "80px",
      cell: (row) => <span className="tabular-nums text-xs">{row.event_id}</span>,
      sortValue: (row) => row.event_id,
    },
    {
      key: "status",
      header: t("students.filter.status" as never),
      width: "120px",
      cell: (row) => statusBadge[row.status] ?? <Badge variant="outline">{row.status}</Badge>,
      sortValue: (row) => row.status,
    },
    {
      key: "executed_at",
      header: t("automation.executions.executedAt" as never),
      width: "160px",
      cell: (row) => (
        <span className="text-xs text-muted-foreground">{formatDate(row.executed_at)}</span>
      ),
      sortValue: (row) => row.executed_at,
    },
    {
      key: "result",
      header: t("automation.executions.resultError" as never),
      cell: (row) => {
        if (row.error_message) {
          return (
            <span
              className="text-xs text-destructive font-mono truncate max-w-xs block"
              title={row.error_message}
            >
              {row.error_message}
            </span>
          );
        }
        const result = Object.keys(row.result_json ?? {}).length
          ? JSON.stringify(row.result_json)
          : "-";
        return (
          <span
            className="text-xs text-muted-foreground font-mono truncate max-w-xs block"
            title={result}
          >
            {result}
          </span>
        );
      },
    },
  ];
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function AutomationExecutionsPage() {
  const { t } = useLanguage();
  const { user } = useAdminAuth();
  const tenantId = user?.tenantId ?? 0;
  const { data, isLoading, isError, refetch } = useAutomationExecutions(tenantId);
  const [statusFilter, setStatusFilter] = useState("");

  const filterFields = [
    {
      key: "status",
      label: t("students.filter.status"),
      type: "select" as const,
      options: [
        { label: t("automation.executions.status.pending"), value: "pending" },
        { label: t("automation.executions.status.completed"), value: "completed" },
        { label: t("automation.executions.status.failed"), value: "failed" },
      ],
    },
  ];

  const columns = buildColumns(t as never);

  const filtered =
    statusFilter && data ? data.filter((e) => e.status === statusFilter) : (data ?? []);

  return (
    <RequirePermission
      permission={PERMISSIONS.AUTOMATION_READ}
      message={t("automation.executions.permissionDenied")}
    >
      <div className="space-y-6" data-testid="automation-executions-page">
        <PageHeader
          title={t("automation.executions.title")}
          description={t("automation.executions.description")}
          icon={ClipboardList}
        />

        <FilterBar
          fields={filterFields}
          values={{ status: statusFilter }}
          onChange={(_key, value) => setStatusFilter(value)}
          onReset={() => setStatusFilter("")}
        />

        {isError && !isLoading && (
          <ErrorState
            title={t("automation.executions.loadFailedTitle")}
            message={t("automation.executions.loadFailedMessage")}
            onRetry={() => void refetch()}
          />
        )}

        {!isError && (
          <DataTable
            columns={columns}
            data={filtered}
            isLoading={isLoading}
            getRowKey={(row) => String(row.id)}
            emptyTitle={t("automation.executions.emptyTitle")}
            emptyDescription={t("automation.executions.emptyDescription")}
          />
        )}
      </div>
    </RequirePermission>
  );
}
