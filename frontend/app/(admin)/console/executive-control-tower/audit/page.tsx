'use client';

import { RequirePermission } from '@/shared/ui/permission-gate';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';
import {
  AuditCompliancePanel,
  ControlTowerShell,
  DataSourceGuardPanel,
} from '@/modules/executive-control-tower/components';
import { useAuditComplianceSummary } from '@/modules/executive-control-tower/hooks';
import { EXECUTIVE_CONTROL_TOWER_PERMISSIONS } from '@/modules/executive-control-tower/permissions';

export default function ExecutiveControlTowerAuditPage() {
  const { data, error, isPending, isUntrusted } = useAuditComplianceSummary();

  if (isPending) return <LoadingState title="Loading audit and compliance metrics" />;
  if (isUntrusted && error instanceof Error) return <DataSourceGuardPanel reason={error.message} />;
  if (error) return <ErrorState error={error} message="Failed to load audit and compliance metrics." />;
  if (!data) return <ErrorState message="Audit and compliance metrics are unavailable." />;

  return (
    <RequirePermission permission={EXECUTIVE_CONTROL_TOWER_PERMISSIONS.AUDIT_READ}>
      <ControlTowerShell
        title="Audit / Compliance"
        description="Read-only audit visibility with limitations shown explicitly."
        activePath="/console/executive-control-tower/audit"
      >
        <AuditCompliancePanel summary={data} />
      </ControlTowerShell>
    </RequirePermission>
  );
}