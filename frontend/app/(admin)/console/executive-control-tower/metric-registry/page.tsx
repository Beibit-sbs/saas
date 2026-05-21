'use client';

import { PermissionGate, RequirePermission } from '@/shared/ui/permission-gate';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';
import {
  ControlTowerHealthPanel,
  ControlTowerShell,
  DataSourceGuardPanel,
  MetricRegistryTable,
} from '@/modules/executive-control-tower/components';
import { useExecutiveControlTowerHealth, useMetricRegistry } from '@/modules/executive-control-tower/hooks';
import { EXECUTIVE_CONTROL_TOWER_PERMISSIONS } from '@/modules/executive-control-tower/permissions';

export default function ExecutiveControlTowerMetricRegistryPage() {
  const registry = useMetricRegistry();
  const health = useExecutiveControlTowerHealth();

  if (registry.isPending) return <LoadingState title="Loading metric registry" />;
  if (registry.isUntrusted && registry.error instanceof Error) {
    return <DataSourceGuardPanel reason={registry.error.message} />;
  }
  if (registry.error) return <ErrorState error={registry.error} message="Failed to load metric registry." />;
  if (!registry.data) return <ErrorState message="Metric registry is unavailable." />;

  return (
    <RequirePermission permission={EXECUTIVE_CONTROL_TOWER_PERMISSIONS.METRIC_REGISTRY_READ}>
      <ControlTowerShell
        title="Metric Registry"
        description="Formulas, permissions, evidence contracts, runtime status, and readiness for all backend metrics."
        activePath="/console/executive-control-tower/metric-registry"
      >
        <div className="space-y-6">
          <MetricRegistryTable registry={registry.data} />
          <PermissionGate permission={EXECUTIVE_CONTROL_TOWER_PERMISSIONS.READ} fallback={null}>
            {health.data ? <ControlTowerHealthPanel health={health.data} /> : null}
          </PermissionGate>
        </div>
      </ControlTowerShell>
    </RequirePermission>
  );
}