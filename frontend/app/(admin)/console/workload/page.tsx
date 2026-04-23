'use client';

import React, { useState } from 'react';
import { PERMISSIONS } from '@/shared/config/permissions';
import { RequirePermission } from '@/shared/auth/permission-gate';
import { PageHeader } from '@/shared/ui/page-header';
import { LoadingState } from '@/shared/ui/page-states';
import { ErrorState } from '@/shared/ui/page-states';
import { Badge } from '@/shared/ui/badge';
import {
  useFacultyWorkload,
  useWorkloadAlerts,
  useDepartmentWorkload,
  useWorkloadMetrics,
  useUpdateFacultyCapacity,
} from '@/modules/faculty-workload/hooks';

export default function FacultyWorkloadPage() {
  const [selectedTermId, setSelectedTermId] = useState<string>('current');
  const [selectedDepartment, setSelectedDepartment] = useState<string>('');

  const { data: metrics, isLoading: metricsLoading } = useWorkloadMetrics(selectedTermId);
  const { data: alerts, isLoading: alertsLoading } = useWorkloadAlerts(selectedTermId);
  const { data: deptSummary } = useDepartmentWorkload(selectedDepartment, selectedTermId);
  const updateCapacity = useUpdateFacultyCapacity();

  const isLoading = metricsLoading || alertsLoading;
  const isError = false;

  if (isLoading) {
    return (
      <RequirePermission permission={PERMISSIONS.FACULTY_READ}>
        <LoadingState message="Loading workload data..." />
      </RequirePermission>
    );
  }

  if (isError || !metrics) {
    return (
      <RequirePermission permission={PERMISSIONS.FACULTY_READ}>
        <ErrorState message="Failed to load workload data" />
      </RequirePermission>
    );
  }

  return (
    <RequirePermission permission={PERMISSIONS.FACULTY_READ}>
      <div className="container mx-auto py-8 space-y-8">
        <PageHeader
          title="Faculty Workload Planning"
          description="Manage faculty workload distribution, capacity, and alerts"
        />

        {/* Term & Department Selector */}
        <div className="card p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Academic Term</label>
              <select
                value={selectedTermId}
                onChange={(e) => setSelectedTermId(e.target.value)}
                className="w-full px-3 py-2 border rounded"
              >
                <option value="current">Current Term</option>
                <option value="next">Next Term</option>
                <option value="previous">Previous Term</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Department (Optional)</label>
              <select
                value={selectedDepartment}
                onChange={(e) => setSelectedDepartment(e.target.value)}
                className="w-full px-3 py-2 border rounded"
              >
                <option value="">All Departments</option>
                {metrics?.departments.map((dept) => (
                  <option key={dept.department} value={dept.department}>
                    {dept.department}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Summary Cards */}
        <div
          className="grid grid-cols-4 gap-4"
          data-testid="workload-summary-section"
        >
          <div className="card p-6">
            <div className="text-sm text-gray-600 mb-2">Total Faculty</div>
            <div className="text-3xl font-bold" data-testid="total-faculty">
              {metrics?.total_faculty}
            </div>
          </div>

          <div className="card p-6">
            <div className="text-sm text-gray-600 mb-2">Avg Utilization</div>
            <div className="text-3xl font-bold" data-testid="avg-utilization">
              {metrics?.average_utilization_pct.toFixed(1)}%
            </div>
          </div>

          <div className="card p-6">
            <div className="text-sm text-gray-600 mb-2">Underload Alerts</div>
            <div className="text-3xl font-bold text-yellow-600" data-testid="underload-count">
              {metrics?.alert_count_by_type.underload}
            </div>
          </div>

          <div className="card p-6">
            <div className="text-sm text-gray-600 mb-2">Overload Alerts</div>
            <div className="text-3xl font-bold text-red-600" data-testid="overload-count">
              {metrics?.alert_count_by_type.overload}
            </div>
          </div>
        </div>

        {/* Alerts Section */}
        {alerts && alerts.length > 0 && (
          <div className="card p-6" data-testid="alerts-section">
            <h3 className="text-lg font-bold mb-4">Workload Alerts</h3>
            <div className="space-y-3">
              {alerts.map((alert) => (
                <div
                  key={`${alert.faculty_id}-${alert.alert_type}`}
                  className="flex items-center justify-between p-3 border rounded bg-gray-50"
                >
                  <div>
                    <div className="font-medium">{alert.faculty_name}</div>
                    <div className="text-sm text-gray-600">
                      {alert.department} • {alert.total_credit_hours} credit hours
                    </div>
                  </div>
                  <Badge
                    variant={
                      alert.severity === 'high'
                        ? 'destructive'
                        : alert.severity === 'medium'
                          ? 'warning'
                          : 'default'
                    }
                  >
                    {alert.alert_type.replace(/_/g, ' ')}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Department Summary */}
        {deptSummary && (
          <div className="card p-6" data-testid="department-summary-section">
            <h3 className="text-lg font-bold mb-4">Department: {deptSummary.department}</h3>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <div className="text-sm text-gray-600">Avg Utilization</div>
                <div className="text-2xl font-bold">{deptSummary.average_utilization_pct.toFixed(1)}%</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Fairness Score</div>
                <div className="text-2xl font-bold">{deptSummary.fairness_score.toFixed(2)}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Active Alerts</div>
                <div className="text-2xl font-bold">
                  {deptSummary.underload_count +
                    deptSummary.overload_count +
                    deptSummary.max_credit_exceeded_count}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Utilization Distribution */}
        <div className="card p-6" data-testid="utilization-distribution">
          <h3 className="text-lg font-bold mb-4">Utilization Distribution</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span>Minimum:</span>
              <span className="font-mono">{metrics?.min_utilization_pct.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span>Median:</span>
              <span className="font-mono">{metrics?.median_utilization_pct.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span>Maximum:</span>
              <span className="font-mono">{metrics?.max_utilization_pct.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span>Std Deviation:</span>
              <span className="font-mono">{metrics?.utilization_std_dev.toFixed(2)}</span>
            </div>
          </div>
        </div>
      </div>
    </RequirePermission>
  );
}
