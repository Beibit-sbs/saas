'use client';

import React, { useState } from 'react';
import { PERMISSIONS } from '@/shared/config/permissions';
import { RequirePermission } from '@/shared/auth/permission-gate';
import { PageHeader } from '@/shared/ui/page-header';
import { LoadingState } from '@/shared/ui/page-states';
import { ErrorState } from '@/shared/ui/page-states';
import { Badge } from '@/shared/ui/badge';
import {
  useDepartmentQualityDashboard,
  useQualityMetricsReport,
  useQualityBenchmarks,
  useRecordQualityMetric,
} from '@/modules/teaching-quality/hooks';

export default function TeachingQualityPage() {
  const [selectedTermId, setSelectedTermId] = useState<string>('current');
  const [selectedDepartment, setSelectedDepartment] = useState<string>('');

  const { data: report, isLoading: reportLoading } = useQualityMetricsReport(selectedTermId);
  const { data: benchmarks } = useQualityBenchmarks(selectedTermId);
  const { data: deptDashboard } = useDepartmentQualityDashboard(selectedDepartment, selectedTermId);
  const recordMetric = useRecordQualityMetric();

  const isLoading = reportLoading;
  const isError = false;

  if (isLoading) {
    return (
      <RequirePermission permission={PERMISSIONS.FACULTY_READ}>
        <LoadingState message="Loading quality metrics..." />
      </RequirePermission>
    );
  }

  if (isError || !report) {
    return (
      <RequirePermission permission={PERMISSIONS.FACULTY_READ}>
        <ErrorState message="Failed to load quality metrics" />
      </RequirePermission>
    );
  }

  return (
    <RequirePermission permission={PERMISSIONS.FACULTY_READ}>
      <div className="container mx-auto py-8 space-y-8">
        <PageHeader
          title="Teaching Quality Analytics"
          description="Monitor faculty performance, benchmarks, and improvement initiatives"
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
                {report?.departments.map((dept) => (
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
          className="grid grid-cols-3 gap-4"
          data-testid="quality-summary-section"
        >
          <div className="card p-6">
            <div className="text-sm text-gray-600 mb-2">Total Faculty Evaluated</div>
            <div className="text-3xl font-bold" data-testid="total-faculty-evaluated">
              {report?.total_faculty_evaluated}
            </div>
          </div>

          <div className="card p-6">
            <div className="text-sm text-gray-600 mb-2">Average Quality Score</div>
            <div className="text-3xl font-bold" data-testid="average-quality-score">
              {report?.average_quality_score.toFixed(2)}/5.0
            </div>
          </div>

          <div className="card p-6">
            <div className="text-sm text-gray-600 mb-2">Above Target</div>
            <div className="text-3xl font-bold text-green-600" data-testid="above-target-count">
              {deptDashboard?.above_target_count || 0}
            </div>
          </div>
        </div>

        {/* Benchmarks Section */}
        {benchmarks && benchmarks.length > 0 && (
          <div className="card p-6" data-testid="benchmarks-section">
            <h3 className="text-lg font-bold mb-4">Quality Benchmarks</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Metric</th>
                    <th className="text-right py-2">Institutional Avg</th>
                    <th className="text-right py-2">Departmental Avg</th>
                    <th className="text-right py-2">Target</th>
                  </tr>
                </thead>
                <tbody>
                  {benchmarks.map((bench) => (
                    <tr key={bench.metric_name} className="border-b hover:bg-gray-50">
                      <td className="py-2">{bench.metric_name}</td>
                      <td className="text-right">{bench.institutional_average.toFixed(2)}</td>
                      <td className="text-right">{bench.departmental_average.toFixed(2)}</td>
                      <td className="text-right font-medium">{bench.target_value.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Department Dashboard */}
        {deptDashboard && (
          <div className="card p-6" data-testid="department-dashboard-section">
            <h3 className="text-lg font-bold mb-4">Department: {deptDashboard.department}</h3>
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div>
                <div className="text-sm text-gray-600">Faculty Count</div>
                <div className="text-2xl font-bold">{deptDashboard.total_faculty}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Average Quality</div>
                <div className="text-2xl font-bold">{deptDashboard.average_quality_score.toFixed(2)}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Below Target</div>
                <div className="text-2xl font-bold text-red-600">{deptDashboard.below_target_count}</div>
              </div>
            </div>

            {deptDashboard.improvement_opportunities.length > 0 && (
              <div>
                <h4 className="font-medium mb-3">Improvement Opportunities</h4>
                <ul className="space-y-2">
                  {deptDashboard.improvement_opportunities.map((opportunity, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm">
                      <span className="text-yellow-600 mt-0.5">•</span>
                      <span>{opportunity}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Trending Metrics */}
        {report?.trending_metrics && report.trending_metrics.length > 0 && (
          <div className="card p-6" data-testid="trending-section">
            <h3 className="text-lg font-bold mb-4">Metric Trends</h3>
            <div className="space-y-3">
              {report.trending_metrics.map((metric) => (
                <div
                  key={metric.metric_name}
                  className="flex items-center justify-between p-3 border rounded"
                >
                  <div>
                    <div className="font-medium">{metric.metric_name}</div>
                    <div className="text-sm text-gray-600">Change: {metric.change_pct.toFixed(1)}%</div>
                  </div>
                  <Badge
                    variant={
                      metric.trend === 'up'
                        ? 'default'
                        : metric.trend === 'down'
                          ? 'destructive'
                          : 'secondary'
                    }
                  >
                    {metric.trend === 'up' ? '↑' : metric.trend === 'down' ? '↓' : '→'} {metric.trend}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </RequirePermission>
  );
}
