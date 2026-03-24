import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/shared/api/client";
import type { RectorDashboard, TenantMetricSnapshot } from "./types";

export const PLATFORM_KPI_DASHBOARD_KEY = "platform-kpi-dashboard";
export const PLATFORM_KPI_METRICS_KEY = "platform-kpi-metrics";

export function useRectorDashboard(tenantId: number = 1) {
  return useQuery({
    queryKey: [PLATFORM_KPI_DASHBOARD_KEY, tenantId],
    queryFn: () =>
      apiGet<RectorDashboard>("/api/bff/admin/platform/kpi/dashboard", {
        tenant_id: tenantId,
      }),
    enabled: tenantId > 0,
    staleTime: 60_000,
  });
}

export function useTenantKpiMetrics(tenantId: number = 1) {
  return useQuery({
    queryKey: [PLATFORM_KPI_METRICS_KEY, tenantId],
    queryFn: () =>
      apiGet<TenantMetricSnapshot[]>("/api/bff/admin/platform/kpi/metrics", {
        tenant_id: tenantId,
      }),
    enabled: tenantId > 0,
    staleTime: 60_000,
  });
}
