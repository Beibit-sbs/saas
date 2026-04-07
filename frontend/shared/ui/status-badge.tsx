"use client";

import { Badge } from "./badge";
import { capitalize } from "../utils/format";

type StatusVariant = "default" | "secondary" | "destructive" | "outline" | "success" | "warning" | "info";

const STATUS_MAP: Record<string, StatusVariant> = {
  active: "success",
  enabled: "success",
  succeeded: "success",
  completed: "success",
  sent: "success",
  ok: "success",
  healthy: "success",
  reachable: "success",

  queued: "info",
  running: "info",
  pending: "info",
  "in-progress": "info",
  processing: "info",

  suspended: "warning",
  inactive: "warning",
  retrying: "warning",
  degraded: "warning",
  planned: "warning",
  scheduled: "info",

  failed: "destructive",
  error: "destructive",
  cancelled: "destructive",
  unreachable: "destructive",
  disabled: "secondary",
  unknown: "secondary",
};

interface StatusBadgeProps {
  status: string | null | undefined;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  if (!status) return <Badge variant="secondary" className={className}>—</Badge>;
  const normalized = status.toLowerCase().replace(/\s+/g, "-");
  const variant = STATUS_MAP[normalized] ?? "secondary";
  return (
    <Badge variant={variant} className={className}>
      {capitalize(status)}
    </Badge>
  );
}
