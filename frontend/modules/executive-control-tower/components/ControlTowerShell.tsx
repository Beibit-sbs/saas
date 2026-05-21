'use client';

import Link from 'next/link';
import { LayoutDashboard } from 'lucide-react';
import { EXECUTIVE_CONTROL_TOWER_SECTION_PERMISSIONS } from '../permissions';
import { PermissionGate } from '@/shared/ui/permission-gate';
import { PageHeader } from '@/shared/ui/page-header';

const NAV_ITEMS = [
  {
    href: '/console/executive-control-tower',
    label: 'Overview',
    permission: EXECUTIVE_CONTROL_TOWER_SECTION_PERMISSIONS.overview,
  },
  {
    href: '/console/executive-control-tower/assignments',
    label: 'Assignments',
    permission: EXECUTIVE_CONTROL_TOWER_SECTION_PERMISSIONS.assignments,
  },
  {
    href: '/console/executive-control-tower/documents',
    label: 'Documents',
    permission: EXECUTIVE_CONTROL_TOWER_SECTION_PERMISSIONS.documents,
  },
  {
    href: '/console/executive-control-tower/sla-risk',
    label: 'SLA / Risk',
    permission: EXECUTIVE_CONTROL_TOWER_SECTION_PERMISSIONS.slaRisk,
  },
  {
    href: '/console/executive-control-tower/strategy',
    label: 'Strategy',
    permission: EXECUTIVE_CONTROL_TOWER_SECTION_PERMISSIONS.strategy,
  },
  {
    href: '/console/executive-control-tower/audit',
    label: 'Audit',
    permission: EXECUTIVE_CONTROL_TOWER_SECTION_PERMISSIONS.audit,
  },
  {
    href: '/console/executive-control-tower/departments',
    label: 'Departments',
    permission: EXECUTIVE_CONTROL_TOWER_SECTION_PERMISSIONS.departments,
  },
  {
    href: '/console/executive-control-tower/metric-registry',
    label: 'Metric registry',
    permission: EXECUTIVE_CONTROL_TOWER_SECTION_PERMISSIONS.metricRegistry,
  },
] as const;

function tabClassName(active: boolean) {
  return active
    ? 'rounded-md border border-primary bg-primary/10 px-3 py-2 text-sm font-medium text-primary'
    : 'rounded-md border border-transparent px-3 py-2 text-sm text-muted-foreground hover:border-border hover:text-foreground';
}

export function ControlTowerHeader({ title, description }: { title: string; description?: string }) {
  return <PageHeader title={title} description={description} icon={LayoutDashboard} />;
}

export function ControlTowerNavTabs({ activePath }: { activePath: string }) {
  return (
    <nav className="flex flex-wrap gap-2 rounded-lg border bg-background p-2" data-testid="control-tower-nav-tabs">
      {NAV_ITEMS.map((item) => (
        <PermissionGate key={item.href} permission={item.permission} fallback={null}>
          <Link className={tabClassName(activePath === item.href)} href={item.href}>
            {item.label}
          </Link>
        </PermissionGate>
      ))}
    </nav>
  );
}

export function ControlTowerShell({
  title,
  description,
  activePath,
  children,
}: {
  title: string;
  description?: string;
  activePath: string;
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-8">
        <ControlTowerHeader title={title} description={description} />
        <ControlTowerNavTabs activePath={activePath} />
        <div className="grid gap-3 md:grid-cols-3">
          <div
            className="rounded-lg border bg-background px-4 py-3 text-sm text-muted-foreground"
            data-testid="computed-from-governance-workflows-label"
          >
            Computed from governance workflows
          </div>
          <div
            className="rounded-lg border bg-background px-4 py-3 text-sm text-muted-foreground"
            data-testid="evidence-linked-metric-label"
          >
            Evidence-linked metric
          </div>
          <div
            className="rounded-lg border bg-background px-4 py-3 text-sm text-muted-foreground"
            data-testid="no-automated-decision-label"
          >
            No automated decision is made by this dashboard
          </div>
        </div>
        {children}
      </div>
    </div>
  );
}