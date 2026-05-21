'use client';

import { RequirePermission } from '@/shared/ui/permission-gate';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';
import {
  ControlTowerShell,
  DataSourceGuardPanel,
  StrategyKpiPanel,
} from '@/modules/executive-control-tower/components';
import { useStrategyKpiSummary } from '@/modules/executive-control-tower/hooks';
import { EXECUTIVE_CONTROL_TOWER_PERMISSIONS } from '@/modules/executive-control-tower/permissions';

export default function ExecutiveControlTowerStrategyPage() {
  const { data, error, isPending, isUntrusted } = useStrategyKpiSummary();

  if (isPending) return <LoadingState title="Loading strategy KPI metrics" />;
  if (isUntrusted && error instanceof Error) return <DataSourceGuardPanel reason={error.message} />;
  if (error) return <ErrorState error={error} message="Failed to load strategy KPI metrics." />;
  if (!data) return <ErrorState message="Strategy KPI metrics are unavailable." />;

  return (
    <RequirePermission permission={EXECUTIVE_CONTROL_TOWER_PERMISSIONS.STRATEGY_READ}>
      <ControlTowerShell
        title="Strategy KPI"
        description="Future-contract metrics only. No fake progress and no invented initiatives."
        activePath="/console/executive-control-tower/strategy"
      >
        <StrategyKpiPanel summary={data} />
      </ControlTowerShell>
    </RequirePermission>
  );
}