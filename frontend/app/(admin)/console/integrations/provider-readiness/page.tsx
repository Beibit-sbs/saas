import Link from "next/link";
import { PERMISSIONS } from "@/shared/config/permissions";
import { RequirePermission } from "@/shared/ui/permission-gate";

const BOUNDARY_LABELS = [
  "Provider readiness only",
  "Read-only boundaries",
  "No live provider calls",
  "No credential storage",
  "No external submission",
  "Human review required",
] as const;

const WORKFLOWS = [
  "W1 Provider Registry Workflow",
  "W2 Provider Profile Workflow",
  "W3 Capability Matrix Workflow",
  "W4 Readiness Assessment Workflow",
  "W5 Evidence Collection Workflow",
  "W6 Compliance Review Workflow",
  "W7 Security Review Workflow",
  "W8 Provider Health Visibility Workflow",
  "W9 Provider Audit Review Workflow",
  "W10 Integration Planning Workflow",
  "W11 Exception and Risk Escalation Workflow",
  "W12 Provider Dashboard Publication Workflow",
] as const;

const DASHBOARDS = [
  "Provider Overview Dashboard",
  "Provider Readiness Dashboard",
  "Capability Matrix Dashboard",
  "Risk Dashboard",
  "Evidence Dashboard",
  "Integration Roadmap Dashboard",
] as const;

const PROVIDERS = [
  "SIS",
  "ERP",
  "LMS",
  "EDS",
  "eGov",
  "IDP",
  "Email Gateway",
  "SMS Gateway",
  "Payment Gateway",
  "HR Provider",
  "Regulatory Reporting Provider",
  "Biometric Device Provider (candidate)",
  "Document Exchange Provider (candidate)",
  "AI Gateway / Model Provider (candidate)",
] as const;

export default function IntegrationProviderReadinessPage() {
  return (
    <RequirePermission
      permission={PERMISSIONS.INTEGRATIONS_MANAGE}
      message="Provider readiness control plane is fail-closed until integration management permission is granted."
    >
      <main className="space-y-6" data-testid="ipr-page-shell">
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold">Integration / Provider Readiness</h1>
          <p className="text-sm text-muted-foreground">
            Governance and readiness control plane for provider registry, profiles, capability matrix, evidence, and review workflows.
          </p>
          <p className="text-xs text-muted-foreground" data-testid="ipr-subtitle">
            Non-live mode only: no provider synchronization, no credentials, no external side effects.
          </p>
        </header>

        <section className="space-y-2" data-testid="ipr-boundary-labels">
          <h2 className="text-lg font-semibold">Boundary labels</h2>
          <div className="flex flex-wrap gap-2">
            {BOUNDARY_LABELS.map((label) => (
              <span key={label} className="rounded-full border border-border px-3 py-1 text-xs text-muted-foreground">
                {label}
              </span>
            ))}
          </div>
        </section>

        <section className="space-y-2" data-testid="ipr-workflow-sections">
          <h2 className="text-lg font-semibold">Workflow sections</h2>
          <ul className="grid gap-2 sm:grid-cols-2 text-sm text-muted-foreground">
            {WORKFLOWS.map((workflow) => (
              <li key={workflow} className="rounded-md border border-border px-3 py-2">{workflow}</li>
            ))}
          </ul>
        </section>

        <section className="space-y-2" data-testid="ipr-dashboard-cards">
          <h2 className="text-lg font-semibold">Dashboard cards</h2>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {DASHBOARDS.map((dashboard) => (
              <article key={dashboard} className="rounded-md border border-border px-3 py-2">
                <h3 className="text-sm font-medium">{dashboard}</h3>
                <p className="text-xs text-muted-foreground">Read-only governance summary card.</p>
              </article>
            ))}
          </div>
        </section>

        <section className="space-y-2" data-testid="ipr-readiness-indicators">
          <h2 className="text-lg font-semibold">Readiness indicators</h2>
          <ul className="grid gap-2 sm:grid-cols-2 text-sm">
            {PROVIDERS.map((provider) => (
              <li key={provider} className="rounded-md border border-border px-3 py-2">
                <p className="font-medium">{provider}</p>
                <p className="text-xs text-muted-foreground">Status: NON_LIVE_READINESS</p>
              </li>
            ))}
          </ul>
        </section>

        <section className="space-y-2" data-testid="ipr-navigation-visibility">
          <h2 className="text-lg font-semibold">Navigation visibility</h2>
          <div className="grid gap-2 sm:grid-cols-3">
            <Link href="/console/integrations" className="rounded-md border border-border px-3 py-2 text-sm hover:bg-muted/40">
              Integrations Root
            </Link>
            <Link href="/console/finance-procurement-asset/provider-readiness" className="rounded-md border border-border px-3 py-2 text-sm hover:bg-muted/40">
              Finance Provider Readiness
            </Link>
            <Link href="/console/hr-staff-governance/provider-readiness" className="rounded-md border border-border px-3 py-2 text-sm hover:bg-muted/40">
              HR Provider Readiness
            </Link>
          </div>
        </section>

        <section className="rounded-md border border-dashed border-border p-4 text-sm text-muted-foreground" data-testid="ipr-empty-state">
          Empty state: no live provider telemetry, no connector health feed, and no activation actions are available in this vertical shell.
        </section>
      </main>
    </RequirePermission>
  );
}