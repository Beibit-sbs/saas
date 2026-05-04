"use client";

import { useMemo } from "react";
import { Skeleton } from "@/shared/ui/skeleton";
import { useAdminAuth } from "@/shared/auth/context";
import { useTenantKpiMetrics } from "./use-dashboard";

interface Wave1KpiBarProps {
  metricKeys: string[];
  labels: Record<string, string>;
}

export function Wave1KpiBar({ metricKeys, labels }: Wave1KpiBarProps) {
  const { user } = useAdminAuth();
  const tenantId = user?.tenantId ?? 0;
  const { data, isLoading } = useTenantKpiMetrics(tenantId);

  const metrics = useMemo(() => {
    if (!data) return [];
    return metricKeys.map((key) => {
      const snap = data.find((s) => s.metric_key === key);
      return { key, label: labels[key] ?? key, value: snap?.metric_value ?? null };
    });
  }, [data, metricKeys, labels]);

  if (isLoading) {
    return (
      <div className="flex flex-wrap gap-3" data-testid="wave1-kpi-bar-loading">
        {metricKeys.map((k) => (
          <Skeleton key={k} className="h-12 w-28" />
        ))}
      </div>
    );
  }

  if (!data || metrics.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-3" data-testid="wave1-kpi-bar">
      {metrics.map((m) => (
        <div key={m.key} className="rounded-md border bg-muted/30 px-3 py-2 text-sm">
          <p className="text-xs text-muted-foreground">{m.label}</p>
          <p className="mt-0.5 font-semibold">
            {m.value !== null ? Number(m.value).toLocaleString() : "—"}
          </p>
        </div>
      ))}
    </div>
  );
}
