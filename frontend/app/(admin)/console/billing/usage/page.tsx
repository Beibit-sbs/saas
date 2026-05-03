"use client";

import { useState } from "react";
import { BarChart2 } from "lucide-react";
import { PageHeader } from "@/shared/ui/page-header";
import { Card } from "@/shared/ui/card";
import { Button } from "@/shared/ui/button";
import { DataTable, type Column } from "@/shared/ui/data-table";
import { ErrorState } from "@/shared/ui/error-state";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/shared/api/client";

// ---------- types ----------

export interface UsageEvent {
  id: number;
  tenant_id: number;
  metric: string;
  value: number;
  created_at: string;
}

interface UsageEventListResponse {
  events: UsageEvent[];
}

interface UsageSumResponse {
  tenant_id: number;
  metric: string;
  total: number;
}

interface TenantRecord {
  id: number;
  slug: string;
  name: string;
}

interface TenantListResponse {
  tenants: TenantRecord[];
}

// ---------- hooks ----------

function useTenants() {
  return useQuery({
    queryKey: ["tenants"],
    queryFn: () => apiGet<TenantListResponse>("/api/admin/tenants"),
  });
}

function useUsageEvents(
  tenantId: number,
  metricFilter?: string,
  limit?: number
) {
  return useQuery({
    queryKey: ["usage-events", tenantId, metricFilter, limit],
    queryFn: () => {
      const params = new URLSearchParams({ tenant_id: String(tenantId) });
      if (metricFilter) params.set("metric", metricFilter);
      if (limit) params.set("limit", String(limit));
      return apiGet<UsageEventListResponse>(`/api/usage/events?${params}`);
    },
    enabled: tenantId > 0,
  });
}

function useUsageSum(tenantId: number, metric: string, since?: string) {
  return useQuery({
    queryKey: ["usage-sum", tenantId, metric, since],
    queryFn: () => {
      const params = new URLSearchParams({
        tenant_id: String(tenantId),
        metric,
      });
      if (since) params.set("since", since);
      return apiGet<UsageSumResponse>(`/api/usage/sum?${params}`);
    },
    enabled: tenantId > 0 && metric.length > 0,
  });
}

function useRecordEvent() {
  return useMutation({
    mutationFn: ({
      tenantId,
      metric,
      value,
    }: {
      tenantId: number;
      metric: string;
      value: number;
    }) =>
      apiPost("/api/usage/events", {
        tenant_id: tenantId,
        metric,
        value,
      }),
  });
}

// ---------- page ----------

export default function UsagePage() {
  const qc = useQueryClient();
  const { getHandlers } = useMutationFeedback();

  const [tenantId, setTenantId] = useState(0);
  const [metricFilter, setMetricFilter] = useState("");
  const [sumMetric, setSumMetric] = useState("");

  // record event modal
  const [recordModalOpen, setRecordModalOpen] = useState(false);
  const [newMetric, setNewMetric] = useState("");
  const [newValue, setNewValue] = useState(1);

  const { data: tenantsData } = useTenants();
  const tenants = tenantsData?.tenants ?? [];

  const { data: eventsData, error } = useUsageEvents(
    tenantId,
    metricFilter || undefined
  );
  const events = eventsData?.events ?? [];

  const { data: sumData } = useUsageSum(tenantId, sumMetric);

  const recordMutation = useRecordEvent();

  const invalidate = () =>
    qc.invalidateQueries({ queryKey: ["usage-events", tenantId] });

  function handleRecord() {
    recordMutation.mutate(
      { tenantId, metric: newMetric, value: newValue },
      {
        ...getHandlers("Usage event recorded"),
        onSuccess: () => {
          invalidate();
          setRecordModalOpen(false);
          setNewMetric("");
          setNewValue(1);
        },
      }
    );
  }

  const totalEvents = events.length;
  const uniqueMetrics = Array.from(new Set(events.map((e) => e.metric))).length;
  const totalValue = events.reduce((acc, e) => acc + e.value, 0);

  const columns: Column<UsageEvent>[] = [
    { key: "id", header: "ID", cell: (e) => String(e.id) },
    { key: "metric", header: "Metric", cell: (e) => e.metric },
    { key: "value", header: "Value", cell: (e) => String(e.value) },
    {
      key: "created_at",
      header: "Recorded At",
      cell: (e) => new Date(e.created_at).toLocaleDateString(),
    },
  ];

  return (
    <RequirePermission permission={PERMISSIONS.BILLING_READ}>
      <div className="space-y-6">
        <PageHeader
          title="Usage Tracking"
          subtitle="Monitor tenant usage metrics"
          icon={BarChart2}
          actions={
            tenantId > 0 ? (
              <Button size="sm" onClick={() => setRecordModalOpen(true)}>
                Record Event
              </Button>
            ) : null
          }
        />

        {/* Controls */}
        <div className="flex items-center gap-4">
          <select
            aria-label="Select tenant"
            className="border rounded px-3 py-2 text-sm"
            value={tenantId}
            onChange={(e) => setTenantId(Number(e.target.value))}
          >
            <option value={0}>— Select tenant —</option>
            {tenants.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>

          <input
            aria-label="Filter by metric"
            className="border rounded px-3 py-2 text-sm"
            placeholder="Filter by metric…"
            value={metricFilter}
            onChange={(e) => setMetricFilter(e.target.value)}
          />
        </div>

        {/* Stats */}
        {tenantId > 0 && (
          <div className="grid grid-cols-3 gap-4">
            <Card className="p-4">
              <p className="text-sm text-muted-foreground">Total Events</p>
              <p className="text-2xl font-bold">{totalEvents}</p>
            </Card>
            <Card className="p-4">
              <p className="text-sm text-muted-foreground">Unique Metrics</p>
              <p className="text-2xl font-bold text-blue-600">{uniqueMetrics}</p>
            </Card>
            <Card className="p-4">
              <p className="text-sm text-muted-foreground">Total Value</p>
              <p className="text-2xl font-bold text-green-600">{totalValue}</p>
            </Card>
          </div>
        )}

        {/* Sum query */}
        {tenantId > 0 && (
          <div className="flex items-center gap-3">
            <input
              aria-label="Metric for sum"
              className="border rounded px-3 py-2 text-sm"
              placeholder="Metric to sum…"
              value={sumMetric}
              onChange={(e) => setSumMetric(e.target.value)}
            />
            {sumData && (
              <p className="text-sm">
                Sum of <strong>{sumData.metric}</strong>:{" "}
                <span className="font-bold">{sumData.total}</span>
              </p>
            )}
          </div>
        )}

        {/* Error */}
        {error && <ErrorState message="Failed to load usage events" />}

        {/* Table */}
        {tenantId > 0 && (
          <div className="space-y-3">
            <DataTable
              columns={columns}
              data={events}
              getRowKey={(e) => String(e.id)}
            />
          </div>
        )}

        {/* Record Event Modal */}
        {recordModalOpen && (
          <div
            role="dialog"
            aria-label="Record Usage Event"
            className="fixed inset-0 flex items-center justify-center bg-black/40"
          >
            <div className="bg-background rounded-lg p-6 w-96 space-y-4">
              <h2 className="text-lg font-semibold">Record Usage Event</h2>
              <div className="space-y-2">
                <label className="text-sm font-medium">Metric</label>
                <input
                  aria-label="Event metric"
                  className="w-full border rounded px-3 py-2 text-sm"
                  value={newMetric}
                  onChange={(e) => setNewMetric(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Value</label>
                <input
                  aria-label="Event value"
                  type="number"
                  className="w-full border rounded px-3 py-2 text-sm"
                  value={newValue}
                  onChange={(e) => setNewValue(Number(e.target.value))}
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => setRecordModalOpen(false)}
                >
                  Back
                </Button>
                <Button
                  onClick={handleRecord}
                  disabled={!newMetric || newValue < 1}
                >
                  Submit
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </RequirePermission>
  );
}
