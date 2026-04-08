"use client";

import { ShieldAlert } from "lucide-react";
import { PageHeader } from "@/shared/ui/page-header";
import { FilterBar } from "@/shared/ui/filter-bar";
import { DataTable, Column } from "@/shared/ui/data-table";
import { ErrorState } from "@/shared/ui/error-state";
import { Button } from "@/shared/ui/button";
import { StatusBadge } from "@/shared/ui/status-badge";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { useTableQueryState } from "@/shared/hooks/use-table-query-state";
import { AccessDenied } from "@/shared/ui/permission-gate";
import { PERMISSIONS } from "@/shared/config/permissions";
import { formatDate, truncate } from "@/shared/utils/format";
import { useAuditEvents } from "@/modules/audit/hooks";
import type { AuditEvent } from "@/modules/audit/types";
import { useLanguage } from "@/app/components/LanguageProvider";

const FILTER_FIELDS = [
  { key: "actor", label: "Actor", type: "text" as const, placeholder: "Filter by actor" },
  { key: "action", label: "Action", type: "text" as const, placeholder: "Filter by action" },
  { key: "entity", label: "Entity", type: "text" as const, placeholder: "Filter by entity" },
  {
    key: "result",
    label: "Result",
    type: "select" as const,
    options: [
      { label: "Success", value: "success" },
      { label: "Failed", value: "failed" },
    ],
  },
  { key: "correlation_id", label: "Correlation", type: "text" as const, placeholder: "Filter by correlation ID" },
  { key: "since", label: "Since", type: "text" as const, placeholder: "2026-04-01T00:00:00Z" },
  { key: "tenant_id", label: "Tenant", type: "text" as const, placeholder: "Tenant ID" },
];

function buildExportUrl(format: "json" | "csv", filters: Record<string, string>): string {
  const params = new URLSearchParams({ format, limit: "500" });
  for (const [key, value] of Object.entries(filters)) {
    if (value.trim()) params.set(key, value.trim());
  }
  return `/api/bff/admin/audit/export?${params.toString()}`;
}

export default function AuditPage() {
  const { t } = useLanguage();
  const tAny = (key: string) => t(key as never);
  const { hasPermission } = usePermissions();
  const table = useTableQueryState({
    filterKeys: ["actor", "action", "entity", "result", "correlation_id", "since", "tenant_id"] as const,
    defaultSort: { key: "timestamp", direction: "desc" },
  });

  const { data, isLoading, error, refetch } = useAuditEvents({
    actor: table.filters.actor || undefined,
    action: table.filters.action || undefined,
    entity: table.filters.entity || undefined,
    result: table.filters.result || undefined,
    correlation_id: table.filters.correlation_id || undefined,
    since: table.filters.since || undefined,
    tenant_id: table.filters.tenant_id || undefined,
    limit: 100,
  });

  if (!hasPermission(PERMISSIONS.AUDIT_READ)) return <AccessDenied />;

  if (error) {
    return <ErrorState title="Unable to load audit events" onRetry={refetch} />;
  }

  const columns: Column<AuditEvent>[] = [
    { key: "timestamp", header: "Timestamp", cell: (row) => formatDate(row.timestamp), sortValue: (row) => row.timestamp },
    { key: "actor", header: "Actor", cell: (row) => row.actor, sortValue: (row) => row.actor.toLowerCase() },
    { key: "action", header: "Action", cell: (row) => row.action, sortValue: (row) => row.action.toLowerCase() },
    { key: "entity", header: "Entity", cell: (row) => row.entity, sortValue: (row) => row.entity.toLowerCase() },
    { key: "result", header: "Result", cell: (row) => <StatusBadge status={row.result} />, sortValue: (row) => row.result.toLowerCase() },
    { key: "tenant", header: "Tenant", cell: (row) => String(row.tenant_id), sortValue: (row) => row.tenant_id },
    { key: "path", header: "Path", cell: (row) => truncate(row.path, 32), sortValue: (row) => row.path.toLowerCase() },
    { key: "correlation", header: "Correlation", cell: (row) => truncate(row.correlation_id, 20), sortValue: (row) => row.correlation_id.toLowerCase() },
  ];

  return (
    <div className="space-y-4" data-testid="audit-page">
      <PageHeader
        title={t("nav.audit")}
        description="Inspect admin actions, filter by actor or tenant, and export evidence for compliance review."
        icon={ShieldAlert}
        actions={(
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => window.open(buildExportUrl("json", table.filters), "_blank", "noopener,noreferrer")}>
              Export JSON
            </Button>
            <Button variant="outline" size="sm" onClick={() => window.open(buildExportUrl("csv", table.filters), "_blank", "noopener,noreferrer")}>
              Export CSV
            </Button>
          </div>
        )}
      />

      <FilterBar
        fields={FILTER_FIELDS}
        values={table.filters}
        onChange={table.setFilter}
        onReset={table.resetFilters}
      />

      <DataTable
        columns={columns}
        data={data?.events ?? []}
        isLoading={isLoading}
        getRowKey={(row) => row.event_id}
        sort={table.sort}
        onSortChange={table.setSort}
        emptyTitle={tAny("noAuditEvents")}
      />
    </div>
  );
}
