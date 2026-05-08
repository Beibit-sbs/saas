"use client";

import { AlertTriangle } from "lucide-react";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { Badge } from "@/shared/ui/badge";
import { PERMISSIONS } from "@/shared/config/permissions";

const INCIDENT_STATES = [
  "OPEN",
  "ACKNOWLEDGED",
  "INVESTIGATING",
  "RESOLVED",
  "ESCALATED",
  "DISMISSED",
] as const;

const CONTRACT_EVENTS = [
  "security.incident.opened",
  "security.incident.acknowledged",
  "security.incident.escalated",
  "security.incident.resolved",
  "security.incident.dismissed",
  "campus.security_incident.detected",
] as const;

export default function SecurityOperationsPage() {
  return (
    <RequirePermission permission={PERMISSIONS.SCHEDULING_READ}>
      <div className="space-y-6" data-testid="security-operations-page">
        <PageHeader
          title="Security Operations"
          description="Security incident lifecycle, escalation, and operational signal coverage"
          icon={AlertTriangle}
        />

        <section className="rounded-lg border bg-card p-4" data-testid="security-operations-lifecycle-section">
          <h2 className="text-sm font-semibold">Incident Lifecycle FSM</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {INCIDENT_STATES.map((state) => (
              <Badge key={state} variant="secondary" data-testid={`incident-state-${state}`}>
                {state}
              </Badge>
            ))}
          </div>
        </section>

        <section className="rounded-lg border bg-card p-4" data-testid="security-operations-events-section">
          <h2 className="text-sm font-semibold">Contracted Events</h2>
          <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
            {CONTRACT_EVENTS.map((eventType) => (
              <li key={eventType} data-testid={`contract-event-${eventType}`}>
                {eventType}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </RequirePermission>
  );
}
