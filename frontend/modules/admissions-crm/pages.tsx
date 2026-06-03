"use client";

import { RequirePermission } from "@/shared/ui/permission-gate";
import {
  useAdmissionsCrmApplicant,
  useAdmissionsCrmApplicants,
  useAdmissionsCrmApplication,
  useAdmissionsCrmApplications,
  useAdmissionsCrmLead,
  useAdmissionsCrmLeads,
  useAdmissionsCrmSummary,
  type ApplicantRecord,
  type ApplicationRecord,
  type LeadRecord,
} from "./hooks";
import { ADMISSIONS_CRM_ROUTES, type AdmissionsCrmRouteKey } from "./routeMap";
import {
  ADMISSIONS_CRM_PERMISSION_MATRIX_64,
  hasAnyAdmissionsCrmPermission,
} from "./permissions";
import { AdmissionsPageLayout } from "./components/AdmissionsPageLayout";
import { TenantScopeNotice } from "./components/TenantScopeNotice";
import { DataStatePanel } from "./components/DataStatePanel";
import { AdmissionsFilters } from "./filters/AdmissionsFilters";
import {
  AdmissionsOverviewDashboard,
  ApplicationStatusDashboard,
  PipelineSummaryDashboard,
  RecruitmentProgressDashboard,
  WorkflowHealthDashboard,
} from "./dashboard/AdmissionsDashboards";
import { LeadCreateForm } from "./forms/LeadCreateForm";
import { LeadEditForm } from "./forms/LeadEditForm";
import { ApplicantCreateForm } from "./forms/ApplicantCreateForm";
import { ApplicationCreateForm } from "./forms/ApplicationCreateForm";
import { AssignmentForm } from "./forms/AssignmentForm";
import { NoteForm } from "./forms/NoteForm";
import { LeadTable } from "./tables/LeadTable";
import { ApplicantTable } from "./tables/ApplicantTable";
import { ApplicationTable } from "./tables/ApplicationTable";
import { StatusHistoryPanel } from "./tables/StatusHistoryPanel";
import { WorkflowTimeline } from "./tables/WorkflowTimeline";
import { AuditPanel } from "./tables/AuditPanel";

interface AdmissionsCrmState {
  tenantId?: number;
  leads?: LeadRecord[];
  applicants?: ApplicantRecord[];
  applications?: ApplicationRecord[];
  loading?: boolean;
  error?: string | null;
  incompleteData?: boolean;
}

function getRouteDefinition(routeKey: AdmissionsCrmRouteKey) {
  const route = ADMISSIONS_CRM_ROUTES.find((item) => item.key === routeKey);
  if (!route) {
    throw new Error(`Unknown admissions CRM route key: ${routeKey}`);
  }
  return route;
}

function buildDefaultState(): AdmissionsCrmState {
  return {
    tenantId: undefined,
    leads: [],
    applicants: [],
    applications: [],
    loading: false,
    error: null,
    incompleteData: true,
  };
}

function AdmissionsCrmNoOverclaimFooter() {
  return (
    <footer className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground" data-testid="acrm-no-overclaim-footer">
      <p>Admissions CRM runtime surfaces only tenant-scoped backend records and explicit user actions.</p>
      <p>No synthetic KPI generation, hidden scoring, or autonomous admissions decisions are enabled.</p>
      <p>Human review remains required for transitions, qualification, conversion, and submission actions.</p>
    </footer>
  );
}

function AdmissionsCrmRouteContractPanel({ routeKey }: { routeKey: AdmissionsCrmRouteKey }) {
  const route = getRouteDefinition(routeKey);
  return (
    <section className="rounded-xl border bg-card p-4 text-sm text-muted-foreground" data-testid="acrm-route-contract-panel">
      <p>Route: {route.path}</p>
      <p>Required permissions: {route.requiredPermissions.join(", ")}</p>
      <p>Tenant scoped: {String(route.tenantScoped)}</p>
      <p>Runtime mode: foundation/batch1</p>
    </section>
  );
}

function AdmissionsCrmShell({
  routeKey,
  state,
}: {
  routeKey: AdmissionsCrmRouteKey;
  state: AdmissionsCrmState;
}) {
  const route = getRouteDefinition(routeKey);
  const summaryPayload = {
    leads: state.leads?.length ?? 0,
    applicants: state.applicants?.length ?? 0,
    applications: state.applications?.length ?? 0,
    startedApplications: (state.applications ?? []).filter((item) => item.status === "application_started").length,
    submittedApplications: (state.applications ?? []).filter((item) => item.status === "application_submitted").length,
  };

  const lead = state.leads?.[0] ?? null;
  const applicant = state.applicants?.[0] ?? null;
  const application = state.applications?.[0] ?? null;

  const title = route.title;
  const subtitle = "Admissions CRM foundation runtime view. Tenant-safe and permission-safe by default.";

  return (
    <AdmissionsPageLayout title={title} subtitle={subtitle}>
      <div className="space-y-4" data-testid={`acrm-page-${routeKey}`}>
        <TenantScopeNotice tenantId={state.tenantId} />
        <DataStatePanel
          loading={state.loading}
          error={state.error}
          empty={!state.loading && !state.error && (state.incompleteData || !state.leads?.length && !state.applicants?.length && !state.applications?.length)}
          emptyMessage="No admissions records available in current tenant scope."
        />

        <AdmissionsFilters />

        {routeKey === "overview" ? <AdmissionsOverviewDashboard payload={summaryPayload} /> : null}
        {routeKey === "dashboard" ? (
          <div className="space-y-4">
            <AdmissionsOverviewDashboard payload={summaryPayload} />
            <PipelineSummaryDashboard payload={summaryPayload} />
            <WorkflowHealthDashboard payload={summaryPayload} />
            <ApplicationStatusDashboard payload={summaryPayload} />
            <RecruitmentProgressDashboard payload={summaryPayload} />
          </div>
        ) : null}

        {routeKey === "leads" ? <LeadTable leads={state.leads ?? []} /> : null}
        {routeKey === "leads-new" ? <LeadCreateForm /> : null}
        {routeKey === "lead-detail" ? (
          <div className="space-y-4">
            <LeadTable leads={lead ? [lead] : []} />
            <LeadEditForm
              initial={lead ? { full_name: lead.full_name, email: lead.email, phone: lead.phone ?? "", source_channel: lead.source_channel } : undefined}
            />
            <StatusHistoryPanel title="Lead Status History" history={lead ? [lead.status] : []} />
            <AssignmentForm />
            <NoteForm />
          </div>
        ) : null}

        {routeKey === "applicants" ? <ApplicantTable applicants={state.applicants ?? []} /> : null}
        {routeKey === "applicants-new" ? <ApplicantCreateForm /> : null}
        {routeKey === "applicant-detail" ? (
          <div className="space-y-4">
            <ApplicantTable applicants={applicant ? [applicant] : []} />
            <StatusHistoryPanel title="Applicant Status History" history={applicant ? [applicant.status] : []} />
            <ApplicationCreateForm />
            <AssignmentForm />
            <NoteForm />
          </div>
        ) : null}

        {routeKey === "applications" ? <ApplicationTable applications={state.applications ?? []} /> : null}
        {routeKey === "applications-new" ? <ApplicationCreateForm /> : null}
        {routeKey === "application-detail" ? (
          <div className="space-y-4">
            <ApplicationTable applications={application ? [application] : []} />
            <StatusHistoryPanel title="Application Status History" history={application ? [application.status] : []} />
            <NoteForm />
          </div>
        ) : null}

        {routeKey === "workflows" ? (
          <div className="space-y-4">
            <WorkflowHealthDashboard payload={summaryPayload} />
            <WorkflowTimeline
              items={[
                { label: "Lead", state: lead?.status ?? "unknown" },
                { label: "Applicant", state: applicant?.status ?? "unknown" },
                { label: "Application", state: application?.status ?? "unknown" },
              ]}
            />
          </div>
        ) : null}

        {routeKey === "audit" ? (
          <AuditPanel
            rows={[
              { action: "read", entity: "lead_registry", actor: "current_user" },
              { action: "read", entity: "applicant_registry", actor: "current_user" },
              { action: "read", entity: "application_registry", actor: "current_user" },
            ]}
          />
        ) : null}

        {routeKey === "settings-permissions" ? (
          <section className="rounded-xl border bg-card p-4" data-testid="acrm-permission-matrix-panel">
            <h3 className="text-base font-semibold">Admissions CRM Permission Matrix</h3>
            <p className="mt-1 text-sm text-muted-foreground">Batch1 runtime exposes capability map only; no synthetic privilege escalation tools.</p>
            <div className="mt-3 grid gap-2 md:grid-cols-2 lg:grid-cols-3">
              {ADMISSIONS_CRM_PERMISSION_MATRIX_64.map((permission) => (
                <div key={permission} className="rounded border px-3 py-2 text-xs font-mono">
                  {permission}
                </div>
              ))}
            </div>
          </section>
        ) : null}

        <AdmissionsCrmRouteContractPanel routeKey={routeKey} />
        <AdmissionsCrmNoOverclaimFooter />
      </div>
    </AdmissionsPageLayout>
  );
}

function AdmissionsCrmLivePage({
  routeKey,
  leadId,
  applicantId,
  applicationId,
}: {
  routeKey: AdmissionsCrmRouteKey;
  leadId?: number;
  applicantId?: number;
  applicationId?: number;
}) {
  const leadsQuery = useAdmissionsCrmLeads();
  const applicantsQuery = useAdmissionsCrmApplicants();
  const applicationsQuery = useAdmissionsCrmApplications();
  const leadQuery = useAdmissionsCrmLead(leadId ?? null);
  const applicantQuery = useAdmissionsCrmApplicant(applicantId ?? null);
  const applicationQuery = useAdmissionsCrmApplication(applicationId ?? null);
  const summary = useAdmissionsCrmSummary();

  const state: AdmissionsCrmState = {
    tenantId:
      leadsQuery.data?.tenant_id
      ?? applicantsQuery.data?.tenant_id
      ?? applicationsQuery.data?.tenant_id,
    leads: routeKey === "lead-detail" ? (leadQuery.data?.item ? [leadQuery.data.item] : []) : (leadsQuery.data?.items ?? []),
    applicants: routeKey === "applicant-detail" ? (applicantQuery.data?.item ? [applicantQuery.data.item] : []) : (applicantsQuery.data?.items ?? []),
    applications: routeKey === "application-detail" ? (applicationQuery.data?.item ? [applicationQuery.data.item] : []) : (applicationsQuery.data?.items ?? []),
    loading:
      leadsQuery.isLoading
      || applicantsQuery.isLoading
      || applicationsQuery.isLoading
      || leadQuery.isLoading
      || applicantQuery.isLoading
      || applicationQuery.isLoading
      || summary.isLoading,
    error:
      (leadsQuery.error as Error | null)?.message
      || (applicantsQuery.error as Error | null)?.message
      || (applicationsQuery.error as Error | null)?.message
      || (leadQuery.error as Error | null)?.message
      || (applicantQuery.error as Error | null)?.message
      || (applicationQuery.error as Error | null)?.message
      || (summary.errors[0] as Error | undefined)?.message
      || null,
    incompleteData: summary.summary.hasIncompleteData,
  };

  return <AdmissionsCrmShell routeKey={routeKey} state={state} />;
}

export function AdmissionsCrmPage({
  routeKey,
  userPermissions,
  stateOverride,
  leadId,
  applicantId,
  applicationId,
}: {
  routeKey: AdmissionsCrmRouteKey;
  userPermissions?: string[];
  stateOverride?: AdmissionsCrmState;
  leadId?: number;
  applicantId?: number;
  applicationId?: number;
}) {
  const route = getRouteDefinition(routeKey);

  if (userPermissions) {
    return hasAnyAdmissionsCrmPermission(userPermissions, route.requiredPermissions)
      ? <AdmissionsCrmShell routeKey={routeKey} state={{ ...buildDefaultState(), ...stateOverride }} />
      : <div data-testid="acrm-permission-denied-state" className="rounded-xl border border-destructive/30 bg-destructive/5 p-4">This Admissions CRM route is fail-closed until required permission is granted.</div>;
  }

  const primaryPermission = route.requiredPermissions[0];
  return (
    <RequirePermission permission={primaryPermission as never} message="This Admissions CRM route is fail-closed until the required permission is granted.">
      <AdmissionsCrmLivePage routeKey={routeKey} leadId={leadId} applicantId={applicantId} applicationId={applicationId} />
    </RequirePermission>
  );
}
