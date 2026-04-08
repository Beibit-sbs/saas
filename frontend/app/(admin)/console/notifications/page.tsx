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
import { PermissionGate, RequirePermission } from "@/shared/ui/permission-gate";
import { useDetailDrawer } from "@/shared/hooks/use-detail-drawer";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useTableQueryState } from "@/shared/hooks/use-table-query-state";
import {
  useNotifications,
  useMarkNotificationRead,
  useMarkAllNotificationsRead,
  useDispatchNotification,
} from "@/modules/platform/notifications/hooks";
import { Notification } from "@/modules/platform/notifications/types";
import { formatRelative } from "@/shared/utils/format";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useLanguage } from "@/app/components/LanguageProvider";
import { Bell, CheckCheck, Plus } from "lucide-react";

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
  const [composeOpen, setComposeOpen] = useState(false);
  const [tenantId, setTenantId] = useState("1");
  const [channel, setChannel] = useState<"email" | "in_app" | "webhook">("in_app");
  const [target, setTarget] = useState("");
  const [subject, setSubject] = useState("");
  const [payloadText, setPayloadText] = useState('{"event":"manual.dispatch"}');
  const [composeError, setComposeError] = useState<string | null>(null);
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
  const dispatch = useDispatchNotification();
  const selectedNotification = data?.items.find((item) => item.id === detail.selectedId) ?? null;
  const canDispatch = Number(tenantId) > 0 && target.trim().length >= 3;

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
    <RequirePermission permission={PERMISSIONS.NOTIFICATIONS_READ}>
    <div className="space-y-4">
      <PageHeader
        title={t("nav.notifications")}
        description={t("console.notifications.description")}
        icon={Bell}
        actions={
          <PermissionGate permission={PERMISSIONS.NOTIFICATIONS_WRITE}>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setComposeError(null);
                  setComposeOpen(true);
                }}
              >
                <Plus className="h-4 w-4 mr-1" />
                {t("notifications.sendAction")}
              </Button>
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
            </div>
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

      <DrawerPanel
        open={composeOpen}
        onClose={() => {
          setComposeOpen(false);
          setComposeError(null);
        }}
        title={t("notifications.sendTitle")}
        description={t("notifications.sendDescription")}
      >
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="notification-tenant-id">{t("notifications.form.tenantId")}</Label>
            <Input
              id="notification-tenant-id"
              value={tenantId}
              onChange={(event) => setTenantId(event.target.value)}
              placeholder="1"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="notification-channel">{t("notifications.form.channel")}</Label>
            <select
              id="notification-channel"
              className="w-full rounded border bg-background px-3 py-2 text-sm"
              value={channel}
              onChange={(event) => setChannel(event.target.value as "email" | "in_app" | "webhook")}
            >
              <option value="in_app">in_app</option>
              <option value="email">email</option>
              <option value="webhook">webhook</option>
            </select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="notification-target">{t("notifications.form.target")}</Label>
            <Input
              id="notification-target"
              value={target}
              onChange={(event) => setTarget(event.target.value)}
              placeholder={channel === "email" ? "ops@example.com" : channel === "webhook" ? "https://example.com/webhook" : "admin-console"}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="notification-subject">{t("notifications.form.subject")}</Label>
            <Input
              id="notification-subject"
              value={subject}
              onChange={(event) => setSubject(event.target.value)}
              placeholder="Platform alert"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="notification-payload">{t("notifications.form.payload")}</Label>
            <textarea
              id="notification-payload"
              className="min-h-[120px] w-full rounded border bg-background px-3 py-2 text-sm"
              value={payloadText}
              onChange={(event) => setPayloadText(event.target.value)}
            />
          </div>
          {composeError ? <p className="text-xs text-destructive">{composeError}</p> : null}
          <PermissionGate permission={PERMISSIONS.NOTIFICATIONS_WRITE}>
            <Button
              disabled={!canDispatch || dispatch.isPending}
              onClick={() => {
                setComposeError(null);
                let parsedPayload: Record<string, unknown> = {};
                if (payloadText.trim().length > 0) {
                  try {
                    const raw = JSON.parse(payloadText);
                    if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
                      setComposeError(t("notifications.payloadMustBeObject"));
                      return;
                    }
                    parsedPayload = raw as Record<string, unknown>;
                  } catch {
                    setComposeError(t("notifications.payloadInvalid"));
                    return;
                  }
                }

                dispatch.mutate(
                  {
                    tenant_id: Number(tenantId),
                    channel,
                    target: target.trim(),
                    subject: subject.trim() || undefined,
                    payload: parsedPayload,
                  },
                  {
                    ...getHandlers({ successTitle: t("notifications.sent") }),
                    onSuccess: () => {
                      setComposeOpen(false);
                      setComposeError(null);
                      setTarget("");
                      setSubject("");
                    },
                  },
                );
              }}
            >
              {t("notifications.sendAction")}
            </Button>
          </PermissionGate>
        </div>
      </DrawerPanel>
    </div>
    </RequirePermission>
  );
}
