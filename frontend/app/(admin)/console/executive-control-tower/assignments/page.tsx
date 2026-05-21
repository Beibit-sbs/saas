'use client';

import { RequirePermission } from '@/shared/ui/permission-gate';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';
import {
  AssignmentExecutionPanel,
  ControlTowerShell,
  DataSourceGuardPanel,
} from '@/modules/executive-control-tower/components';
import { useAssignmentExecutionSummary } from '@/modules/executive-control-tower/hooks';
import { EXECUTIVE_CONTROL_TOWER_PERMISSIONS } from '@/modules/executive-control-tower/permissions';

export default function ExecutiveControlTowerAssignmentsPage() {
  const { data, error, isPending, isUntrusted } = useAssignmentExecutionSummary();

  if (isPending) return <LoadingState title="Loading assignment execution metrics" />;
  if (isUntrusted && error instanceof Error) return <DataSourceGuardPanel reason={error.message} />;
  if (error) return <ErrorState error={error} message="Failed to load assignment execution metrics." />;
  if (!data) return <ErrorState message="Assignment execution metrics are unavailable." />;

  return (
    <RequirePermission permission={EXECUTIVE_CONTROL_TOWER_PERMISSIONS.ASSIGNMENTS_READ}>
      <ControlTowerShell
        title="Assignment Execution"
        description="Operational visibility only with no ranking or punitive behavior."
        activePath="/console/executive-control-tower/assignments"
      >
        <AssignmentExecutionPanel summary={data} />
      </ControlTowerShell>
    </RequirePermission>
  );
}