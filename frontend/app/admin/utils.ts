import type { FeatureFlag } from "./types";

export function formatAuditTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function formatFeatureFlagLastChange(flag: FeatureFlag): string {
  const meta = flag.metadata;
  const actorCandidates: unknown[] = [
    flag.last_changed_by,
    flag.updated_by,
    meta?.last_changed_by,
    meta?.updated_by,
    meta?.actor,
  ];
  const timestampCandidates: unknown[] = [
    flag.last_changed_at,
    flag.updated_at,
    meta?.last_changed_at,
    meta?.updated_at,
    meta?.timestamp,
  ];
  const actor = actorCandidates.find((item) => typeof item === "string" && item.trim()) as string | undefined;
  const timestamp = timestampCandidates.find((item) => typeof item === "string" && item.trim()) as string | undefined;

  if (!actor && !timestamp) {
    return "";
  }

  if (actor && timestamp) {
    return `${actor} • ${formatAuditTimestamp(timestamp)}`;
  }

  return actor || formatAuditTimestamp(timestamp || "");
}

export function formatBytes(size: number | undefined): string {
  if (!size || size < 0) {
    return "-";
  }
  if (size < 1024) {
    return `${size} B`;
  }
  const kb = size / 1024;
  if (kb < 1024) {
    return `${kb.toFixed(1)} KB`;
  }
  const mb = kb / 1024;
  if (mb < 1024) {
    return `${mb.toFixed(1)} MB`;
  }
  return `${(mb / 1024).toFixed(2)} GB`;
}

export function fileNameFromPath(path: string): string {
  const normalized = String(path || "").trim();
  if (!normalized) {
    return "-";
  }
  const parts = normalized.split("/");
  return parts[parts.length - 1] || normalized;
}

export function backupStatusBadgeClass(status: string): string {
  const normalized = String(status || "").toLowerCase();
  if (normalized.includes("success") || normalized === "done") {
    return "badgeOk";
  }
  if (normalized.includes("run") || normalized.includes("progress") || normalized === "planned") {
    return "badgeWarn";
  }
  if (normalized.includes("fail") || normalized.includes("error")) {
    return "badgeErr";
  }
  return "badgeInfo";
}