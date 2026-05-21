'use client';

import { RequirePermission } from '@/shared/ui/permission-gate';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';
import {
  ControlTowerShell,
  DataSourceGuardPanel,
  ExecutiveOverviewPanel,
} from '@/modules/executive-control-tower/components';
import { useExecutiveControlTowerSummary } from '@/modules/executive-control-tower/hooks';
import { EXECUTIVE_CONTROL_TOWER_PERMISSIONS } from '@/modules/executive-control-tower/permissions';

export default function ExecutiveControlTowerPage() {
  const { data, error, isPending, isUntrusted } = useExecutiveControlTowerSummary();

  if (isPending) {
    return <LoadingState title="Loading Executive Control Tower" />;
  }

  if (isUntrusted && error instanceof Error) {
    return <DataSourceGuardPanel reason={error.message} />;
  }

  if (error) {
    return <ErrorState error={error} message="Failed to load Executive Control Tower overview." />;
  }

  if (!data) {
    return <ErrorState message="Executive Control Tower overview is unavailable." />;
  }

  return (
    <RequirePermission permission={EXECUTIVE_CONTROL_TOWER_PERMISSIONS.SUMMARY_READ}>
      <ControlTowerShell
        title="Executive Control Tower"
        description="Read-only executive visibility over governance workflows and evidence-linked metrics."
        activePath="/console/executive-control-tower"
      >
        <ExecutiveOverviewPanel summary={data} />
      </ControlTowerShell>
    </RequirePermission>
  );
}