'use client';

/**
 * Procurement Workflow Admin Page
 * Provides oversight of request, approval, and order lifecycle
 */

import React, { useState } from 'react';
import {
  useProcurementDashboardSummary,
  useProcurementList,
} from '@/modules/procurement-workflow/hooks';
import { PERMISSIONS } from '@/shared/config/permissions';
import { RequirePermission } from '@/shared/auth/permission-gate';
import { PageHeader } from '@/shared/ui/page-header';
import { LoadingState, ErrorState } from '@/shared/ui/page-states';
import { Badge } from '@/shared/ui/badge';

export default function ProcurementWorkflowPage() {
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedRequester, setSelectedRequester] = useState<string>('');

  const { data: dashboardData, isLoading, isError } = useProcurementDashboardSummary();
  const { data: requestsData, isLoading: isListLoading } = useProcurementList({
    status: selectedStatus !== 'all' ? selectedStatus : undefined,
    requester_id: selectedRequester || undefined,
  });

  if (isLoading) {
    return <LoadingState message="Loading procurement dashboard..." />;
  }

  if (isError) {
    return <ErrorState message="Failed to load procurement data" />;
  }

  return (
    <RequirePermission permission={PERMISSIONS.DASHBOARD_READ}>
      <div className="min-h-screen bg-gray-50">
        <PageHeader title="Procurement Workflow" />

        <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
          <section data-testid="dashboard-summary-section">
            <h2 className="text-xl font-semibold mb-4">Summary Overview</h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Total Requests</p>
                <p className="text-2xl font-bold text-gray-900" data-testid="total-requests">
                  {dashboardData?.total_requests || 0}
                </p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Pending Approvals</p>
                <p className="text-2xl font-bold text-amber-600" data-testid="pending-approvals">
                  {dashboardData?.total_pending_approvals || 0}
                </p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Ordered Value</p>
                <p className="text-2xl font-bold text-blue-600" data-testid="ordered-value">
                  ${(dashboardData?.total_ordered_value || 0).toLocaleString()}
                </p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Overdue Requests</p>
                <p className="text-2xl font-bold text-red-600" data-testid="overdue-requests">
                  {dashboardData?.overdue_requests || 0}
                </p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Approved</p>
                <p className="text-2xl font-bold text-emerald-600" data-testid="approved-count">
                  {dashboardData?.status_breakdown?.approved || 0}
                </p>
              </div>
            </div>
          </section>

          {dashboardData && dashboardData.overdue_requests > 0 && (
            <section data-testid="overdue-alert-section">
              <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
                <p className="text-sm text-red-800">
                  {dashboardData.overdue_requests} overdue procurement requests require attention
                </p>
              </div>
            </section>
          )}

          <section data-testid="status-distribution-section">
            <h2 className="text-xl font-semibold mb-4">Request Status Distribution</h2>
            <div className="bg-white p-4 rounded-lg shadow space-y-2">
              <div className="flex justify-between"><span className="text-sm font-medium">Draft</span><span className="text-sm">{dashboardData?.status_breakdown?.draft || 0}</span></div>
              <div className="flex justify-between"><span className="text-sm font-medium">Submitted</span><span className="text-sm">{dashboardData?.status_breakdown?.submitted || 0}</span></div>
              <div className="flex justify-between"><span className="text-sm font-medium">Under Review</span><span className="text-sm">{dashboardData?.status_breakdown?.under_review || 0}</span></div>
              <div className="flex justify-between"><span className="text-sm font-medium">Approved</span><span className="text-sm">{dashboardData?.status_breakdown?.approved || 0}</span></div>
              <div className="flex justify-between"><span className="text-sm font-medium">Ordered</span><span className="text-sm">{dashboardData?.status_breakdown?.ordered || 0}</span></div>
              <div className="flex justify-between"><span className="text-sm font-medium">Fulfilled</span><span className="text-sm">{dashboardData?.status_breakdown?.fulfilled || 0}</span></div>
            </div>
          </section>

          <section data-testid="filters-section">
            <h2 className="text-xl font-semibold mb-4">Filters</h2>
            <div className="bg-white p-4 rounded-lg shadow space-y-4">
              <div>
                <label htmlFor="status-filter" className="block text-sm font-medium mb-2">Status</label>
                <select
                  id="status-filter"
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  className="w-full md:w-56 px-3 py-2 border border-gray-300 rounded-md"
                  data-testid="status-filter"
                >
                  <option value="all">All Statuses</option>
                  <option value="draft">Draft</option>
                  <option value="submitted">Submitted</option>
                  <option value="under_review">Under Review</option>
                  <option value="approved">Approved</option>
                  <option value="rejected">Rejected</option>
                  <option value="ordered">Ordered</option>
                  <option value="fulfilled">Fulfilled</option>
                </select>
              </div>
              <div>
                <label htmlFor="requester-filter" className="block text-sm font-medium mb-2">Requester</label>
                <input
                  id="requester-filter"
                  type="text"
                  placeholder="Filter by requester ID..."
                  value={selectedRequester}
                  onChange={(e) => setSelectedRequester(e.target.value)}
                  className="w-full md:w-56 px-3 py-2 border border-gray-300 rounded-md"
                  data-testid="requester-filter"
                />
              </div>
            </div>
          </section>

          <section data-testid="requests-list-section">
            <h2 className="text-xl font-semibold mb-4">Procurement Requests</h2>
            {isListLoading ? (
              <LoadingState message="Loading procurement requests..." />
            ) : requestsData && requestsData.length > 0 ? (
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Request</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Requester</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Department</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Priority</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Estimated</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {requestsData.map((request) => (
                      <tr key={request.request_id} data-testid={`request-row-${request.request_id}`}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{request.request_number}</div>
                          <div className="text-xs text-gray-600">{request.title}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{request.requester_name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{request.department_name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <span className={priorityClass(request.priority)} data-testid={`priority-${request.request_id}`}>
                            {formatValue(request.priority)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${request.estimated_total.toLocaleString()}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge variant={statusVariant(request.status)} data-testid={`status-badge-${request.status}`}>
                            {formatValue(request.status)}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <p className="text-gray-500">No procurement requests found</p>
              </div>
            )}
          </section>

          <div className="text-right text-xs text-gray-500">
            Last updated: {dashboardData?.last_updated ? new Date(dashboardData.last_updated).toLocaleString() : 'N/A'}
          </div>
        </div>
      </div>
    </RequirePermission>
  );
}

function formatValue(value: string): string {
  return value
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function statusVariant(status: string): "default" | "secondary" | "destructive" | "success" | "info" | "warning" {
  switch (status) {
    case 'approved':
    case 'fulfilled':
      return 'success';
    case 'under_review':
    case 'submitted':
      return 'warning';
    case 'ordered':
      return 'info';
    case 'rejected':
    case 'cancelled':
      return 'destructive';
    case 'draft':
      return 'secondary';
    default:
      return 'default';
  }
}

function priorityClass(priority: string): string {
  switch (priority) {
    case 'critical':
      return 'text-red-700 font-semibold';
    case 'high':
      return 'text-orange-700 font-semibold';
    case 'medium':
      return 'text-blue-700';
    default:
      return 'text-gray-700';
  }
}
