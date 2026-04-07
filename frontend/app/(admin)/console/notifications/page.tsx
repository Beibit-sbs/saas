"use client";

import { PageHeader } from "@/shared/ui/page-header";
import { DataTable, Column } from "@/shared/ui/data-table";
import { FilterBar } from "@/shared/ui/filter-bar";
import { StatusBadge } from "@/shared/ui/status-badge";
import { Button } from "@/shared/ui/button";
import { DrawerPanel } from "@/shared/ui/drawer-panel";
import { DetailList } from "@/shared/ui/detail-list";
import { ErrorState } from "@/shared/ui/error-state";
import { PermissionGate } from "@/shared/ui/permission-gate";
import { useDetailDrawer } from "@/shared/hooks/use-detail-drawer";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useTableQueryState } from "@/shared/hooks/use-table-query-state";
import {
  useNotifications,
  useMarkNotificationRead,
  useMarkAllNotificationsRead,
} from "@/modules/platform/notifications/hooks";
import { Notification } from "@/modules/platform/notifications/types";
import { formatRelative } from "@/shared/utils/format";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useLanguage } from "@/app/components/LanguageProvider";
import { Bell, CheckCheck } from "lucide-react";

const FILTER_FIELDS = [
  {
    key: "read",
    label: "Read",
    type: "select" as const,
    options: [
      { label: "Unread", value: "false" },
      { label: "Read", value: "true" },
    ],
  },
];

export default function NotificationsPage() {
  const { t } = useLanguage();
  const table = useTableQueryState({ filterKeys: ["read"] as const, defaultPageSize: 20, defaultSort: { key: "when", direction: "desc" } });
  const detail = useDetailDrawer({ paramKey: "notification" });
  const { getHandlers } = useMutationFeedback();

  const { data, isLoading, error, refetch } = useNotifications({
    page: table.page,
    page_size: table.pageSize,
    read: table.filters.read ? table.filters.read === "true" : undefined,
  });
  const markRead = useMarkNotificationRead();
  const markAll = useMarkAllNotificationsRead();
  const selectedNotification = data?.items.find((item) => item.id === detail.selectedId) ?? null;

  if (error) {
    return (
      <ErrorState
        title={t("notifications.loadFailedTitle")}
        onRetry={() => void refetch()}
        retryLabel={t("state.retry")}
      />
    );
  }

  const columns: Column<Notification>[] = [
    { key: "title", header: "Title", cell: (r) => <span className="font-medium">{r.title}</span>, sortValue: (r) => r.title.toLowerCase() },
    { key: "body", header: "Message", cell: (r) => <span className="text-muted-foreground">{r.body}</span> },
    { key: "severity", header: "Severity", cell: (r) => <StatusBadge status={r.severity} />, sortValue: (r) => r.severity },
    { key: "tenant", header: "University", cell: (r) => r.tenant_id ?? "global", sortValue: (r) => r.tenant_id ?? "global" },
    { key: "when", header: "When", cell: (r) => formatRelative(r.created_at), sortValue: (r) => r.created_at },
    {
      key: "actions",
      header: "",
      width: "80px",
      cell: (r) =>
        !r.read ? (
          <PermissionGate permission={PERMISSIONS.NOTIFICATIONS_WRITE}>
            <Button
              variant="ghost"
              size="sm"
              disabled={markRead.isPending || markAll.isPending}
              onClick={(event) => {
                event.stopPropagation();
                if (markRead.isPending || markAll.isPending) {
                  return;
                }
                markRead.mutate(r.id, getHandlers({ successTitle: "Notification marked read" }));
              }}
            >
              Mark read
            </Button>
          </PermissionGate>
        ) : null,
    },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title={t("nav.notifications")}
        description={t("console.notifications.description")}
        icon={Bell}
        actions={
          <PermissionGate permission={PERMISSIONS.NOTIFICATIONS_WRITE}>
            <Button
              variant="outline"
              size="sm"
              disabled={markAll.isPending || markRead.isPending}
              onClick={() => {
                if (markAll.isPending || markRead.isPending) {
                  return;
                }
                markAll.mutate(undefined, getHandlers({ successTitle: "All notifications marked as read" }));
              }}
            >
              <CheckCheck className="h-4 w-4 mr-1" />
              Mark all read
            </Button>
          </PermissionGate>
        }
      />

      <FilterBar fields={FILTER_FIELDS} values={table.filters} onChange={table.setFilter} onReset={table.resetFilters} />

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
        emptyTitle={t("notifications.emptyTitle")}
      />

      <DrawerPanel
        open={detail.isOpen}
        onClose={detail.close}
        title={selectedNotification?.title ?? "Notification details"}
        description={selectedNotification?.type ?? "Select a notification from the table."}
      >
        {selectedNotification ? (
          <DetailList
            items={[
              { label: "Severity", value: <StatusBadge status={selectedNotification.severity} /> },
              { label: "University", value: selectedNotification.tenant_id ?? "global" },
              { label: "Read", value: selectedNotification.read ? "Yes" : "No" },
              { label: "Created", value: formatRelative(selectedNotification.created_at) },
              { label: "Message", value: <p className="whitespace-pre-wrap">{selectedNotification.body}</p> },
            ]}
          />
        ) : (
          <ErrorState title="Notification not found" message="The selected notification is not present on this page of results." />
        )}
      </DrawerPanel>
    </div>
  );
}
