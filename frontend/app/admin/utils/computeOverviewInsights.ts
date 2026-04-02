import type {
  AdminInsight,
  DashboardSnapshot,
  JobItem,
  LocalUser,
  SupportedLanguage,
  SystemHealthResponse,
  AuditEvent,
} from "../types";

type ComputeOverviewInsightsParams = {
  dashboardSnapshot: DashboardSnapshot | null;
  systemHealth: SystemHealthResponse | null;
  jobs: JobItem[];
  auditEvents: AuditEvent[];
  localUsers: LocalUser[];
  supportedLanguages: SupportedLanguage[];
};

const HEALTHY_SERVICE_STATES = new Set(["ok", "healthy", "ready", "up", "success"]);
const AI_JOB_PATTERN = /(ai|chat|llm|inference|model)/i;

function parseDate(value?: string | null): Date | null {
  if (!value) {
    return null;
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function hoursBetween(older: Date | null, newer: Date): number | null {
  if (!older) {
    return null;
  }
  return (newer.getTime() - older.getTime()) / 3_600_000;
}

function countWithinHours<T>(items: T[], getTimestamp: (item: T) => string | null | undefined, now: Date, startHours: number, endHours = 0): T[] {
  return items.filter((item) => {
    const timestamp = parseDate(getTimestamp(item));
    if (!timestamp) {
      return false;
    }
    const age = hoursBetween(timestamp, now);
    if (age === null) {
      return false;
    }
    return age <= startHours && age > endHours;
  });
}

function percent(part: number, total: number): number {
  if (total <= 0) {
    return 0;
  }
  return Math.round((part / total) * 100);
}

function isHealthyState(value?: string | null): boolean {
  return HEALTHY_SERVICE_STATES.has(String(value || "").trim().toLowerCase());
}

function formatHours(hours: number): string {
  if (hours < 1) {
    return "<1h";
  }
  if (hours < 24) {
    return `${Math.round(hours)}h`;
  }
  return `${Math.round(hours / 24)}d`;
}

function toNumericQueueDepth(queues: Record<string, string | number | boolean | null> | undefined): number {
  if (!queues) {
    return 0;
  }
  return Object.values(queues).reduce<number>((total, value) => {
    if (typeof value === "number" && Number.isFinite(value)) {
      return total + Math.max(0, value);
    }
    if (typeof value === "string") {
      const parsed = Number(value);
      if (Number.isFinite(parsed)) {
        return total + Math.max(0, parsed);
      }
    }
    return total;
  }, 0);
}

function top<T>(items: T[], minimum: number, limit: number): T[] {
  if (items.length >= minimum) {
    return items.slice(0, limit);
  }
  return items;
}

export function computeOverviewInsights({
  dashboardSnapshot,
  systemHealth,
  jobs,
  auditEvents,
  localUsers,
  supportedLanguages,
}: ComputeOverviewInsightsParams): AdminInsight[] {
  if (!dashboardSnapshot) {
    return [];
  }

  const now = parseDate(dashboardSnapshot.generated_at) ?? new Date();
  const issues: AdminInsight[] = [];
  const healthySignals: AdminInsight[] = [];

  const lastBackup = dashboardSnapshot.backups.last_job;
  const lastBackupTime = parseDate(lastBackup?.finished_at);
  const backupAgeHours = hoursBetween(lastBackupTime, now);

  if (!lastBackup) {
    issues.push({
      id: "backup-missing",
      title: "No verified recovery point",
      explanation: "The control plane has no completed backup job, so restore readiness is unproven.",
      impact: "high",
      recommendedAction: "Open Backups, validate a profile, and run a backup before the next change window.",
      signal: "0 recent successful backups",
      tab: "backups",
      score: 98,
    });
  } else if (lastBackup.status !== "success") {
    issues.push({
      id: "backup-failed",
      title: "Recovery posture is degraded",
      explanation: `The latest backup finished with status ${lastBackup.status}, so the last restore point cannot be trusted.`,
      impact: "high",
      recommendedAction: "Review the failed backup job, fix the profile or path issue, and rerun the backup.",
      signal: `${lastBackup.status} at ${lastBackup.finished_at || lastBackup.started_at || "unknown time"}`,
      tab: "backups",
      score: 94,
    });
  } else if ((backupAgeHours ?? 0) >= 72) {
    issues.push({
      id: "backup-stale-high",
      title: "Recovery point is stale",
      explanation: `The last successful backup is ${formatHours(backupAgeHours ?? 0)} old, which exceeds a normal operational recovery cadence.`,
      impact: "high",
      recommendedAction: "Run a fresh backup and verify retention so the platform has a current restore point.",
      signal: `${formatHours(backupAgeHours ?? 0)} since last success`,
      tab: "backups",
      score: 90,
    });
  } else if ((backupAgeHours ?? 0) >= 24) {
    issues.push({
      id: "backup-stale-medium",
      title: "Backup cadence is slipping",
      explanation: `The last successful backup is ${formatHours(backupAgeHours ?? 0)} old, so resilience is drifting away from a daily checkpoint.`,
      impact: "medium",
      recommendedAction: "Review backup scheduling and trigger a fresh run before the next operational change.",
      signal: `${formatHours(backupAgeHours ?? 0)} since last success`,
      tab: "backups",
      score: 71,
    });
  } else {
    healthySignals.push({
      id: "backup-healthy",
      title: "Recovery cadence is healthy",
      explanation: "A successful backup exists within the last day, so restore posture is currently covered.",
      impact: "low",
      recommendedAction: "Keep the current backup schedule and periodically rehearse restore validation.",
      signal: `${formatHours(backupAgeHours ?? 0)} since last success`,
      tab: "backups",
      score: 24,
    });
  }

  const unhealthyServices = Object.entries(systemHealth?.services ?? {}).filter(([, status]) => !isHealthyState(status));
  const queueDepth = toNumericQueueDepth(systemHealth?.queues);
  const diskUsage = typeof systemHealth?.disk?.usage_percent === "number" ? systemHealth.disk.usage_percent : null;
  const backendHealthy = dashboardSnapshot.system.backend_health === "ok";
  const apiHealthy = dashboardSnapshot.system.api_health === "ok";

  if (!backendHealthy || !apiHealthy || unhealthyServices.length > 0) {
    const serviceList = unhealthyServices.map(([name]) => name).slice(0, 3).join(", ") || "backend/api";
    issues.push({
      id: "system-degraded",
      title: "Core services show degradation",
      explanation: `One or more platform services are unhealthy (${serviceList}), which raises risk for admin actions and API calls.`,
      impact: "high",
      recommendedAction: "Open System Health, inspect unhealthy services, and clear the failing dependency before further rollout.",
      signal: unhealthyServices.length > 0 ? `${unhealthyServices.length} unhealthy services` : `${backendHealthy ? 0 : 1 + (apiHealthy ? 0 : 1)} failed health checks`,
      tab: "system",
      score: 92,
    });
  } else if ((diskUsage ?? 0) >= 90 || queueDepth >= 20) {
    issues.push({
      id: "system-pressure-high",
      title: "System pressure is accumulating",
      explanation: `Infrastructure headroom is narrowing with disk at ${Math.round(diskUsage ?? 0)}% and queue depth at ${queueDepth}.`,
      impact: "high",
      recommendedAction: "Open System Health and Jobs to reduce queue backlog or free disk before service quality drops.",
      signal: `${Math.round(diskUsage ?? 0)}% disk · ${queueDepth} queued items`,
      tab: "system",
      score: 88,
    });
  } else if ((diskUsage ?? 0) >= 85 || queueDepth >= 10) {
    issues.push({
      id: "system-pressure-medium",
      title: "System headroom is tightening",
      explanation: `The platform is still serving traffic, but disk usage or queue depth is trending toward an operational threshold.`,
      impact: "medium",
      recommendedAction: "Review queue consumers and disk growth before routine admin work turns into incident response.",
      signal: `${Math.round(diskUsage ?? 0)}% disk · ${queueDepth} queued items`,
      tab: "system",
      score: 69,
    });
  } else {
    healthySignals.push({
      id: "system-stable",
      title: "System baseline is stable",
      explanation: "Backend, API, and infrastructure headroom are currently within normal control thresholds.",
      impact: "low",
      recommendedAction: "Keep monitoring system health and preserve headroom before the next traffic spike.",
      signal: `${Math.round(diskUsage ?? 0)}% disk · ${queueDepth} queued items`,
      tab: "system",
      score: 22,
    });
  }

  const recentJobs = countWithinHours(jobs, (job) => job.created_at, now, 24);
  const previousJobs = countWithinHours(jobs, (job) => job.created_at, now, 48, 24);
  const failedRecentJobs = recentJobs.filter((job) => job.status === "failed");
  const queuedOldJobs = jobs.filter((job) => job.status === "queued" && (hoursBetween(parseDate(job.created_at), now) ?? 0) >= 2);
  const runningOldJobs = jobs.filter((job) => job.status === "running" && (hoursBetween(parseDate(job.started_at ?? job.created_at), now) ?? 0) >= 2);
  const stalledJobs = queuedOldJobs.length + runningOldJobs.length;
  const recentFailureRate = recentJobs.length > 0 ? failedRecentJobs.length / recentJobs.length : 0;

  if ((recentJobs.length >= 4 && recentFailureRate >= 0.35) || stalledJobs > 0) {
    issues.push({
      id: "job-throughput-risk",
      title: "Execution pipeline needs intervention",
      explanation: `Background work is losing reliability with ${failedRecentJobs.length}/${recentJobs.length || 1} recent job failures and ${stalledJobs} stuck queued or running jobs.`,
      impact: stalledJobs >= 3 || recentFailureRate >= 0.5 ? "high" : "medium",
      recommendedAction: "Open Jobs, clear stuck work, and retry failing flows before backlog impacts operators or students.",
      signal: `${failedRecentJobs.length} failed · ${stalledJobs} stalled`,
      tab: "jobs",
      score: stalledJobs >= 3 || recentFailureRate >= 0.5 ? 86 : 74,
    });
  }

  if (previousJobs.length >= 6 && recentJobs.length * 2 < previousJobs.length) {
    issues.push({
      id: "job-activity-drop",
      title: "Operational activity dropped sharply",
      explanation: `Job volume fell from ${previousJobs.length} to ${recentJobs.length} over the last day window, which can indicate stalled automations or missing triggers.`,
      impact: recentJobs.length === 0 ? "high" : "medium",
      recommendedAction: "Inspect Jobs and upstream schedulers to confirm that expected workflows are still being triggered.",
      signal: `${previousJobs.length} -> ${recentJobs.length} day over day`,
      tab: "jobs",
      score: recentJobs.length === 0 ? 79 : 63,
    });
  }

  const recentAuditEvents = countWithinHours(auditEvents, (event) => event.timestamp, now, 24);
  const failedAuditEvents = recentAuditEvents.filter((event) => String(event.result || "").toLowerCase() === "failed");

  if (recentAuditEvents.length >= 8 && failedAuditEvents.length >= 2) {
    issues.push({
      id: "audit-failures",
      title: "Admin actions are failing in the audit trail",
      explanation: `The audit stream recorded ${failedAuditEvents.length} failed privileged actions in the last 24 hours, which suggests unstable operator workflows or policy friction.`,
      impact: failedAuditEvents.length >= 4 ? "high" : "medium",
      recommendedAction: "Open Audit, isolate the failing action pattern, and correct the policy or configuration behind it.",
      signal: `${failedAuditEvents.length}/${recentAuditEvents.length} recent failures`,
      tab: "audit",
      score: failedAuditEvents.length >= 4 ? 82 : 67,
    });
  } else if (recentJobs.length >= 4 && recentAuditEvents.length === 0) {
    issues.push({
      id: "audit-visibility-gap",
      title: "Operational activity lacks audit visibility",
      explanation: `Jobs are still running, but no audit events were recorded in the last 24 hours, so decision traceability is weakening.`,
      impact: "medium",
      recommendedAction: "Open Audit and verify that operator events are still being emitted and retained.",
      signal: `${recentJobs.length} recent jobs · 0 recent audit events`,
      tab: "audit",
      score: 65,
    });
  } else if (recentAuditEvents.length > 0 && failedAuditEvents.length === 0) {
    healthySignals.push({
      id: "audit-healthy",
      title: "Audit flow is active",
      explanation: "Recent administrative actions are being recorded without failed audit results, so operational traceability is intact.",
      impact: "low",
      recommendedAction: "Keep exporting and reviewing audit history as part of routine governance.",
      signal: `${recentAuditEvents.length} recent audit events`,
      tab: "audit",
      score: 18,
    });
  }

  const aiConfigured = dashboardSnapshot.integrations.ai_providers.configured_count;
  const aiTotal = dashboardSnapshot.integrations.ai_providers.total_count;
  const recentAiJobs = recentJobs.filter((job) => AI_JOB_PATTERN.test(job.job_type));

  if (aiTotal > 0 && aiConfigured === 0) {
    issues.push({
      id: "ai-unconfigured",
      title: "AI control plane is not ready",
      explanation: recentAiJobs.length > 0
        ? `AI-related jobs are present, but no provider is configured, so AI workflows are at risk of failing outright.`
        : "No AI provider is configured, so AI features cannot be promoted into reliable operational use.",
      impact: recentAiJobs.length > 0 ? "high" : "medium",
      recommendedAction: "Open Integrations and configure at least one validated AI provider before enabling more AI-dependent flows.",
      signal: `${aiConfigured}/${aiTotal} providers configured`,
      tab: "integrations",
      score: recentAiJobs.length > 0 ? 78 : 58,
    });
  } else if (aiTotal > 0 && aiConfigured < aiTotal && recentAiJobs.length > 0) {
    issues.push({
      id: "ai-partial-coverage",
      title: "AI provider coverage is partial",
      explanation: `AI workload is active, but only ${aiConfigured} of ${aiTotal} providers are configured, which limits routing resilience.`,
      impact: "medium",
      recommendedAction: "Open Integrations and finish provider validation to improve failover and policy routing options.",
      signal: `${aiConfigured}/${aiTotal} providers configured`,
      tab: "integrations",
      score: 57,
    });
  } else if (aiConfigured > 0) {
    healthySignals.push({
      id: "ai-ready",
      title: "AI provider layer is configured",
      explanation: "The control plane has validated provider coverage for AI features, reducing rollout friction.",
      impact: "low",
      recommendedAction: "Keep validating providers after key changes and before scaling AI traffic.",
      signal: `${aiConfigured}/${aiTotal} providers configured`,
      tab: "integrations",
      score: 15,
    });
  }

  const enabledLanguageCodes = new Set(
    supportedLanguages
      .filter((language) => language.enabled)
      .map((language) => language.code.trim().toLowerCase()),
  );
  const usersWithDisabledLanguage = localUsers.filter((user) => {
    const code = user.default_language.trim().toLowerCase();
    return code.length > 0 && enabledLanguageCodes.size > 0 && !enabledLanguageCodes.has(code);
  });

  if (usersWithDisabledLanguage.length > 0) {
    issues.push({
      id: "user-language-drift",
      title: "Some accounts point to disabled languages",
      explanation: `${usersWithDisabledLanguage.length} local user accounts default to languages that are not enabled, which can cause an inconsistent admin or learner experience.`,
      impact: usersWithDisabledLanguage.length >= 3 ? "high" : "medium",
      recommendedAction: "Open Local Users and align default language settings with the currently enabled language set.",
      signal: `${usersWithDisabledLanguage.length} affected accounts`,
      tab: "local-users",
      score: usersWithDisabledLanguage.length >= 3 ? 73 : 61,
    });
  } else if (dashboardSnapshot.languages.enabled_count > 0) {
    healthySignals.push({
      id: "language-coverage-stable",
      title: "Language coverage is aligned",
      explanation: "Enabled platform languages are consistent with current local account defaults, so language drift is not visible in the control plane.",
      impact: "low",
      recommendedAction: "Keep language enablement and account defaults aligned as new cohorts or locales are added.",
      signal: `${dashboardSnapshot.languages.enabled_count}/${dashboardSnapshot.languages.total_count} languages enabled`,
      tab: "languages",
      score: 14,
    });
  }

  const rolelessUsers = localUsers.filter((user) => user.roles.filter((role) => role.trim().length > 0).length === 0);
  if (rolelessUsers.length > 0) {
    issues.push({
      id: "roleless-users",
      title: "Access governance has orphaned accounts",
      explanation: `${rolelessUsers.length} local user accounts have no assigned roles, so access intent is undefined.`,
      impact: rolelessUsers.length >= 2 ? "high" : "medium",
      recommendedAction: "Open RBAC or Local Users and assign the intended role model before the accounts are used operationally.",
      signal: `${rolelessUsers.length} accounts without roles`,
      tab: "rbac",
      score: rolelessUsers.length >= 2 ? 76 : 59,
    });
  }

  issues.sort((left, right) => right.score - left.score);
  healthySignals.sort((left, right) => right.score - left.score);

  const selectedIssues = top(issues, 3, 5);
  if (selectedIssues.length >= 3) {
    return selectedIssues.slice(0, 5);
  }

  return [...selectedIssues, ...healthySignals].slice(0, 5);
}