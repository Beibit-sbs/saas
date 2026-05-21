'use client';

import { RequirePermission } from '@/shared/ui/permission-gate';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';
import {
  ControlTowerShell,
  DataSourceGuardPanel,
  DepartmentPerformancePanel,
} from '@/modules/executive-control-tower/components';
import { useDepartmentPerformanceSummary } from '@/modules/executive-control-tower/hooks';
import { EXECUTIVE_CONTROL_TOWER_PERMISSIONS } from '@/modules/executive-control-tower/permissions';

export default function ExecutiveControlTowerDepartmentsPage() {
  const { data, error, isPending, isUntrusted } = useDepartmentPerformanceSummary();

  if (isPending) return <LoadingState title="Loading department visibility metrics" />;
  if (isUntrusted && error instanceof Error) return <DataSourceGuardPanel reason={error.message} />;
  if (error) return <ErrorState error={error} message="Failed to load department visibility metrics." />;
  if (!data) return <ErrorState message="Department visibility metrics are unavailable." />;

  return (
    <RequirePermission permission={EXECUTIVE_CONTROL_TOWER_PERMISSIONS.DEPARTMENT_READ}>
      <ControlTowerShell
        title="Department Performance"
        description="Operational visibility only with no employee ranking or punitive score."
        activePath="/console/executive-control-tower/departments"
      >
        <DepartmentPerformancePanel summary={data} />
      </ControlTowerShell>
    </RequirePermission>
  );
}