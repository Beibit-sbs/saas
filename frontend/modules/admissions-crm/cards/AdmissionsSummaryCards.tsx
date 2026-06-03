"use client";

export interface SummaryCardsPayload {
  leads: number;
  applicants: number;
  applications: number;
  submittedApplications: number;
  startedApplications: number;
}

function Card({ title, value }: { title: string; value: number }) {
  return (
    <article className="rounded-xl border bg-card p-4" data-testid={`acrm-card-${title.toLowerCase().replace(/\s+/g, "-")}`}>
      <h3 className="text-xs uppercase text-muted-foreground">{title}</h3>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
    </article>
  );
}

export function AdmissionsSummaryCards({ payload }: { payload: SummaryCardsPayload }) {
  return (
    <section className="grid gap-3 md:grid-cols-3 lg:grid-cols-5" data-testid="acrm-summary-cards">
      <Card title="Leads" value={payload.leads} />
      <Card title="Applicants" value={payload.applicants} />
      <Card title="Applications" value={payload.applications} />
      <Card title="Started" value={payload.startedApplications} />
      <Card title="Submitted" value={payload.submittedApplications} />
    </section>
  );
}

export function PipelineSummaryCards({ payload }: { payload: SummaryCardsPayload }) {
  const leadToApplicant = payload.leads === 0 ? 0 : Math.round((payload.applicants / payload.leads) * 100);
  const applicantToApplication = payload.applicants === 0 ? 0 : Math.round((payload.applications / payload.applicants) * 100);
  return (
    <section className="grid gap-3 md:grid-cols-2" data-testid="acrm-pipeline-summary-cards">
      <Card title="Lead->Applicant %" value={leadToApplicant} />
      <Card title="Applicant->Application %" value={applicantToApplication} />
    </section>
  );
}

export function WorkflowHealthCards({ payload }: { payload: SummaryCardsPayload }) {
  return (
    <section className="grid gap-3 md:grid-cols-2" data-testid="acrm-workflow-health-cards">
      <Card title="Started Applications" value={payload.startedApplications} />
      <Card title="Submitted Applications" value={payload.submittedApplications} />
    </section>
  );
}

export function ApplicationStatusCards({ payload }: { payload: SummaryCardsPayload }) {
  return (
    <section className="grid gap-3 md:grid-cols-3" data-testid="acrm-application-status-cards">
      <Card title="Total Applications" value={payload.applications} />
      <Card title="Started" value={payload.startedApplications} />
      <Card title="Submitted" value={payload.submittedApplications} />
    </section>
  );
}

export function RecruitmentProgressCards({ payload }: { payload: SummaryCardsPayload }) {
  return (
    <section className="grid gap-3 md:grid-cols-2" data-testid="acrm-recruitment-progress-cards">
      <Card title="Lead Volume" value={payload.leads} />
      <Card title="Qualified Pipeline" value={payload.applicants} />
    </section>
  );
}
