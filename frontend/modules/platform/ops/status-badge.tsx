import { Badge } from "@/shared/ui/badge";
import type { OpsStatus } from "./types";

interface OpsStatusBadgeProps {
  status: OpsStatus;
}

const LABELS: Record<OpsStatus, string> = {
  healthy: "Healthy",
  degraded: "Degraded",
  critical: "Critical",
  skipped: "Skipped",
  unknown: "Unknown",
};

const VARIANTS: Record<OpsStatus, "success" | "warning" | "destructive" | "secondary"> = {
  healthy: "success",
  degraded: "warning",
  critical: "destructive",
  skipped: "secondary",
  unknown: "secondary",
};

export function OpsStatusBadge({ status }: OpsStatusBadgeProps) {
  return <Badge variant={VARIANTS[status]}>{LABELS[status]}</Badge>;
}