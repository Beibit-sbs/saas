import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/shared/api/client";
import type {
  OpsHealthSnapshot,
  OpsSummaryResponse,
  OpsStatus,
} from "./types";

export function toOpsStatus(value: string | undefined | null): OpsStatus {
  if (!value) return "unknown";
  const normalized = value.toLowerCase();
  if (normalized === "ok" || normalized === "healthy" || normalized === "reachable") return "healthy";
  if (normalized === "skipped" || normalized === "not_required" || normalized === "out_of_scope") return "skipped";
  if (normalized === "degraded") return "degraded";
  if (normalized === "error" || normalized === "unhealthy" || normalized === "unreachable") return "critical";
  return "unknown";
}

export function summarizeOverall(statuses: OpsStatus[]): OpsStatus {
  if (statuses.some((s) => s === "critical")) return "critical";
  if (statuses.some((s) => s === "degraded")) return "degraded";
  if (statuses.every((s) => s === "healthy" || s === "skipped")) return "healthy";
  return "unknown";
}

export function useOpsHealth() {
  return useQuery<OpsHealthSnapshot>({
    queryKey: ["ops", "health"],
    refetchInterval: 30_000,
    queryFn: async () => {
      const summary = await apiGet<OpsSummaryResponse>("/api/v1/platform/ops/summary");

      const apiStatus = "healthy" as OpsStatus;
      const dbStatus = "healthy" as OpsStatus;
      const workerStatus =
        summary.runtime.worker_heartbeat_age_seconds === null
          ? ("unknown" as OpsStatus)
          : summary.runtime.worker_heartbeat_age_seconds > 180
            ? ("critical" as OpsStatus)
            : ("healthy" as OpsStatus);

      return {
        overall: summarizeOverall([apiStatus, dbStatus, workerStatus]),
        api: apiStatus,
        db: dbStatus,
        worker: workerStatus,
        workerHeartbeatAt: summary.runtime.worker_heartbeat,
        updatedAt: summary.updated_at,
        errors: [],
      };
    },
  });
}