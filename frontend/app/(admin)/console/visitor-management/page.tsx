"use client";

import { ShieldCheck } from "lucide-react";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { Badge } from "@/shared/ui/badge";
import { PERMISSIONS } from "@/shared/config/permissions";

const LIFECYCLE_STATES = [
  "REQUESTED",
  "APPROVED",
  "REJECTED",
  "CHECKED_IN",
  "CHECKED_OUT",
  "EXPIRED",
  "CANCELLED",
] as const;

const CONTRACT_EVENTS = [
  "visitor.registered",
  "visitor.approved",
  "visitor.rejected",
  "visitor.checked_in",
  "visitor.checked_out",
  "visitor.expired",
  "visitor.cancelled",
  "visitor.unauthorized_attempt",
] as const;

export default function VisitorManagementPage() {
  return (
    <RequirePermission permission={PERMISSIONS.SCHEDULING_READ}>
      <div className="space-y-6" data-testid="visitor-management-page">
        <PageHeader
          title="Visitor Management"
          description="Visitor lifecycle, check-in/check-out, and unauthorized access signal coverage"
          icon={ShieldCheck}
        />

        <section className="rounded-lg border bg-card p-4" data-testid="visitor-management-lifecycle-section">
          <h2 className="text-sm font-semibold">Lifecycle FSM</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {LIFECYCLE_STATES.map((state) => (
              <Badge key={state} variant="secondary" data-testid={`visitor-state-${state}`}>
                {state}
              </Badge>
            ))}
          </div>
        </section>

        <section className="rounded-lg border bg-card p-4" data-testid="visitor-management-events-section">
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
