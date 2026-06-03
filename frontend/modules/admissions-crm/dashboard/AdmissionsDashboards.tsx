"use client";

import type { ReactNode } from "react";
import type { SummaryCardsPayload } from "../cards/AdmissionsSummaryCards";
import {
  AdmissionsSummaryCards,
  ApplicationStatusCards,
  PipelineSummaryCards,
  RecruitmentProgressCards,
  WorkflowHealthCards,
} from "../cards/AdmissionsSummaryCards";

function DashboardShell({ title, description, children }: { title: string; description: string; children: ReactNode }) {
  return (
    <section className="space-y-4 rounded-xl border bg-card p-4" data-testid={`acrm-dashboard-${title.toLowerCase().replace(/\s+/g, "-")}`}>
      <header>
        <h3 className="text-base font-semibold">{title}</h3>
        <p className="text-sm text-muted-foreground">{description}</p>
      </header>
      {children}
    </section>
  );
}

export function AdmissionsOverviewDashboard({ payload }: { payload: SummaryCardsPayload }) {
  return (
    <DashboardShell title="Admissions Overview" description="Tenant-scoped operational snapshot from live backend records.">
      <AdmissionsSummaryCards payload={payload} />
    </DashboardShell>
  );
}

export function PipelineSummaryDashboard({ payload }: { payload: SummaryCardsPayload }) {
  return (
    <DashboardShell title="Pipeline Summary" description="Conversion flow summary from lead, applicant, and application entities.">
      <PipelineSummaryCards payload={payload} />
    </DashboardShell>
  );
}

export function WorkflowHealthDashboard({ payload }: { payload: SummaryCardsPayload }) {
  return (
    <DashboardShell title="Workflow Health" description="Status-only health indicators without synthetic workflow metrics.">
      <WorkflowHealthCards payload={payload} />
    </DashboardShell>
  );
}

export function ApplicationStatusDashboard({ payload }: { payload: SummaryCardsPayload }) {
  return (
    <DashboardShell title="Application Status" description="Application state totals from current tenant records.">
      <ApplicationStatusCards payload={payload} />
    </DashboardShell>
  );
}

export function RecruitmentProgressDashboard({ payload }: { payload: SummaryCardsPayload }) {
  return (
    <DashboardShell title="Recruitment Progress" description="Lead and applicant movement without campaign analytics overreach.">
      <RecruitmentProgressCards payload={payload} />
    </DashboardShell>
  );
}
