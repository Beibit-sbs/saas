'use client';

import { RequirePermission } from '@/shared/ui/permission-gate';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';
import {
  ControlTowerShell,
  DataSourceGuardPanel,
  SlaRiskBottleneckPanel,
} from '@/modules/executive-control-tower/components';
import { useSlaRiskBottleneckSummary } from '@/modules/executive-control-tower/hooks';
import { EXECUTIVE_CONTROL_TOWER_PERMISSIONS } from '@/modules/executive-control-tower/permissions';

export default function ExecutiveControlTowerSlaRiskPage() {
  const { data, error, isPending, isUntrusted } = useSlaRiskBottleneckSummary();

  if (isPending) return <LoadingState title="Loading SLA and risk metrics" />;
  if (isUntrusted && error instanceof Error) return <DataSourceGuardPanel reason={error.message} />;
  if (error) return <ErrorState error={error} message="Failed to load SLA and risk metrics." />;
  if (!data) return <ErrorState message="SLA and risk metrics are unavailable." />;

  return (
    <RequirePermission permission={EXECUTIVE_CONTROL_TOWER_PERMISSIONS.SLA_RISK_READ}>
      <ControlTowerShell
        title="SLA / Risk / Bottleneck"
        description="Operational SLA and bottleneck visibility with no auto-escalation action."
        activePath="/console/executive-control-tower/sla-risk"
      >
        <SlaRiskBottleneckPanel summary={data} />
      </ControlTowerShell>
    </RequirePermission>
  );
}