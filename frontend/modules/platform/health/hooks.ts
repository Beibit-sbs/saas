import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/shared/api/client";
import type { HealthStatus, Metrics } from "./types";

export function useHealthStatus() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => apiGet<HealthStatus>("/health"),
    refetchInterval: 60_000,
  });
}

export function useMetrics() {
  return useQuery({
    queryKey: ["metrics"],
    queryFn: () => apiGet<Metrics>("/metrics"),
    refetchInterval: 60_000,
  });
}
