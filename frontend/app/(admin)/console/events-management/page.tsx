"use client";

import { CalendarDays } from "lucide-react";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { Badge } from "@/shared/ui/badge";
import { PERMISSIONS } from "@/shared/config/permissions";

const LIFECYCLE_STATES = [
  "DRAFT",
  "PUBLISHED",
  "REGISTRATION_OPEN",
  "IN_PROGRESS",
  "COMPLETED",
  "CANCELLED",
] as const;

const CONTRACT_EVENTS = [
  "event.created",
  "event.published",
  "event.registration_opened",
  "event.registration_full",
  "event.started",
  "event.completed",
  "event.cancelled",
] as const;

export default function EventsManagementPage() {
  return (
    <RequirePermission permission={PERMISSIONS.SCHEDULING_READ}>
      <div className="space-y-6" data-testid="events-management-page">
        <PageHeader
          title="Events Management"
          description="Campus events lifecycle, registration readiness, and operational signal coverage"
          icon={CalendarDays}
        />

        <section className="rounded-lg border bg-card p-4" data-testid="events-management-lifecycle-section">
          <h2 className="text-sm font-semibold">Lifecycle FSM</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {LIFECYCLE_STATES.map((state) => (
              <Badge key={state} variant="secondary" data-testid={`event-state-${state}`}>
                {state}
              </Badge>
            ))}
          </div>
        </section>

        <section className="rounded-lg border bg-card p-4" data-testid="events-management-events-section">
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
