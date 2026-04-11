"use client";

import { useState } from "react";
import { PageHeader } from "@/shared/ui/page-header";
import { DataTable, Column } from "@/shared/ui/data-table";
import { FilterBar } from "@/shared/ui/filter-bar";
import { StatusBadge } from "@/shared/ui/status-badge";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { ConfirmActionDialog } from "@/shared/ui/confirm-action-dialog";
import { DrawerPanel } from "@/shared/ui/drawer-panel";
import { DetailList } from "@/shared/ui/detail-list";
import { ErrorState } from "@/shared/ui/error-state";
import { PermissionGate, RequirePermission } from "@/shared/ui/permission-gate";
import { useDetailDrawer } from "@/shared/hooks/use-detail-drawer";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useTableQueryState } from "@/shared/hooks/use-table-query-state";
import { useTenants, useSuspendTenant, useActivateTenant, useCreateTenant, useDeleteTenant, useUpdateTenant } from "@/modules/platform/tenants/hooks";
import { Tenant } from "@/modules/platform/tenants/types";
import { formatDate, formatNumber } from "@/shared/utils/format";
import { normalizeApiError } from "@/shared/utils/api-error";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useLanguage } from "@/app/components/LanguageProvider";
import { Building2, Plus } from "lucide-react";

export default function TenantsPage() {
  const { t } = useLanguage();
  const [createOpen, setCreateOpen] = useState(false);
  const [slug, setSlug] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [plan, setPlan] = useState("1");
  const [createError, setCreateError] = useState<string | null>(null);
  const [editDisplayName, setEditDisplayName] = useState("");
  const [editPlan, setEditPlan] = useState("1");
  const [updateError, setUpdateError] = useState<string | null>(null);

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
  const removeTenant = useDeleteTenant();
  const createTenant = useCreateTenant();
  const updateTenant = useUpdateTenant();
  const rows = Array.isArray(data?.items) ? data.items : [];
  const selectedTenant = rows.find((item) => item.id === detail.selectedId) ?? null;

  const canCreate = slug.trim().length > 0 && displayName.trim().length > 0;

  const filterFields = [
    { key: "search", label: t("tenants.searchLabel"), type: "text" as const, placeholder: t("tenants.searchPlaceholder") },
    {
      key: "status",
      label: t("tenants.statusLabel"),
      type: "select" as const,
      options: [
        { label: t("tenants.status.active"), value: "active" },
        { label: t("tenants.status.inactive"), value: "inactive" },
        { label: t("tenants.status.suspended"), value: "suspended" },
        { label: t("tenants.status.trial"), value: "trial" },
        { label: t("tenants.status.archived"), value: "archived" },
      ],
    },
  ];

  if (error) {
    return <ErrorState title={t("tenants.loadFailed")} onRetry={refetch} />;
  }

  const columns: Column<Tenant>[] = [
    { key: "name", header: t("tenants.name"), cell: (r) => <span className="font-medium">{r.display_name}</span>, sortValue: (r) => r.display_name.toLowerCase() },
    { key: "slug", header: t("tenants.slug"), cell: (r) => <code className="text-xs">{r.slug}</code>, sortValue: (r) => r.slug.toLowerCase() },
    { key: "plan", header: t("tenants.plan"), cell: (r) => r.plan, sortValue: (r) => r.plan.toLowerCase() },
    { key: "status", header: t("tenants.statusLabel"), cell: (r) => <StatusBadge status={r.status} />, sortValue: (r) => r.status },
    {
      key: "students",
      header: t("tenants.students"),
      cell: (r) => `${formatNumber(r.current_students)} / ${formatNumber(r.max_students)}`,
      sortValue: (r) => r.current_students,
    },
    { key: "created", header: t("tenants.created"), cell: (r) => formatDate(r.created_at), sortValue: (r) => r.created_at },
    {
      key: "actions",
      header: "",
      width: "120px",
      cell: (r) => (
        <div className="flex gap-1 justify-end" onClick={(event) => event.stopPropagation()}>
          <PermissionGate permission={PERMISSIONS.TENANTS_WRITE}>
            {r.status === "active" ? (
              <ConfirmActionDialog
                title={t("tenants.suspendConfirmTitle")}
                description={t("tenants.suspendConfirmDescription").replace("{name}", r.display_name)}
                variant="destructive"
                onConfirm={() =>
                  suspend.mutate(r.id, {
                    ...getHandlers({ successTitle: t("tenants.suspended") }),
                  })
                }
                trigger={
                  <Button variant="outline" size="sm" disabled={suspend.isPending}>
                    {t("tenants.suspend")}
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
                    ...getHandlers({ successTitle: t("tenants.activated") }),
                  })
                }
              >
                {t("tenants.activate")}
              </Button>
            )}
            {r.id !== "1" ? (
              <ConfirmActionDialog
                title={t("tenants.deleteConfirmTitle")}
                description={t("tenants.deleteConfirmDescription").replace("{name}", r.display_name)}
                variant="destructive"
                onConfirm={() =>
                  removeTenant.mutate(r.id, {
                    ...getHandlers({ successTitle: t("tenants.deleted") }),
                  })
                }
                trigger={
                  <Button variant="destructive" size="sm" disabled={removeTenant.isPending}>
                    {t("tenants.delete")}
                  </Button>
                }
              />
            ) : null}
          </PermissionGate>
        </div>
      ),
    },
  ];

  return (
    <RequirePermission permission={PERMISSIONS.TENANTS_READ}>
    <div className="space-y-4">
      <PageHeader
        title={t("nav.tenants")}
        description={t("console.tenants.description")}
        icon={Building2}
        actions={
          <PermissionGate permission={PERMISSIONS.TENANTS_WRITE}>
            <Button
              size="sm"
              onClick={() => {
                setCreateError(null);
                setCreateOpen(true);
              }}
            >
              <Plus className="h-4 w-4 mr-1" />
              {t("tenants.new")}
            </Button>
          </PermissionGate>
        }
      />

      <FilterBar
        fields={filterFields}
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
        onRowClick={(row) => {
          setEditDisplayName(row.display_name);
          setEditPlan(row.plan);
          setUpdateError(null);
          detail.open(row.id);
        }}
        emptyTitle={t("tenants.emptyTitle")}
        emptyDescription={t("tenants.emptyDescription")}
      />

      <DrawerPanel
        open={detail.isOpen}
        onClose={detail.close}
        title={selectedTenant?.display_name ?? t("tenants.detailsTitle")}
        description={selectedTenant ? t("tenants.operationalSummary").replace("{slug}", selectedTenant.slug) : t("tenants.selectFromTable")}
        width="md"
      >
        {selectedTenant ? (
          <div className="space-y-4">
            <DetailList
              items={[
                { label: t("tenants.slug"), value: <code className="text-xs">{selectedTenant.slug}</code> },
                { label: t("tenants.statusLabel"), value: <StatusBadge status={selectedTenant.status} /> },
                { label: t("tenants.studentCapacity"), value: `${formatNumber(selectedTenant.current_students)} / ${formatNumber(selectedTenant.max_students)}` },
                { label: t("tenants.created"), value: formatDate(selectedTenant.created_at) },
                { label: t("tenants.updated"), value: formatDate(selectedTenant.updated_at) },
              ]}
            />

            <PermissionGate permission={PERMISSIONS.TENANTS_WRITE}>
              <div className="space-y-1.5">
                <Label htmlFor="tenant-edit-name">{t("tenants.displayName")}</Label>
                <Input
                  id="tenant-edit-name"
                  value={editDisplayName}
                  onChange={(event) => {
                    setEditDisplayName(event.target.value);
                    if (updateError) setUpdateError(null);
                  }}
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="tenant-edit-plan">{t("tenants.plan")}</Label>
                <Input
                  id="tenant-edit-plan"
                  value={editPlan}
                  onChange={(event) => {
                    setEditPlan(event.target.value);
                    if (updateError) setUpdateError(null);
                  }}
                  placeholder="1"
                />
              </div>

              {updateError ? <p className="text-xs text-destructive">{updateError}</p> : null}

              <Button
                disabled={updateTenant.isPending || !editDisplayName.trim() || !editPlan.trim()}
                onClick={() =>
                  updateTenant.mutate(
                    {
                      id: selectedTenant.id,
                      payload: {
                        display_name: editDisplayName.trim(),
                        plan: editPlan.trim(),
                      },
                    },
                    {
                      ...getHandlers({ successTitle: t("tenants.activated") }),
                      onSuccess: () => {
                        setUpdateError(null);
                        detail.close();
                      },
                      onError: (error) => {
                        getHandlers({ successTitle: t("tenants.activated") }).onError(error);
                        const normalized = normalizeApiError(error);
                        setUpdateError(normalized.message);
                      },
                    },
                  )
                }
              >
                Save changes
              </Button>
            </PermissionGate>
          </div>
        ) : (
          <ErrorState title={t("tenants.notFound")} message={t("tenants.notFoundDescription")} />
        )}
      </DrawerPanel>

      <DrawerPanel
        open={createOpen}
        onClose={() => {
          setCreateError(null);
          setCreateOpen(false);
        }}
        title={t("tenants.createTitle")}
        description={t("tenants.createDescription")}
        width="md"
      >
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="tenant-slug">{t("tenants.slug")}</Label>
            <Input
              id="tenant-slug"
              value={slug}
              onChange={(event) => {
                setSlug(event.target.value);
                if (createError) setCreateError(null);
              }}
              placeholder="new-tenant"
            />
            {createError && <p className="text-xs text-destructive">{createError}</p>}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="tenant-name">{t("tenants.displayName")}</Label>
            <Input
              id="tenant-name"
              value={displayName}
              onChange={(event) => {
                setDisplayName(event.target.value);
                if (createError) setCreateError(null);
              }}
              placeholder={t("tenants.new")}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="tenant-plan">{t("tenants.plan")}</Label>
            <Input
              id="tenant-plan"
              value={plan}
              onChange={(event) => {
                setPlan(event.target.value);
                if (createError) setCreateError(null);
              }}
              placeholder="1"
            />
          </div>

          <PermissionGate permission={PERMISSIONS.TENANTS_WRITE}>
            <Button
              disabled={!canCreate || createTenant.isPending}
              onClick={() =>
                createTenant.mutate(
                  {
                    slug: slug.trim(),
                    display_name: displayName.trim(),
                    plan: plan.trim() || "1",
                  },
                  {
                    ...getHandlers({ successTitle: t("tenants.createdSuccess") }),
                    onSuccess: () => {
                      setCreateError(null);
                      setCreateOpen(false);
                      setSlug("");
                      setDisplayName("");
                      setPlan("1");
                    },
                    onError: (error) => {
                      getHandlers({ successTitle: t("tenants.createdSuccess") }).onError(error);
                      const normalized = normalizeApiError(error);
                      setCreateError(normalized.message);
                    },
                  },
                )
              }
            >
              {t("tenants.createAction")}
            </Button>
          </PermissionGate>
        </div>
      </DrawerPanel>
    </div>
    </RequirePermission>
  );
}
