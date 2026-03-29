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

import { useAutomationExecutions } from "@/modules/platform/automation/use-executions";
import type { AutomationExecution, AutomationExecutionStatus } from "@/modules/platform/automation/types";

// ---------------------------------------------------------------------------
// Status badge helper
// ---------------------------------------------------------------------------

const STATUS_BADGE: Record<AutomationExecutionStatus, JSX.Element> = {
  pending: <Badge variant="warning">Pending</Badge>,
  completed: <Badge variant="success">Completed</Badge>,
  failed: <Badge variant="destructive">Failed</Badge>,
};

// ---------------------------------------------------------------------------
// Filter fields
// ---------------------------------------------------------------------------

const FILTER_FIELDS = [
  {
    key: "status",
    label: "Status",
    type: "select" as const,
    options: [
      { label: "Pending", value: "pending" },
      { label: "Completed", value: "completed" },
      { label: "Failed", value: "failed" },
    ],
  },
];

// ---------------------------------------------------------------------------
// Columns
// ---------------------------------------------------------------------------

const COLUMNS: Column<AutomationExecution>[] = [
  {
    key: "id",
    header: "ID",
    width: "64px",
    cell: (row) => <span className="tabular-nums text-xs text-muted-foreground">{row.id}</span>,
    sortValue: (row) => row.id,
  },
  {
    key: "rule_id",
    header: "Rule ID",
    width: "80px",
    cell: (row) => <span className="tabular-nums text-xs">{row.rule_id}</span>,
    sortValue: (row) => row.rule_id,
  },
  {
    key: "event_id",
    header: "Event ID",
    width: "80px",
    cell: (row) => <span className="tabular-nums text-xs">{row.event_id}</span>,
    sortValue: (row) => row.event_id,
  },
  {
    key: "status",
    header: "Status",
    width: "120px",
    cell: (row) => STATUS_BADGE[row.status] ?? <Badge variant="outline">{row.status}</Badge>,
    sortValue: (row) => row.status,
  },
  {
    key: "executed_at",
    header: "Executed At",
    width: "160px",
    cell: (row) => (
      <span className="text-xs text-muted-foreground">{formatDate(row.executed_at)}</span>
    ),
    sortValue: (row) => row.executed_at,
  },
  {
    key: "result",
    header: "Result / Error",
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
        : "—";
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

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function AutomationExecutionsPage() {
  const { user } = useAdminAuth();
  const tenantId = user?.tenantId ?? 0;
  const { data, isLoading, isError, refetch } = useAutomationExecutions(tenantId);
  const [statusFilter, setStatusFilter] = useState("");

  const filtered =
    statusFilter && data ? data.filter((e) => e.status === statusFilter) : (data ?? []);

  return (
    <RequirePermission
      permission={PERMISSIONS.AUTOMATION_READ}
      message="You need automation.read permission to view execution logs."
    >
      <div className="space-y-6" data-testid="automation-executions-page">
        <PageHeader
          title="Execution Log"
          description="Audit trail for all automation rule executions."
          icon={ClipboardList}
        />

        <FilterBar
          fields={FILTER_FIELDS}
          values={{ status: statusFilter }}
          onChange={(_key, value) => setStatusFilter(value)}
          onReset={() => setStatusFilter("")}
        />

        {isError && !isLoading && (
          <ErrorState
            title="Failed to load execution log"
            message="Could not fetch automation executions."
            onRetry={() => void refetch()}
          />
        )}

        {!isError && (
          <DataTable
            columns={COLUMNS}
            data={filtered}
            isLoading={isLoading}
            getRowKey={(row) => String(row.id)}
            emptyTitle="No executions"
            emptyDescription="Executions appear here once automation rules are triggered by events."
          />
        )}
      </div>
    </RequirePermission>
  );
}
