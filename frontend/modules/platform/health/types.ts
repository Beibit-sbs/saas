export interface ServiceHealth {
  name: string;
  status: "healthy" | "degraded" | "unhealthy";
  latency_ms: number | null;
  details: string | null;
}

export interface HealthStatus {
  status: "ok" | "healthy" | "degraded" | "unhealthy" | "unknown";
  service?: string;
  services?: ServiceHealth[];
  checked_at?: string;
}

export interface Metrics {
  total_tenants: number;
  active_tenants: number;
  total_students: number;
  active_jobs: number;
  queued_jobs: number;
  failed_jobs_24h: number;
  api_requests_1h: number;
  avg_response_ms: number;
}
