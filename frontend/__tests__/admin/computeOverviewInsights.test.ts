import { describe, expect, it } from "vitest";

import { computeOverviewInsights } from "../../app/admin/utils/computeOverviewInsights";
import type { DashboardSnapshot, SupportedLanguage, SystemHealthResponse } from "../../app/admin/types";

const supportedLanguages: SupportedLanguage[] = [
  { code: "ru", name: "Russian", native_name: "Русский", enabled: true, system: true },
  { code: "en", name: "English", native_name: "English", enabled: true, system: true },
];

function buildSnapshot(overrides?: Partial<DashboardSnapshot>): DashboardSnapshot {
  return {
    status: "ok",
    generated_at: "2026-03-31T06:00:00Z",
    system: {
      backend_health: "ok",
      api_health: "ok",
      metrics_available: true,
    },
    users: {
      local_users_count: 4,
    },
    rbac: {
      roles_count: 3,
      assignments_count: 5,
    },
    languages: {
      total_count: 2,
      enabled_count: 2,
      system_count: 2,
    },
    integrations: {
      ldap: {
        enabled: true,
        configured: true,
      },
      ai_providers: {
        total_count: 2,
        configured_count: 0,
      },
    },
    backups: {
      active_profile: "default",
      profiles_count: 1,
      last_job: null,
    },
    audit: {
      recent_events_count: 12,
      last_event: null,
    },
    ...overrides,
  };
}

const healthySystem: SystemHealthResponse = {
  status: "ok",
  services: { api: "ok", worker: "ok" },
  metrics: {},
  queues: { default: 0 },
  disk: {
    path: "/tmp",
    total_bytes: 100,
    used_bytes: 45,
    free_bytes: 55,
    usage_percent: 45,
  },
};

describe("computeOverviewInsights", () => {
  it("prioritizes backup, jobs, and AI readiness risks from real signals", () => {
    const insights = computeOverviewInsights({
      dashboardSnapshot: buildSnapshot(),
      systemHealth: healthySystem,
      jobs: [
        {
          id: 1,
          tenant_id: 1,
          job_type: "ai_inference",
          status: "failed",
          payload_json: {},
          retry_count: 1,
          max_retries: 3,
          created_at: "2026-03-31T05:00:00Z",
          started_at: "2026-03-31T05:01:00Z",
          finished_at: "2026-03-31T05:03:00Z",
        },
        {
          id: 2,
          tenant_id: 1,
          job_type: "sync_students",
          status: "queued",
          payload_json: {},
          retry_count: 0,
          max_retries: 3,
          created_at: "2026-03-31T02:00:00Z",
        },
        {
          id: 3,
          tenant_id: 1,
          job_type: "sync_grades",
          status: "failed",
          payload_json: {},
          retry_count: 1,
          max_retries: 3,
          created_at: "2026-03-31T04:00:00Z",
          started_at: "2026-03-31T04:05:00Z",
          finished_at: "2026-03-31T04:06:00Z",
        },
        {
          id: 4,
          tenant_id: 1,
          job_type: "sync_teachers",
          status: "succeeded",
          payload_json: {},
          retry_count: 0,
          max_retries: 3,
          created_at: "2026-03-31T03:00:00Z",
          started_at: "2026-03-31T03:01:00Z",
          finished_at: "2026-03-31T03:04:00Z",
        },
      ],
      auditEvents: [],
      localUsers: [],
      supportedLanguages,
    });

    expect(insights.slice(0, 3).map((item) => item.id)).toEqual([
      "backup-missing",
      "job-throughput-risk",
      "ai-unconfigured",
    ]);
    expect(insights[0]?.impact).toBe("high");
    expect(insights[1]?.recommendedAction).toContain("Open Jobs");
  });

  it("falls back to healthy low-impact signals when critical issues are absent", () => {
    const insights = computeOverviewInsights({
      dashboardSnapshot: buildSnapshot({
        integrations: {
          ldap: { enabled: true, configured: true },
          ai_providers: { total_count: 1, configured_count: 1 },
        },
        backups: {
          active_profile: "default",
          profiles_count: 1,
          last_job: {
            job_id: "backup-1",
            status: "success",
            profile_id: "default",
            file_path: "/tmp/backup.dump",
            size_bytes: 128,
            started_at: "2026-03-31T04:00:00Z",
            finished_at: "2026-03-31T04:30:00Z",
          },
        },
      }),
      systemHealth: healthySystem,
      jobs: [],
      auditEvents: [
        {
          event_id: "a-1",
          timestamp: "2026-03-31T05:00:00Z",
          actor: "admin",
          action: "rbac.assign",
          path: "/api/bff/admin/rbac",
          client_ip: "10.0.0.1",
          correlation_id: "corr-1",
          result: "success",
        },
      ],
      localUsers: [],
      supportedLanguages,
    });

    expect(insights.length).toBeGreaterThanOrEqual(3);
    expect(insights.every((item) => item.impact === "low")).toBe(true);
    expect(insights.map((item) => item.id)).toEqual(expect.arrayContaining(["backup-healthy", "system-stable", "audit-healthy"]));
  });
});