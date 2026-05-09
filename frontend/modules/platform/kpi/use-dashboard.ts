import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/shared/api/client";
import type { RectorDashboard, RectorKpiDrilldownSummary, TenantMetricSnapshot } from "./types";

export const PLATFORM_KPI_DASHBOARD_KEY = "platform-kpi-dashboard";
export const PLATFORM_KPI_METRICS_KEY = "platform-kpi-metrics";
export const PLATFORM_KPI_DRILLDOWN_KEY = "platform-kpi-drilldown";

export function useRectorDashboard(tenantId: number) {
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

export function useRectorKpiDrilldown(tenantId: number) {
  return useQuery({
    queryKey: [PLATFORM_KPI_DRILLDOWN_KEY, tenantId],
    queryFn: () =>
      apiGet<RectorKpiDrilldownSummary>("/api/bff/admin/platform/kpi/drilldown", {
        tenant_id: tenantId,
      }),
    enabled: tenantId > 0,
    staleTime: 60_000,
  });
}

export function useTenantKpiMetrics(tenantId: number) {
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
