import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/shared/api/client";
import type {
  HealthApiResponse,
  HealthDbResponse,
  HealthWorkerResponse,
  OpsHealthSnapshot,
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

function errorText(err: unknown): string {
  if (err instanceof Error && err.message) return err.message;
  return "Request failed";
}

export function useOpsHealth() {
  return useQuery<OpsHealthSnapshot>({
    queryKey: ["ops", "health"],
    refetchInterval: 30_000,
    queryFn: async () => {
      const [apiResult, dbResult, workerResult] = await Promise.allSettled([
        apiGet<HealthApiResponse>("/health"),
        apiGet<HealthDbResponse>("/health/db"),
        apiGet<HealthWorkerResponse>("/health/worker"),
      ]);

      const errors: string[] = [];

      const apiStatus = apiResult.status === "fulfilled"
        ? toOpsStatus(apiResult.value.status)
        : (errors.push(`api: ${errorText(apiResult.reason)}`), "critical");

      const dbStatus = dbResult.status === "fulfilled"
        ? toOpsStatus(dbResult.value.status)
        : (errors.push(`db: ${errorText(dbResult.reason)}`), "critical");

      const workerStatus = workerResult.status === "fulfilled"
        ? toOpsStatus(workerResult.value.status)
        : (errors.push(`worker: ${errorText(workerResult.reason)}`), "critical");

      const workerHeartbeatAt = workerResult.status === "fulfilled"
        ? workerResult.value.heartbeat_at ?? null
        : null;

      return {
        overall: summarizeOverall([apiStatus, dbStatus, workerStatus]),
        api: apiStatus,
        db: dbStatus,
        worker: workerStatus,
        workerHeartbeatAt,
        updatedAt: new Date().toISOString(),
        errors,
      };
    },
  });
}