import Link from "next/link";
import { PERMISSIONS } from "@/shared/config/permissions";
import { RequirePermission } from "@/shared/ui/permission-gate";

const PROVIDER_READINESS_BOUNDARY_LABELS = [
  "Provider readiness only",
  "Read-only boundaries",
  "No live provider calls",
  "No credentials storage",
  "No external submission",
  "Human review required",
] as const;

const PROVIDER_READINESS_WORKFLOWS = [
  "W1 Provider registry workflow",
  "W2 Provider profile workflow",
  "W3 Capability matrix workflow",
  "W4 Readiness assessment workflow",
  "W5 Evidence collection workflow",
  "W6 Compliance review workflow",
  "W7 Security review workflow",
  "W8 Provider health visibility workflow",
  "W9 Provider audit review workflow",
  "W10 Integration planning workflow",
  "W11 Exception and risk escalation workflow",
  "W12 Dashboard publication workflow",
] as const;

const PROVIDER_READINESS_DASHBOARDS = [
  "Provider Overview Dashboard",
  "Provider Readiness Dashboard",
  "Capability Matrix Dashboard",
  "Risk Dashboard",
  "Evidence Dashboard",
  "Integration Roadmap Dashboard",
] as const;

const PROVIDER_READINESS_ROUTES = [
  { href: "/console/integrations/provider-readiness", title: "Provider Readiness Control Plane" },
  { href: "/console/finance-procurement-asset/provider-readiness", title: "Finance Provider Readiness" },
  { href: "/console/hr-staff-governance/provider-readiness", title: "HR Provider Readiness" },
] as const;

export default function ConsoleIntegrationsRootPage() {
  return (
    <RequirePermission
      permission={PERMISSIONS.INTEGRATIONS_MANAGE}
      message="Integration surfaces are fail-closed until integration management permission is granted."
    >
      <main className="space-y-6" data-testid="integrations-root-page">
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold">Integrations</h1>
          <p className="text-sm text-muted-foreground">
            Identity integrations and provider-readiness governance shell for non-live integration delivery.
          </p>
          <p className="text-xs text-muted-foreground" data-testid="integrations-subtitle">
            Runtime mode: metadata/readiness/evidence only. No live provider connectivity claims.
          </p>
        </header>

        <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <Link
            href="/console/federation"
            className="rounded-lg border border-border p-4 hover:bg-muted/40"
          >
            <h2 className="font-medium">Identity Federation</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Configure SSO providers and federation settings.
            </p>
          </Link>
          <Link
            href="/console/ldap"
            className="rounded-lg border border-border p-4 hover:bg-muted/40"
          >
            <h2 className="font-medium">LDAP</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Configure directory sync and LDAP connectivity.
            </p>
          </Link>
          <Link
            href="/console/integrations/provider-readiness"
            className="rounded-lg border border-border p-4 hover:bg-muted/40"
            data-testid="integrations-provider-readiness-card"
          >
            <h2 className="font-medium">Provider Readiness Control Plane</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Registry, capability matrix, evidence, dashboards, and boundary governance for non-live providers.
            </p>
          </Link>
        </section>

        <section className="space-y-2" data-testid="integrations-boundary-labels">
          <h2 className="text-lg font-semibold">Boundary labels</h2>
          <div className="flex flex-wrap gap-2">
            {PROVIDER_READINESS_BOUNDARY_LABELS.map((label) => (
              <span key={label} className="rounded-full border border-border px-3 py-1 text-xs text-muted-foreground">
                {label}
              </span>
            ))}
          </div>
        </section>

        <section className="space-y-2" data-testid="integrations-workflow-sections">
          <h2 className="text-lg font-semibold">Workflow coverage</h2>
          <ul className="grid gap-2 sm:grid-cols-2 text-sm text-muted-foreground">
            {PROVIDER_READINESS_WORKFLOWS.map((workflow) => (
              <li key={workflow} className="rounded-md border border-border px-3 py-2">{workflow}</li>
            ))}
          </ul>
        </section>

        <section className="space-y-2" data-testid="integrations-dashboard-cards">
          <h2 className="text-lg font-semibold">Dashboard cards</h2>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {PROVIDER_READINESS_DASHBOARDS.map((dashboard) => (
              <article key={dashboard} className="rounded-md border border-border px-3 py-2">
                <h3 className="text-sm font-medium">{dashboard}</h3>
                <p className="text-xs text-muted-foreground">Read-only governance visibility.</p>
              </article>
            ))}
          </div>
        </section>

        <section className="space-y-2" data-testid="integrations-navigation-visibility">
          <h2 className="text-lg font-semibold">Navigation visibility</h2>
          <div className="grid gap-2 sm:grid-cols-3">
            {PROVIDER_READINESS_ROUTES.map((route) => (
              <Link key={route.href} href={route.href} className="rounded-md border border-border px-3 py-2 text-sm hover:bg-muted/40">
                {route.title}
              </Link>
            ))}
          </div>
        </section>

        <section className="rounded-md border border-dashed border-border p-4 text-sm text-muted-foreground" data-testid="integrations-empty-state">
          No live provider health telemetry is available in this shell. Evidence, compliance, and readiness remain human-reviewed.
        </section>
      </main>
    </RequirePermission>
  );
}
