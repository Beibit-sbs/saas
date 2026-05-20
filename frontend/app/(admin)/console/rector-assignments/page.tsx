'use client';

/**
 * Rector Assignment Registry + Dashboard
 *
 * Dashboard KPIs are only rendered when backend confirms:
 *   fake_metrics === false  AND  data_source === "computed_from_assignments"
 *
 * If either guard fails → DataQualityError state is shown.
 * No hardcoded dashboard values. No mock fallbacks.
 */

import React, { useState } from 'react';
import Link from 'next/link';
import {
  useRectorAssignmentDashboard,
  useRectorAssignmentList,
} from '@/modules/rector-assignments/hooks';
import {
  STATUS_LABELS,
  STATUS_BADGE_VARIANTS,
} from '@/modules/rector-assignments/status';
import { AssignmentStatus, AssignmentPriority } from '@/modules/rector-assignments/types';
import { PERMISSIONS } from '@/shared/config/permissions';
import { PermissionGate, RequirePermission } from '@/shared/auth/permission-gate';
import { PageHeader } from '@/shared/ui/page-header';
import { LoadingState, ErrorState } from '@/shared/ui/page-states';
import { Badge } from '@/shared/ui/badge';
import { ShieldAlert } from 'lucide-react';

// ---------------------------------------------------------------------------
// DataQualityError — shown when fake_metrics guard or data_source guard fails
// ---------------------------------------------------------------------------

function DataQualityError({ reason }: { reason: string }) {
  return (
    <div
      className="flex flex-col items-center justify-center gap-3 rounded-lg border border-red-200 bg-red-50 px-6 py-10 text-center"
      data-testid="data-quality-error"
      role="alert"
      aria-live="assertive"
    >
      <ShieldAlert className="h-8 w-8 text-red-400" />
      <p className="font-medium text-red-700">Dashboard data could not be verified.</p>
      <p className="text-sm text-red-600">{reason}</p>
      <p className="text-xs text-red-500">Please contact support.</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export default function RectorAssignmentsPage() {
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedPriority, setSelectedPriority] = useState<string>('all');
  const [overdueOnly, setOverdueOnly] = useState(false);
  const [search, setSearch] = useState('');

  const {
    data: dashboardData,
    isLoading: isDashboardLoading,
    isError: isDashboardError,
  } = useRectorAssignmentDashboard();

  const { data: listData, isLoading: isListLoading } = useRectorAssignmentList({
    status: selectedStatus !== 'all' ? (selectedStatus as AssignmentStatus) : undefined,
    priority: selectedPriority !== 'all' ? (selectedPriority as AssignmentPriority) : undefined,
    overdue_only: overdueOnly || undefined,
    search: search || undefined,
  });

  if (isDashboardLoading) {
    return <LoadingState message="Loading Rector Assignment dashboard..." />;
  }

  if (isDashboardError) {
    return <ErrorState message="Failed to load rector assignment dashboard." />;
  }

  // -------------------------------------------------------------------------
  // Anti-fake guards — MUST check before rendering any KPI value
  // -------------------------------------------------------------------------
  if (dashboardData && dashboardData.fake_metrics !== false) {
    return (
      <DataQualityError reason="Backend reported fake_metrics=true. KPI values are not safe to display." />
    );
  }

  if (dashboardData && dashboardData.data_source !== 'computed_from_assignments') {
    return (
      <DataQualityError
        reason={`data_source is "${dashboardData.data_source}" — expected "computed_from_assignments".`}
      />
    );
  }

  return (
    <RequirePermission permission={PERMISSIONS.RECTOR_ASSIGNMENTS_DASHBOARD_READ}>
      <div className="min-h-screen bg-gray-50">
        <PageHeader title="Rector Assignment Registry" />

        <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
          {/* KPI Cards — only rendered after guards pass */}
          {dashboardData && (
            <section data-testid="kpi-cards-section">
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                <KpiCard
                  label="Total"
                  value={dashboardData.total_assignments}
                  testId="kpi-total"
                />
                <KpiCard
                  label="Active"
                  value={dashboardData.active_count}
                  color="text-blue-700"
                  testId="kpi-active"
                />
                <KpiCard
                  label="Overdue"
                  value={dashboardData.overdue_count}
                  color="text-red-700"
                  testId="kpi-overdue"
                />
                <KpiCard
                  label="Escalated"
                  value={dashboardData.escalated_count}
                  color="text-red-800"
                  testId="kpi-escalated"
                />
                <KpiCard
                  label="Completed"
                  value={dashboardData.completed_count}
                  color="text-green-700"
                  testId="kpi-completed"
                />
                <KpiCard
                  label="Due This Week"
                  value={dashboardData.due_this_week}
                  color="text-amber-700"
                  testId="kpi-due-week"
                />
              </div>
            </section>
          )}

          {/* Overdue alert */}
          {dashboardData && dashboardData.overdue_count > 0 && (
            <section data-testid="overdue-alert-section">
              <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                <p className="text-sm text-red-800">
                  {dashboardData.overdue_count} assignment
                  {dashboardData.overdue_count !== 1 ? 's are' : ' is'} overdue and require
                  attention.{' '}
                  <Link href="/console/rector-assignments/overdue" className="underline font-medium">
                    View overdue board →
                  </Link>
                </p>
              </div>
            </section>
          )}

          {/* Escalation alert */}
          {dashboardData && dashboardData.escalated_count > 0 && (
            <section data-testid="escalation-alert-section">
              <div className="rounded-lg border border-orange-200 bg-orange-50 p-4">
                <p className="text-sm text-orange-800">
                  {dashboardData.escalated_count} escalated assignment
                  {dashboardData.escalated_count !== 1 ? 's' : ''} require review.{' '}
                  <Link href="/console/rector-assignments/escalations" className="underline font-medium">
                    View escalation queue →
                  </Link>
                </p>
              </div>
            </section>
          )}

          {/* Filters + Create Button */}
          <section data-testid="filters-section">
            <div className="flex flex-wrap items-end gap-4 bg-white rounded-lg shadow p-4">
              <div>
                <label htmlFor="status-filter" className="block text-xs font-medium text-gray-600 mb-1">
                  Status
                </label>
                <select
                  id="status-filter"
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                  data-testid="status-filter"
                >
                  <option value="all">All Statuses</option>
                  {Object.values(AssignmentStatus).map((s) => (
                    <option key={s} value={s}>
                      {STATUS_LABELS[s]}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="priority-filter" className="block text-xs font-medium text-gray-600 mb-1">
                  Priority
                </label>
                <select
                  id="priority-filter"
                  value={selectedPriority}
                  onChange={(e) => setSelectedPriority(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm"
                  data-testid="priority-filter"
                >
                  <option value="all">All Priorities</option>
                  <option value="CRITICAL">Critical</option>
                  <option value="HIGH">High</option>
                  <option value="NORMAL">Normal</option>
                  <option value="LOW">Low</option>
                </select>
              </div>

              <div className="flex items-center gap-2">
                <input
                  id="overdue-only"
                  type="checkbox"
                  checked={overdueOnly}
                  onChange={(e) => setOverdueOnly(e.target.checked)}
                  className="h-4 w-4"
                  data-testid="overdue-only-toggle"
                />
                <label htmlFor="overdue-only" className="text-sm text-gray-700">
                  Overdue only
                </label>
              </div>

              <div>
                <label htmlFor="search-input" className="block text-xs font-medium text-gray-600 mb-1">
                  Search
                </label>
                <input
                  id="search-input"
                  type="text"
                  placeholder="Search assignments..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm w-48"
                  data-testid="search-input"
                />
              </div>

              <div className="ml-auto">
                <PermissionGate permission={PERMISSIONS.RECTOR_ASSIGNMENTS_CREATE}>
                  <Link
                    href="/console/rector-assignments/new"
                    className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700"
                    data-testid="create-assignment-btn"
                  >
                    + New Assignment
                  </Link>
                </PermissionGate>
              </div>
            </div>
          </section>

          {/* Assignment Registry Table */}
          <section data-testid="assignment-list-section">
            <h2 className="text-lg font-semibold mb-3">Assignments</h2>
            {isListLoading ? (
              <LoadingState message="Loading assignments..." />
            ) : listData && listData.length > 0 ? (
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Title
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Priority
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Due Date
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Status
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Action
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {listData.map((a) => (
                      <tr key={a.id} data-testid={`assignment-row-${a.id}`}>
                        <td className="px-6 py-4">
                          <div className="text-sm font-medium text-gray-900">{a.title}</div>
                          {a.is_overdue && (
                            <span className="text-xs text-red-600 font-medium">Overdue</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={priorityClass(a.priority)}
                            data-testid={`priority-${a.id}`}
                          >
                            {formatPriority(a.priority)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                          {a.due_date ? formatDate(a.due_date) : '—'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge
                            variant={STATUS_BADGE_VARIANTS[a.status]}
                            data-testid={`status-badge-${a.id}`}
                          >
                            {STATUS_LABELS[a.status] ?? a.status}
                          </Badge>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <Link
                            href={`/console/rector-assignments/${a.id}`}
                            className="text-blue-600 hover:underline"
                          >
                            View
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-10 text-center" data-testid="empty-list">
                <p className="text-gray-500 mb-4">No assignments found.</p>
                <PermissionGate permission={PERMISSIONS.RECTOR_ASSIGNMENTS_CREATE}>
                  <Link
                    href="/console/rector-assignments/new"
                    className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700"
                  >
                    Create First Assignment
                  </Link>
                </PermissionGate>
              </div>
            )}
          </section>
        </div>
      </div>
    </RequirePermission>
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function KpiCard({
  label,
  value,
  color = 'text-gray-900',
  testId,
}: {
  label: string;
  value: number;
  color?: string;
  testId: string;
}) {
  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <p className="text-xs text-gray-600">{label}</p>
      <p className={`text-2xl font-bold ${color}`} data-testid={testId}>
        {value}
      </p>
    </div>
  );
}

function priorityClass(priority: string): string {
  switch (priority) {
    case 'CRITICAL':
      return 'text-red-700 font-semibold text-sm';
    case 'HIGH':
      return 'text-orange-700 font-semibold text-sm';
    case 'NORMAL':
      return 'text-blue-700 text-sm';
    default:
      return 'text-gray-600 text-sm';
  }
}

function formatPriority(p: string): string {
  const map: Record<string, string> = {
    CRITICAL: 'Critical',
    HIGH: 'High',
    NORMAL: 'Normal',
    LOW: 'Low',
  };
  return map[p] ?? p;
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString();
  } catch {
    return iso;
  }
}
