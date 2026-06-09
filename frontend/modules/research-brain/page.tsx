'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { RequirePermission } from '@/shared/ui/permission-gate';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';
import { PERMISSIONS } from '@/shared/config/permissions';
import { researchBrainApi } from './api';
import type { Researcher } from './types';

function MetricCard({ label, value, helper }: { label: string; value: string | number; helper?: string }) {
  return (
    <div className="rounded-lg border p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
      {helper ? <p className="mt-1 text-xs text-muted-foreground">{helper}</p> : null}
    </div>
  );
}

export function ResearchBrainRuntimeShellPage() {
  const shell = useQuery({ queryKey: ['research-brain:shell'], queryFn: researchBrainApi.getShell, staleTime: 60000 });
  const orchestration = useQuery({ queryKey: ['research-brain:orchestration'], queryFn: researchBrainApi.getOrchestration, staleTime: 30000 });
  const context = useQuery({ queryKey: ['research-brain:context'], queryFn: researchBrainApi.getContext, staleTime: 30000 });
  const kpis = useQuery({ queryKey: ['research-brain:kpis'], queryFn: researchBrainApi.getKpis, staleTime: 30000 });
  const signals = useQuery({ queryKey: ['research-brain:signals'], queryFn: researchBrainApi.getSignals, staleTime: 30000 });
  const rbac = useQuery({ queryKey: ['research-brain:rbac'], queryFn: researchBrainApi.getRbacValidation, staleTime: 30000 });

  if (shell.isPending || orchestration.isPending || context.isPending || kpis.isPending || signals.isPending || rbac.isPending) {
    return <LoadingState title="Loading Research Brain runtime shell" />;
  }

  if (shell.error || orchestration.error || context.error || kpis.error || signals.error || rbac.error) {
    return <ErrorState message="Failed to load Research Brain runtime shell." error={shell.error ?? orchestration.error ?? context.error ?? kpis.error ?? signals.error ?? rbac.error} />;
  }

  if (!shell.data || !orchestration.data || !context.data || !kpis.data || !signals.data || !rbac.data) {
    return <ErrorState message="Research Brain runtime shell is unavailable." />;
  }

  return (
    <RequirePermission permission={PERMISSIONS.RESEARCH_SCIENCE_OVERVIEW_READ}>
      <div className="space-y-6" data-testid="research-brain-runtime-shell">
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold">Research Brain Runtime Shell</h1>
          <p className="text-sm text-muted-foreground">
            Unified read-only shell over existing canonicals and approved bridge contracts. No live provider integrations.
          </p>
        </header>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Publications" value={kpis.data.publication_count} helper="Analytics-owned KPI surface" />
          <MetricCard label="Grants" value={kpis.data.grant_count} helper="Analytics-owned KPI surface" />
          <MetricCard label="Projects" value={kpis.data.project_count} helper="Analytics-owned KPI surface" />
          <MetricCard label="Ethics" value={kpis.data.ethics_count} helper="Analytics-owned KPI surface" />
        </div>

        <section className="rounded-lg border p-4" data-testid="research-brain-bridge-modules">
          <h2 className="text-lg font-semibold">Bridge Modules</h2>
          <p className="mt-1 text-sm text-muted-foreground">Owner: {shell.data.owner_module}. Boundary: {shell.data.runtime_boundary}.</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {shell.data.bridge_modules.map((bridge) => (
              <span key={bridge} className="rounded-full border px-3 py-1 text-xs">{bridge}</span>
            ))}
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-2" data-testid="research-brain-orchestration">
          {Object.entries(orchestration.data)
            .filter(([key]) => key !== 'tenant_id')
            .map(([key, item]) => {
              const typed = item as { source_module: string; read_only: boolean; total: number; notes: string };
              return (
                <div key={key} className="rounded-lg border p-4">
                  <h3 className="font-medium capitalize">{key}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">Source: {typed.source_module}</p>
                  <p className="mt-1 text-sm">Total: {typed.total}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{typed.notes}</p>
                </div>
              );
            })}
        </section>

        <section className="rounded-lg border p-4" data-testid="research-brain-signals">
          <h2 className="text-lg font-semibold">Signal Exposure</h2>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {signals.data.signals.map((signal) => (
              <div key={signal.family} className="rounded-lg border p-3">
                <p className="font-medium">{signal.family}</p>
                <p className="text-sm text-muted-foreground">Owner: {signal.owner}</p>
                <p className="text-sm text-muted-foreground">Review queue: {signal.review_queue}</p>
                <p className="text-sm">Observed: {signal.observed_count}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="research-brain-rbac-validation">
          <h2 className="text-lg font-semibold">RBAC Validation</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            tenant={rbac.data.tenant}, rbac={rbac.data.rbac}, audit={rbac.data.audit}
          </p>
          <ul className="mt-3 space-y-1 text-sm">
            {rbac.data.roles.map((role) => (
              <li key={role.role}>{role.role}: {role.status}</li>
            ))}
          </ul>
        </section>

        <section className="rounded-lg border p-4" data-testid="research-brain-navigation-links">
          <h2 className="text-lg font-semibold">Runtime Navigation</h2>
          <div className="mt-3 flex flex-wrap gap-2 text-sm">
            <Link href="/console/research-science" className="rounded-full border px-3 py-1">Research Science Overview</Link>
            <Link href="/console/research-science/dashboard" className="rounded-full border px-3 py-1">Research Science Dashboard</Link>
            <Link href="/console/research-brain/researchers" className="rounded-full border px-3 py-1">Researcher Registry</Link>
            <Link href="/console/research-brain/scientometrics" className="rounded-full border px-3 py-1">Scientometrics</Link>
            <Link href="/console/research-brain/risk" className="rounded-full border px-3 py-1">Research Risk</Link>
            <Link href="/console/research-grants" className="rounded-full border px-3 py-1">Research Grants</Link>
            <Link href="/console/research-ethics" className="rounded-full border px-3 py-1">Research Ethics</Link>
          </div>
        </section>
      </div>
    </RequirePermission>
  );
}

export function ResearchBrainResearchersPage() {
  const researchers = useQuery({ queryKey: ['research-brain:researchers'], queryFn: researchBrainApi.listResearchers, staleTime: 30000 });
  const summary = useQuery({ queryKey: ['research-brain:researchers-summary'], queryFn: researchBrainApi.getResearcherSummary, staleTime: 30000 });

  const selectedResearcherId = researchers.data?.items?.[0]?.researcher_id;

  const profile = useQuery({
    queryKey: ['research-brain:researcher-profile', selectedResearcherId],
    queryFn: () => researchBrainApi.getResearcher(selectedResearcherId as string),
    enabled: Boolean(selectedResearcherId),
    staleTime: 30000,
  });

  const activity = useQuery({
    queryKey: ['research-brain:researcher-activity', selectedResearcherId],
    queryFn: () => researchBrainApi.getResearcherActivity(selectedResearcherId as string),
    enabled: Boolean(selectedResearcherId),
    staleTime: 30000,
  });

  const risk = useQuery({
    queryKey: ['research-brain:researcher-risk', selectedResearcherId],
    queryFn: () => researchBrainApi.getResearcherRisk(selectedResearcherId as string),
    enabled: Boolean(selectedResearcherId),
    staleTime: 30000,
  });

  if (researchers.isPending || summary.isPending || profile.isPending || activity.isPending || risk.isPending) {
    return <LoadingState title="Loading Researcher Registry runtime" />;
  }

  if (researchers.error || summary.error || profile.error || activity.error || risk.error) {
    return <ErrorState message="Failed to load Researcher Registry runtime." error={researchers.error ?? summary.error ?? profile.error ?? activity.error ?? risk.error} />;
  }

  if (!researchers.data || !summary.data || !profile.data || !activity.data || !risk.data) {
    return <ErrorState message="Researcher Registry runtime is unavailable." />;
  }

  const selected = profile.data;
  const selectedActivity = activity.data;
  const selectedRisk = risk.data;

  return (
    <RequirePermission permission={PERMISSIONS.RESEARCH_SCIENCE_OVERVIEW_READ}>
      <div className="space-y-6" data-testid="research-brain-researchers-page">
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold">Researcher Registry Runtime</h1>
          <p className="text-sm text-muted-foreground">
            Canonical researcher registry under Research Brain. Read-only runtime with provider-ready boundaries and no live external integrations.
          </p>
        </header>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Researchers" value={summary.data.total_researchers} helper="Canonical registry size" />
          <MetricCard label="Active Researchers" value={summary.data.active_researchers} helper="Status-driven" />
          <MetricCard label="High Risk" value={summary.data.high_risk_researchers} helper="Brain-core signal consumer" />
          <MetricCard label="Publications" value={summary.data.publication_total} helper="Metadata-derived" />
        </div>

        <section className="rounded-lg border p-4" data-testid="researcher-registry-list">
          <h2 className="text-lg font-semibold">Researcher Registry</h2>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {researchers.data.items.map((item: Researcher) => (
              <div key={item.researcher_id} className="rounded-lg border p-3">
                <p className="font-medium">{item.full_name}</p>
                <p className="text-sm text-muted-foreground">{item.researcher_id}</p>
                <p className="text-sm">Projects: {item.active_projects} | Grants: {item.active_grants}</p>
                <p className="text-sm">Publications: {item.publication_count} | Citations: {item.citation_count}</p>
                <p className="text-sm">Risk: {item.risk_level}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-lg border p-4" data-testid="researcher-profile-view">
            <h2 className="text-lg font-semibold">Researcher Profile</h2>
            <p className="mt-2 text-sm">Employee ID: {selected.employee_id}</p>
            <p className="text-sm">Position: {selected.position}</p>
            <p className="text-sm">Department: {selected.department ?? 'n/a'}</p>
            <p className="text-sm">Laboratory: {selected.laboratory ?? 'n/a'}</p>
            <p className="text-sm">Research Areas: {selected.research_areas.join(', ')}</p>
            <p className="text-sm">Specializations: {selected.specializations.join(', ')}</p>
          </div>

          <div className="rounded-lg border p-4" data-testid="researcher-workload-view">
            <h2 className="text-lg font-semibold">Researcher Workload</h2>
            <p className="mt-2 text-sm">Active Projects: {selectedActivity.project_summary.active_projects}</p>
            <p className="text-sm">Active Grants: {selectedActivity.grant_summary.active_grants}</p>
            <p className="text-sm">Publications: {selectedActivity.publication_summary.publication_count}</p>
            <p className="text-sm">Citations: {selectedActivity.publication_summary.citation_count}</p>
            <p className="text-sm">h-index: {selectedActivity.scientometric_summary.h_index}</p>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-lg border p-4" data-testid="researcher-grants-view">
            <h2 className="text-lg font-semibold">Researcher Grants</h2>
            <p className="mt-2 text-sm">Active Grants: {selectedActivity.grant_summary.active_grants}</p>
            <p className="text-xs text-muted-foreground">Read-only grant visibility bridged from research_science and research_grants.</p>
          </div>

          <div className="rounded-lg border p-4" data-testid="researcher-publications-view">
            <h2 className="text-lg font-semibold">Researcher Publications</h2>
            <p className="mt-2 text-sm">Publication Count: {selectedActivity.publication_summary.publication_count}</p>
            <p className="text-sm">Citation Count: {selectedActivity.publication_summary.citation_count}</p>
            <p className="text-xs text-muted-foreground">Provider-ready only: no Scopus/WoS/ORCID/Scholar live integrations.</p>
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="researcher-risk-view">
          <h2 className="text-lg font-semibold">Researcher Risk</h2>
          <p className="mt-2 text-sm">Risk Level: {selectedRisk.risk_level}</p>
          <p className="text-sm">Signals: {selectedRisk.signals.join(', ') || 'none'}</p>
          <ul className="mt-2 list-disc pl-5 text-sm">
            {selectedRisk.notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </section>
      </div>
    </RequirePermission>
  );
}

export function ResearchBrainScientometricsPage() {
  const dashboard = useQuery({ queryKey: ['research-brain:scientometrics-dashboard'], queryFn: researchBrainApi.getScientometricsDashboard, staleTime: 30000 });
  const ranking = useQuery({ queryKey: ['research-brain:scientometrics-ranking'], queryFn: researchBrainApi.getScientometricRanking, staleTime: 30000 });
  const researchers = useQuery({ queryKey: ['research-brain:researchers'], queryFn: researchBrainApi.listResearchers, staleTime: 30000 });

  const selectedResearcherId = researchers.data?.items?.[0]?.researcher_id;

  const profile = useQuery({
    queryKey: ['research-brain:scientometric-profile', selectedResearcherId],
    queryFn: () => researchBrainApi.getResearcherScientometrics(selectedResearcherId as string),
    enabled: Boolean(selectedResearcherId),
    staleTime: 30000,
  });

  const citation = useQuery({
    queryKey: ['research-brain:scientometric-citation', selectedResearcherId],
    queryFn: () => researchBrainApi.getResearcherCitationAnalytics(selectedResearcherId as string),
    enabled: Boolean(selectedResearcherId),
    staleTime: 30000,
  });

  const impact = useQuery({
    queryKey: ['research-brain:scientometric-impact', selectedResearcherId],
    queryFn: () => researchBrainApi.getResearcherImpactAnalytics(selectedResearcherId as string),
    enabled: Boolean(selectedResearcherId),
    staleTime: 30000,
  });

  const publicationImpact = useQuery({
    queryKey: ['research-brain:scientometric-publication-impact', selectedResearcherId],
    queryFn: () => researchBrainApi.getResearcherPublicationImpact(selectedResearcherId as string),
    enabled: Boolean(selectedResearcherId),
    staleTime: 30000,
  });

  const trends = useQuery({
    queryKey: ['research-brain:scientometric-trends', selectedResearcherId],
    queryFn: () => researchBrainApi.getResearcherScientometricTrends(selectedResearcherId as string),
    enabled: Boolean(selectedResearcherId),
    staleTime: 30000,
  });

  if (
    dashboard.isPending ||
    ranking.isPending ||
    researchers.isPending ||
    profile.isPending ||
    citation.isPending ||
    impact.isPending ||
    publicationImpact.isPending ||
    trends.isPending
  ) {
    return <LoadingState title="Loading Scientometrics runtime" />;
  }

  if (
    dashboard.error ||
    ranking.error ||
    researchers.error ||
    profile.error ||
    citation.error ||
    impact.error ||
    publicationImpact.error ||
    trends.error
  ) {
    return (
      <ErrorState
        message="Failed to load Scientometrics runtime."
        error={
          dashboard.error ??
          ranking.error ??
          researchers.error ??
          profile.error ??
          citation.error ??
          impact.error ??
          publicationImpact.error ??
          trends.error
        }
      />
    );
  }

  if (!dashboard.data || !ranking.data || !profile.data || !citation.data || !impact.data || !publicationImpact.data || !trends.data) {
    return <ErrorState message="Scientometrics runtime is unavailable." />;
  }

  return (
    <RequirePermission permission={PERMISSIONS.RESEARCH_SCIENCE_OVERVIEW_READ}>
      <div className="space-y-6" data-testid="research-brain-scientometrics-page">
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold">Scientometrics and Citation Analytics Runtime</h1>
          <p className="text-sm text-muted-foreground">
            Analytics-owned scientometrics runtime with provider-ready identities only. No live ORCID, Scopus, Web of Science, Google Scholar, or DOI synchronization.
          </p>
        </header>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Top Researchers" value={dashboard.data.top_researchers.length} helper="Scientometrics dashboard widget" />
          <MetricCard label="Citation Leaderboard" value={dashboard.data.citation_leaderboard.length} helper="Read-only citation analytics" />
          <MetricCard label="h-index Leaderboard" value={dashboard.data.h_index_leaderboard.length} helper="Read-only impact analytics" />
          <MetricCard label="Publication Impact Profiles" value={dashboard.data.publication_impact_summary.length} helper="Bridge-backed publication impact" />
        </div>

        <section className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-lg border p-4" data-testid="scientometrics-top-researchers-widget">
            <h2 className="text-lg font-semibold">Top Researchers</h2>
            <ul className="mt-2 space-y-1 text-sm">
              {dashboard.data.top_researchers.map((item) => (
                <li key={item.researcher_id}>{item.researcher_id}: impact {item.impact_score}</li>
              ))}
            </ul>
          </div>
          <div className="rounded-lg border p-4" data-testid="scientometrics-researcher-ranking-widget">
            <h2 className="text-lg font-semibold">Researcher Ranking</h2>
            <ul className="mt-2 space-y-1 text-sm">
              {ranking.data.items.map((item) => (
                <li key={item.researcher_id}>#{item.rank} {item.researcher_id} (risk {item.scientometric_risk})</li>
              ))}
            </ul>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-lg border p-4" data-testid="scientometrics-citation-leaderboard-widget">
            <h2 className="text-lg font-semibold">Citation Leaderboard</h2>
            <ul className="mt-2 space-y-1 text-sm">
              {dashboard.data.citation_leaderboard.map((item) => (
                <li key={item.researcher_id}>{item.researcher_id}: {item.citation_count} citations</li>
              ))}
            </ul>
          </div>
          <div className="rounded-lg border p-4" data-testid="scientometrics-hindex-leaderboard-widget">
            <h2 className="text-lg font-semibold">h-index Leaderboard</h2>
            <ul className="mt-2 space-y-1 text-sm">
              {dashboard.data.h_index_leaderboard.map((item) => (
                <li key={item.researcher_id}>{item.researcher_id}: h-index {item.h_index}</li>
              ))}
            </ul>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-lg border p-4" data-testid="scientometrics-publication-impact-summary-widget">
            <h2 className="text-lg font-semibold">Publication Impact Summary</h2>
            <ul className="mt-2 space-y-1 text-sm">
              {dashboard.data.publication_impact_summary.map((item) => (
                <li key={item.researcher_id}>{item.researcher_id}: indexed {item.indexed_publications}, international {item.international_publications}</li>
              ))}
            </ul>
          </div>
          <div className="rounded-lg border p-4" data-testid="scientometrics-trend-summary-widget">
            <h2 className="text-lg font-semibold">Scientometric Trend Summary</h2>
            <ul className="mt-2 space-y-1 text-sm">
              {dashboard.data.scientometric_trend_summary.map((item) => (
                <li key={item.period}>{item.period}: {item.trend_direction} (impact {item.impact_score})</li>
              ))}
            </ul>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-lg border p-4" data-testid="scientometric-profile-view">
            <h2 className="text-lg font-semibold">Researcher Scientometric Profile</h2>
            <p className="mt-2 text-sm">Researcher: {profile.data.researcher_id}</p>
            <p className="text-sm">Citations: {profile.data.citation_count}</p>
            <p className="text-sm">h-index: {profile.data.h_index}</p>
            <p className="text-sm">i10-index: {profile.data.i10_index}</p>
            <p className="text-sm">Impact score: {profile.data.impact_score}</p>
            <p className="text-sm">Scientometric risk: {profile.data.scientometric_risk}</p>
          </div>

          <div className="rounded-lg border p-4" data-testid="citation-analytics-view">
            <h2 className="text-lg font-semibold">Citation Analytics</h2>
            <p className="mt-2 text-sm">Publication count: {citation.data.publication_count}</p>
            <p className="text-sm">Citation count: {citation.data.citation_count}</p>
            <p className="text-sm">Top publications: {citation.data.top_publications.join(', ') || 'n/a'}</p>
            <p className="text-sm">Trend: {citation.data.trend_direction}</p>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-lg border p-4" data-testid="publication-impact-view">
            <h2 className="text-lg font-semibold">Publication Impact</h2>
            <p className="mt-2 text-sm">Publication count: {publicationImpact.data.publication_count}</p>
            <p className="text-sm">Indexed publications: {publicationImpact.data.indexed_publications}</p>
            <p className="text-sm">International publications: {publicationImpact.data.international_publications}</p>
            <p className="text-sm">Impact score: {impact.data.impact_score}</p>
          </div>

          <div className="rounded-lg border p-4" data-testid="external-identity-readiness-view">
            <h2 className="text-lg font-semibold">External Identity Readiness</h2>
            <ul className="mt-2 space-y-1 text-sm">
              {profile.data.external_identities.map((identity) => (
                <li key={identity.provider_name}>
                  {identity.provider_name}: {identity.provider_status} ({identity.provider_identifier})
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className="rounded-lg border p-4" data-testid="scientometric-trends-view">
          <h2 className="text-lg font-semibold">Scientometric Trends</h2>
          <ul className="mt-2 space-y-1 text-sm">
            {trends.data.map((trend) => (
              <li key={trend.period}>{trend.period}: citations {trend.citation_count}, h-index {trend.h_index}, direction {trend.trend_direction}</li>
            ))}
          </ul>
        </section>
      </div>
    </RequirePermission>
  );
}

export function ResearchBrainRiskPage() {
  const dashboard = useQuery({ queryKey: ['research-brain:risk-dashboard'], queryFn: researchBrainApi.getResearchRiskDashboard, staleTime: 30000 });
  const profile = useQuery({ queryKey: ['research-brain:risk-profile'], queryFn: researchBrainApi.getResearchRiskProfile, staleTime: 30000 });
  const summary = useQuery({ queryKey: ['research-brain:risk-summary'], queryFn: researchBrainApi.getResearchRiskSummary, staleTime: 30000 });
  const signals = useQuery({ queryKey: ['research-brain:risk-signals'], queryFn: researchBrainApi.getResearchRiskSignals, staleTime: 30000 });
  const trends = useQuery({ queryKey: ['research-brain:risk-trends'], queryFn: researchBrainApi.getResearchRiskTrends, staleTime: 30000 });
  const recommendations = useQuery({ queryKey: ['research-brain:risk-recommendations'], queryFn: researchBrainApi.getResearchRiskRecommendations, staleTime: 30000 });

  if (dashboard.isPending || profile.isPending || summary.isPending || signals.isPending || trends.isPending || recommendations.isPending) {
    return <LoadingState title="Loading Research Risk runtime" />;
  }

  if (dashboard.error || profile.error || summary.error || signals.error || trends.error || recommendations.error) {
    return (
      <ErrorState
        message="Failed to load Research Risk runtime."
        error={dashboard.error ?? profile.error ?? summary.error ?? signals.error ?? trends.error ?? recommendations.error}
      />
    );
  }

  if (!dashboard.data || !profile.data || !summary.data || !signals.data || !trends.data || !recommendations.data) {
    return <ErrorState message="Research Risk runtime is unavailable." />;
  }

  const riskSummary = summary.data;

  return (
    <RequirePermission permission={PERMISSIONS.RESEARCH_SCIENCE_DASHBOARD_READ}>
      <div className="space-y-6" data-testid="research-brain-risk-page">
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold">Research Risk Runtime</h1>
          <p className="text-sm text-muted-foreground">
            Brain-core-owned research risk monitoring over publication, grant, ethics, scientometric, and execution dimensions. Read-only and human-review gated.
          </p>
        </header>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Overall Risk Score" value={riskSummary.overall_risk_score} helper={`Severity ${riskSummary.severity}`} />
          <MetricCard label="Publication Risk" value={riskSummary.publication_risk} helper={riskSummary.risk_heatmap.publication} />
          <MetricCard label="Grant Risk" value={riskSummary.grant_risk} helper={riskSummary.risk_heatmap.grant} />
          <MetricCard label="Ethics Risk" value={riskSummary.ethics_risk} helper={riskSummary.risk_heatmap.ethics} />
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <div className="rounded-lg border p-4" data-testid="research-risk-overall-score-widget">
            <h2 className="text-lg font-semibold">Overall Risk Score</h2>
            <p className="mt-2 text-3xl font-semibold">{riskSummary.overall_risk_score}</p>
            <p className="text-sm text-muted-foreground">Current severity: {riskSummary.severity}</p>
          </div>
          <div className="rounded-lg border p-4" data-testid="research-risk-heatmap-widget">
            <h2 className="text-lg font-semibold">Risk Heatmap</h2>
            <ul className="mt-2 space-y-1 text-sm">
              {Object.entries(riskSummary.risk_heatmap).map(([dimension, severity]) => (
                <li key={dimension}>{dimension}: {severity}</li>
              ))}
            </ul>
          </div>
          <div className="rounded-lg border p-4" data-testid="top-critical-risks-widget">
            <h2 className="text-lg font-semibold">Top Critical Risks</h2>
            <ul className="mt-2 space-y-1 text-sm">
              {riskSummary.top_critical_risks.map((risk) => (
                <li key={risk}>{risk}</li>
              ))}
            </ul>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <div className="rounded-lg border p-4" data-testid="publication-risk-widget">
            <h2 className="text-lg font-semibold">Publication Risk</h2>
            <p className="mt-2 text-sm">Score: {riskSummary.publication_risk}</p>
          </div>
          <div className="rounded-lg border p-4" data-testid="grant-risk-widget">
            <h2 className="text-lg font-semibold">Grant Risk</h2>
            <p className="mt-2 text-sm">Score: {riskSummary.grant_risk}</p>
          </div>
          <div className="rounded-lg border p-4" data-testid="ethics-risk-widget">
            <h2 className="text-lg font-semibold">Ethics Risk</h2>
            <p className="mt-2 text-sm">Score: {riskSummary.ethics_risk}</p>
          </div>
          <div className="rounded-lg border p-4" data-testid="scientometric-risk-widget">
            <h2 className="text-lg font-semibold">Scientometric Risk</h2>
            <p className="mt-2 text-sm">Score: {riskSummary.scientometric_risk}</p>
          </div>
        </div>

        <section className="rounded-lg border p-4" data-testid="risk-profile-view">
          <h2 className="text-lg font-semibold">Risk Profile</h2>
          <p className="mt-2 text-sm">Generated at: {profile.data.generated_at ?? 'n/a'}</p>
          <p className="text-sm">Execution risk: {profile.data.summary.execution_risk}</p>
          <p className="text-sm">Provider execution enabled: {String(profile.data.provider_execution_enabled)}</p>
          <p className="text-sm">External calls enabled: {String(profile.data.external_calls_enabled)}</p>
        </section>

        <section className="rounded-lg border p-4" data-testid="risk-signal-inventory-view">
          <h2 className="text-lg font-semibold">Signal Inventory</h2>
          <ul className="mt-2 space-y-2 text-sm">
            {signals.data.map((signal) => (
              <li key={signal.family}>
                <span className="font-medium">{signal.family}</span>: {signal.severity} ({signal.dimension}) - {signal.description}
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-lg border p-4" data-testid="risk-recommendations-view">
          <h2 className="text-lg font-semibold">Risk Recommendations</h2>
          <ul className="mt-2 space-y-1 text-sm">
            {recommendations.data.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>

        <section className="rounded-lg border p-4" data-testid="risk-trend-analysis-view">
          <h2 className="text-lg font-semibold">Trend Analysis</h2>
          <ul className="mt-2 space-y-1 text-sm">
            {trends.data.map((trend) => (
              <li key={trend.dimension}>
                {trend.dimension}: {trend.previous_score} {'->'} {trend.current_score} ({trend.trend_direction})
              </li>
            ))}
          </ul>
        </section>
      </div>
    </RequirePermission>
  );
}
