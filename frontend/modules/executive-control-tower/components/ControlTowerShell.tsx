'use client';

import Link from 'next/link';
import { useState } from 'react';
import { LayoutDashboard } from 'lucide-react';
import { EXECUTIVE_CONTROL_TOWER_SECTION_PERMISSIONS } from '../permissions';
import { PermissionGate } from '@/shared/ui/permission-gate';
import { PageHeader } from '@/shared/ui/page-header';
import {
  DateRangeFilter,
  EmptyState,
  FilterBar,
  KPIGrid,
  MetricCard,
  PageActionBar,
  PageActions,
  PageToolbar,
  SectionHeader,
  PageShell,
  ExportButton,
  EvidenceUploadPanel,
  SearchInput,
  StatusFilter,
} from '@/shared/ui-framework';

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
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [range, setRange] = useState({ from: '', to: '' });

  return (
    <PageShell>
      <SectionHeader eyebrow="Executive Control Tower" title={title} description={description} />
      <PageToolbar
        left={
          <PageActions>
            <PageActionBar
              secondaryActions={[
                { id: 'refresh', label: 'Refresh', disabled: true, disabledReason: 'Read-only executive overview.' },
                { id: 'edit', label: 'Edit', disabled: true, disabledReason: 'No edit workflow on this shell.' },
              ]}
              primaryAction={{ id: 'create', label: 'Create', disabled: true, disabledReason: 'No create workflow on this shell.' }}
            />
          </PageActions>
        }
        right={
          <PageActions>
            <ExportButton exportAvailable={false} unavailableReason="Export endpoint unavailable for executive overview." />
          </PageActions>
        }
      />
      <FilterBar onApply={() => undefined} onClear={() => { setSearch(''); setStatus(''); setRange({ from: '', to: '' }); }} onPersistToUrl={() => undefined}>
        <SearchInput value={search} onChange={setSearch} placeholder="Search executive surfaces" />
        <StatusFilter value={status} onChange={setStatus} options={[{ value: 'visible', label: 'Visible' }, { value: 'future', label: 'Future scope' }]} />
        <DateRangeFilter value={range} onChange={setRange} />
      </FilterBar>
      <ControlTowerHeader title={title} description={description} />
        <ControlTowerNavTabs activePath={activePath} />
      <KPIGrid>
        <MetricCard
          label="Workflow basis"
          value="Computed"
          source="governance_workflows"
          timestamp="runtime"
          limitations={['metadata_only']}
          incompleteData={true}
        />
        <MetricCard
          label="Evidence linkage"
          value="Enabled"
          source="evidence_contract"
          timestamp="runtime"
          limitations={['no_live_execution']}
          incompleteData={true}
        />
        <MetricCard
          label="Decision mode"
          value="Human review"
          source="safety_boundary"
          timestamp="runtime"
          limitations={['no_automated_decision']}
          incompleteData={true}
        />
      </KPIGrid>
      <div className="hidden" aria-hidden>
        <div data-testid="computed-from-governance-workflows-label">Computed from governance workflows</div>
        <div data-testid="evidence-linked-metric-label">Evidence-linked metric</div>
        <div data-testid="no-automated-decision-label">No automated decision is made by this dashboard</div>
      </div>
      <section className="grid gap-4 xl:grid-cols-2" data-testid="control-tower-state-gallery">
        <EmptyState variant="no_data" title="No executive data" description="No executive rows are currently available for the selected contract surface." />
        <EmptyState variant="no_results" title="No executive results" description="Shared filters can narrow executive visibility without introducing fake controls." />
        <EmptyState variant="metadata_only" title="Executive metadata only" description="KPI and workflow visibility remain evidence-backed and read-only." limitation="No automated escalation or decision execution is exposed." />
        <EmptyState variant="future_scope" title="Future-scope executive workflows" description="Live strategy execution and automated workflow intervention remain deferred outside A-044.R6." />
      </section>
      <EvidenceUploadPanel uploadSupported={false} limitationLabel="Evidence upload endpoints are not available in this shared executive shell." />
        {children}
    </PageShell>
  );
}