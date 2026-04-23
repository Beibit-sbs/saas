'use client';

/**
 * Budget Planning & Controls Admin Page
 * Provides oversight of budget allocation, variance analysis, and expense tracking
 */

import React, { useState } from 'react';
import {
  useBudgetDashboardSummary,
  useBudgetsList,
} from '@/modules/budget-planning/hooks';
import { PERMISSIONS } from '@/shared/config/permissions';
import { RequirePermission } from '@/shared/auth/permission-gate';
import { PageHeader } from '@/shared/ui/page-header';
import { LoadingState, ErrorState } from '@/shared/ui/page-states';
import { Badge } from '@/shared/ui/badge';

export default function BudgetPlanningPage() {
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedFiscalYear, setSelectedFiscalYear] = useState<string>('');

  const { data: dashboardData, isLoading, isError } = useBudgetDashboardSummary();
  const {
    data: budgetsListData,
    isLoading: isListLoading,
    refetch: refetchList,
  } = useBudgetsList({
    status: selectedStatus !== 'all' ? selectedStatus : undefined,
    fiscal_year_id: selectedFiscalYear || undefined,
  });

  if (isLoading) {
    return <LoadingState message="Loading budget dashboard..." />;
  }

  if (isError) {
    return <ErrorState message="Failed to load budget data" />;
  }

  return (
    <RequirePermission permission={PERMISSIONS.DASHBOARD_READ}>
      <div className="min-h-screen bg-gray-50">
        <PageHeader title="Budget Planning & Controls" />

        <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
          {/* Dashboard Summary Section */}
          <section data-testid="dashboard-summary-section">
            <h2 className="text-xl font-semibold mb-4">Summary Overview</h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Total Budgets</p>
                <p
                  className="text-2xl font-bold text-gray-900"
                  data-testid="total-budgets"
                >
                  {dashboardData?.total_budgets || 0}
                </p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Total Budgeted</p>
                <p
                  className="text-2xl font-bold text-blue-600"
                  data-testid="total-budgeted"
                >
                  ${(dashboardData?.total_allocated || 0).toLocaleString()}
                </p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Total Spent</p>
                <p
                  className="text-2xl font-bold text-orange-600"
                  data-testid="total-spent"
                >
                  ${(dashboardData?.total_spent || 0).toLocaleString()}
                </p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Available</p>
                <p
                  className="text-2xl font-bold text-green-600"
                  data-testid="total-available"
                >
                  ${(dashboardData?.total_available || 0).toLocaleString()}
                </p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Spend %</p>
                <p
                  className="text-2xl font-bold text-purple-600"
                  data-testid="spend-percentage"
                >
                  {(dashboardData?.spend_percentage || 0).toFixed(1)}%
                </p>
              </div>
            </div>
          </section>

          {/* Variance Alert Section */}
          {dashboardData && dashboardData.unfavorable_variances > 0 && (
            <section data-testid="variance-alert-section">
              <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
                <p className="text-sm text-red-800">
                  ⚠️ {dashboardData.unfavorable_variances} unfavorable variances detected
                </p>
              </div>
            </section>
          )}

          {/* Budget Status Distribution */}
          <section data-testid="status-distribution-section">
            <h2 className="text-xl font-semibold mb-4">Budget Status Distribution</h2>
            <div className="bg-white p-4 rounded-lg shadow space-y-2">
              <div className="flex justify-between">
                <span className="text-sm font-medium">Active</span>
                <span className="text-sm">{dashboardData?.status_breakdown?.active || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Approved</span>
                <span className="text-sm">{dashboardData?.status_breakdown?.approved || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Submitted</span>
                <span className="text-sm">{dashboardData?.status_breakdown?.submitted || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Draft</span>
                <span className="text-sm">{dashboardData?.status_breakdown?.draft || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Closed</span>
                <span className="text-sm">{dashboardData?.status_breakdown?.closed || 0}</span>
              </div>
            </div>
          </section>

          {/* Filters Section */}
          <section data-testid="filters-section">
            <h2 className="text-xl font-semibold mb-4">Filters</h2>
            <div className="bg-white p-4 rounded-lg shadow space-y-4">
              <div>
                <label htmlFor="status-filter" className="block text-sm font-medium mb-2">
                  Status
                </label>
                <select
                  id="status-filter"
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  className="w-full md:w-48 px-3 py-2 border border-gray-300 rounded-md"
                  data-testid="status-filter"
                >
                  <option value="all">All Statuses</option>
                  <option value="draft">Draft</option>
                  <option value="submitted">Submitted</option>
                  <option value="approved">Approved</option>
                  <option value="active">Active</option>
                  <option value="closed">Closed</option>
                </select>
              </div>
              <div>
                <label htmlFor="fiscal-year-filter" className="block text-sm font-medium mb-2">
                  Fiscal Year
                </label>
                <input
                  id="fiscal-year-filter"
                  type="text"
                  placeholder="Filter by fiscal year..."
                  value={selectedFiscalYear}
                  onChange={(e) => setSelectedFiscalYear(e.target.value)}
                  className="w-full md:w-48 px-3 py-2 border border-gray-300 rounded-md"
                  data-testid="fiscal-year-filter"
                />
              </div>
            </div>
          </section>

          {/* Budget List Section */}
          <section data-testid="budget-list-section">
            <h2 className="text-xl font-semibold mb-4">Budget Management</h2>
            {isListLoading ? (
              <LoadingState message="Loading budgets..." />
            ) : budgetsListData && budgetsListData.length > 0 ? (
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Cost Center
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Category
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Budgeted
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Spent
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        % Spent
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {budgetsListData.map((budget) => (
                      <tr key={budget.budget_id} data-testid={`budget-row-${budget.budget_id}`}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-sm font-medium text-gray-900">
                            {budget.cost_center_name}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {budget.category}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          ${budget.total_budgeted.toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          ${budget.total_spent.toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="w-16 bg-gray-200 rounded-full h-2">
                              <div
                                className={`h-2 rounded-full ${
                                  budget.spend_percentage > 90
                                    ? 'bg-red-600'
                                    : budget.spend_percentage > 75
                                    ? 'bg-yellow-600'
                                    : 'bg-green-600'
                                }`}
                                style={{
                                  width: `${Math.min(budget.spend_percentage, 100)}%`,
                                }}
                                data-testid={`progress-bar-${budget.budget_id}`}
                              />
                            </div>
                            <span className="ml-2 text-sm text-gray-600">
                              {budget.spend_percentage.toFixed(1)}%
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge
                            variant={getStatusVariant(budget.status)}
                            data-testid={`status-badge-${budget.status}`}
                          >
                            {formatStatus(budget.status)}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <p className="text-gray-500">No budgets found</p>
              </div>
            )}
          </section>

          {/* Last Updated Footer */}
          <div className="text-right text-xs text-gray-500">
            Last updated: {dashboardData?.last_updated ? new Date(dashboardData.last_updated).toLocaleString() : 'N/A'}
          </div>
        </div>
      </div>
    </RequirePermission>
  );
}

function getStatusVariant(status: string): "default" | "secondary" | "success" | "info" | "warning" | "outline" {
  switch (status) {
    case 'active':
      return 'success';
    case 'approved':
      return 'info';
    case 'submitted':
      return 'warning';
    case 'draft':
      return 'secondary';
    case 'closed':
      return 'outline';
    default:
      return 'default';
  }
}

function formatStatus(status: string): string {
  return status
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}
