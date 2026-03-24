"use client";

import { PageHeader } from "@/shared/ui/page-header";
import { DataTable, Column } from "@/shared/ui/data-table";
import { FilterBar } from "@/shared/ui/filter-bar";
import { StatusBadge } from "@/shared/ui/status-badge";
import { Button } from "@/shared/ui/button";
import { ConfirmActionDialog } from "@/shared/ui/confirm-action-dialog";
import { DrawerPanel } from "@/shared/ui/drawer-panel";
import { DetailList } from "@/shared/ui/detail-list";
import { ErrorState } from "@/shared/ui/error-state";
import { PermissionGate } from "@/shared/ui/permission-gate";
import { useDetailDrawer } from "@/shared/hooks/use-detail-drawer";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useTableQueryState } from "@/shared/hooks/use-table-query-state";
import { useTenants, useSuspendTenant, useActivateTenant } from "@/modules/platform/tenants/hooks";
import { Tenant } from "@/modules/platform/tenants/types";
import { formatDate, formatNumber } from "@/shared/utils/format";
import { PERMISSIONS } from "@/shared/config/permissions";
import { Building2, Plus } from "lucide-react";

const FILTER_FIELDS = [
  { key: "search", label: "Search", type: "text" as const, placeholder: "Name or slug…" },
  {
    key: "status",
    label: "Status",
    type: "select" as const,
    options: [
      { label: "Active", value: "active" },
      { label: "Suspended", value: "suspended" },
      { label: "Trial", value: "trial" },
      { label: "Archived", value: "archived" },
    ],
  },
];

export default function TenantsPage() {
  const table = useTableQueryState({ filterKeys: ["search", "status"] as const, defaultPageSize: 20, defaultSort: { key: "created", direction: "desc" } });
  const detail = useDetailDrawer({ paramKey: "tenant" });
  const { getHandlers } = useMutationFeedback();

  const { data, isLoading, error, refetch } = useTenants({
    page: table.page,
    page_size: table.pageSize,
    search: table.filters.search,
    status: table.filters.status,
  });

  const suspend = useSuspendTenant();
  const activate = useActivateTenant();
  const selectedTenant = data?.items.find((item) => item.id === detail.selectedId) ?? null;

  if (error) {
    return <ErrorState title="Failed to load tenants" onRetry={refetch} />;
  }

  const columns: Column<Tenant>[] = [
    { key: "name", header: "Name", cell: (r) => <span className="font-medium">{r.display_name}</span>, sortValue: (r) => r.display_name.toLowerCase() },
    { key: "slug", header: "Slug", cell: (r) => <code className="text-xs">{r.slug}</code>, sortValue: (r) => r.slug.toLowerCase() },
    { key: "plan", header: "Plan", cell: (r) => r.plan, sortValue: (r) => r.plan.toLowerCase() },
    { key: "status", header: "Status", cell: (r) => <StatusBadge status={r.status} />, sortValue: (r) => r.status },
    {
      key: "students",
      header: "Students",
      cell: (r) => `${formatNumber(r.current_students)} / ${formatNumber(r.max_students)}`,
      sortValue: (r) => r.current_students,
    },
    { key: "created", header: "Created", cell: (r) => formatDate(r.created_at), sortValue: (r) => r.created_at },
    {
      key: "actions",
      header: "",
      width: "120px",
      cell: (r) => (
        <div className="flex gap-1 justify-end" onClick={(event) => event.stopPropagation()}>
          <PermissionGate permission={PERMISSIONS.TENANTS_WRITE}>
            {r.status === "active" ? (
              <ConfirmActionDialog
                title="Suspend tenant?"
                description={`${r.display_name} will lose access immediately.`}
                variant="destructive"
                onConfirm={() =>
                  suspend.mutate(r.id, {
                    ...getHandlers({ successTitle: "Tenant suspended" }),
                  })
                }
                trigger={
                  <Button variant="outline" size="sm" disabled={suspend.isPending}>
                    Suspend
                  </Button>
                }
              />
            ) : (
              <Button
                variant="outline"
                size="sm"
                disabled={activate.isPending}
                onClick={() =>
                  activate.mutate(r.id, {
                    ...getHandlers({ successTitle: "Tenant activated" }),
                  })
                }
              >
                Activate
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
        title="Tenants"
        description="Manage platform tenants"
        icon={Building2}
        actions={
          <Button size="sm">
            <Plus className="h-4 w-4 mr-1" />
            New Tenant
          </Button>
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
        data={data?.items ?? []}
        isLoading={isLoading}
        getRowKey={(r) => r.id}
        pagination={{ page: table.page, pageSize: table.pageSize, total: data?.total ?? 0 }}
        pageSizeOptions={[10, 20, 50]}
        onPageChange={table.setPage}
        onPageSizeChange={table.setPageSize}
        sort={table.sort}
        onSortChange={table.setSort}
        onRowClick={(row) => detail.open(row.id)}
        emptyTitle="No tenants found"
        emptyDescription="Create the first tenant to get started."
      />

      <DrawerPanel
        open={detail.isOpen}
        onClose={detail.close}
        title={selectedTenant?.display_name ?? "Tenant details"}
        description={selectedTenant ? `Operational summary for ${selectedTenant.slug}` : "Select a tenant from the table."}
        width="md"
      >
        {selectedTenant ? (
          <DetailList
            items={[
              { label: "Slug", value: <code className="text-xs">{selectedTenant.slug}</code> },
              { label: "Status", value: <StatusBadge status={selectedTenant.status} /> },
              { label: "Plan", value: selectedTenant.plan },
              { label: "Student capacity", value: `${formatNumber(selectedTenant.current_students)} / ${formatNumber(selectedTenant.max_students)}` },
              { label: "Created", value: formatDate(selectedTenant.created_at) },
              { label: "Updated", value: formatDate(selectedTenant.updated_at) },
            ]}
          />
        ) : (
          <ErrorState title="Tenant not found" message="The selected tenant is not present on this page of results." />
        )}
      </DrawerPanel>
    </div>
  );
}
