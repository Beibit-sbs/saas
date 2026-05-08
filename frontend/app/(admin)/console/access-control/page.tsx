"use client";

import { KeyRound } from "lucide-react";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { Badge } from "@/shared/ui/badge";
import { PERMISSIONS } from "@/shared/config/permissions";

const CARD_STATES = ["ACTIVE", "SUSPENDED", "REVOKED"] as const;

const CONTRACT_EVENTS = [
  "access.granted",
  "access.denied",
  "card.issued",
  "card.suspended",
  "card.revoked",
  "card.reactivated",
  "security.anomaly",
] as const;

export default function AccessControlPage() {
  return (
    <RequirePermission permission={PERMISSIONS.SCHEDULING_READ}>
      <div className="space-y-6" data-testid="access-control-page">
        <PageHeader
          title="Access Control"
          description="Card lifecycle and access signal coverage without hardware control actions"
          icon={KeyRound}
        />

        <section className="rounded-lg border bg-card p-4" data-testid="access-control-lifecycle-section">
          <h2 className="text-sm font-semibold">Card Lifecycle FSM</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {CARD_STATES.map((state) => (
              <Badge key={state} variant="secondary" data-testid={`card-state-${state}`}>
                {state}
              </Badge>
            ))}
          </div>
        </section>

        <section className="rounded-lg border bg-card p-4" data-testid="access-control-events-section">
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
