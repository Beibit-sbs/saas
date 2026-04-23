'use client';

/**
 * Contracts & Legal Repository Admin Page
 * Provides registry oversight, status workflow control, and legal search
 */

import React, { useState } from 'react';
import {
  useContractDashboardSummary,
  useContractsList,
} from '@/modules/contracts-legal-repository/hooks';
import { PERMISSIONS } from '@/shared/config/permissions';
import { RequirePermission } from '@/shared/auth/permission-gate';
import { PageHeader } from '@/shared/ui/page-header';
import { LoadingState, ErrorState } from '@/shared/ui/page-states';
import { Badge } from '@/shared/ui/badge';

export default function ContractsLegalRepositoryPage() {
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');

  const { data: dashboardData, isLoading, isError } = useContractDashboardSummary();
  const { data: contractsData, isLoading: isListLoading } = useContractsList({
    status: selectedStatus !== 'all' ? selectedStatus : undefined,
    type: selectedType !== 'all' ? selectedType : undefined,
  });

  if (isLoading) {
    return <LoadingState message="Loading contracts dashboard..." />;
  }

  if (isError) {
    return <ErrorState message="Failed to load contracts data" />;
  }

  return (
    <RequirePermission permission={PERMISSIONS.DASHBOARD_READ}>
      <div className="min-h-screen bg-gray-50">
        <PageHeader title="Contracts & Legal Repository" />

        <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
          <section data-testid="dashboard-summary-section">
            <h2 className="text-xl font-semibold mb-4">Summary Overview</h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Total Contracts</p>
                <p className="text-2xl font-bold text-gray-900" data-testid="total-contracts">
                  {dashboardData?.total_contracts || 0}
                </p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Expiring (30d)</p>
                <p className="text-2xl font-bold text-orange-600" data-testid="expiring-30-days">
                  {dashboardData?.expiring_30_days || 0}
                </p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">High Risk</p>
                <p className="text-2xl font-bold text-red-600" data-testid="high-risk-count">
                  {dashboardData?.high_risk_count || 0}
                </p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Active Value</p>
                <p className="text-2xl font-bold text-blue-600" data-testid="total-active-value">
                  ${(dashboardData?.total_active_value || 0).toLocaleString()}
                </p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Active</p>
                <p className="text-2xl font-bold text-emerald-600" data-testid="active-count">
                  {dashboardData?.status_breakdown?.active || 0}
                </p>
              </div>
            </div>
          </section>

          {dashboardData && dashboardData.expiring_30_days > 0 && (
            <section data-testid="expiry-alert-section">
              <div className="bg-amber-50 border border-amber-200 p-4 rounded-lg">
                <p className="text-sm text-amber-800">
                  {dashboardData.expiring_30_days} contracts are approaching expiry within 30 days
                </p>
              </div>
            </section>
          )}

          <section data-testid="status-distribution-section">
            <h2 className="text-xl font-semibold mb-4">Contract Status Distribution</h2>
            <div className="bg-white p-4 rounded-lg shadow space-y-2">
              <div className="flex justify-between"><span className="text-sm font-medium">Draft</span><span className="text-sm">{dashboardData?.status_breakdown?.draft || 0}</span></div>
              <div className="flex justify-between"><span className="text-sm font-medium">In Review</span><span className="text-sm">{dashboardData?.status_breakdown?.in_review || 0}</span></div>
              <div className="flex justify-between"><span className="text-sm font-medium">Approved</span><span className="text-sm">{dashboardData?.status_breakdown?.approved || 0}</span></div>
              <div className="flex justify-between"><span className="text-sm font-medium">Active</span><span className="text-sm">{dashboardData?.status_breakdown?.active || 0}</span></div>
              <div className="flex justify-between"><span className="text-sm font-medium">Expiring</span><span className="text-sm">{dashboardData?.status_breakdown?.expiring || 0}</span></div>
              <div className="flex justify-between"><span className="text-sm font-medium">Expired</span><span className="text-sm">{dashboardData?.status_breakdown?.expired || 0}</span></div>
            </div>
          </section>

          <section data-testid="filters-section">
            <h2 className="text-xl font-semibold mb-4">Filters</h2>
            <div className="bg-white p-4 rounded-lg shadow grid md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="status-filter" className="block text-sm font-medium mb-2">Status</label>
                <select
                  id="status-filter"
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  data-testid="status-filter"
                >
                  <option value="all">All Statuses</option>
                  <option value="draft">Draft</option>
                  <option value="in_review">In Review</option>
                  <option value="approved">Approved</option>
                  <option value="active">Active</option>
                  <option value="expiring">Expiring</option>
                  <option value="expired">Expired</option>
                  <option value="terminated">Terminated</option>
                </select>
              </div>
              <div>
                <label htmlFor="type-filter" className="block text-sm font-medium mb-2">Type</label>
                <select
                  id="type-filter"
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  data-testid="type-filter"
                >
                  <option value="all">All Types</option>
                  <option value="vendor">Vendor</option>
                  <option value="service">Service</option>
                  <option value="employment">Employment</option>
                  <option value="partnership">Partnership</option>
                  <option value="lease">Lease</option>
                  <option value="grant">Grant</option>
                </select>
              </div>
            </div>
          </section>

          <section data-testid="contracts-list-section">
            <h2 className="text-xl font-semibold mb-4">Contract Registry</h2>
            {isListLoading ? (
              <LoadingState message="Loading contracts..." />
            ) : contractsData && contractsData.length > 0 ? (
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Contract</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Counterparty</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Risk</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">End Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {contractsData.map((contract) => (
                      <tr key={contract.contract_id} data-testid={`contract-row-${contract.contract_id}`}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{contract.contract_number}</div>
                          <div className="text-xs text-gray-600">{contract.title}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{formatValue(contract.type)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{contract.counterparty}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={riskClass(contract.risk_level)} data-testid={`risk-${contract.contract_id}`}>
                            {formatValue(contract.risk_level)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{new Date(contract.end_date).toLocaleDateString()}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge variant={statusVariant(contract.status)} data-testid={`status-badge-${contract.status}`}>
                            {formatValue(contract.status)}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <p className="text-gray-500">No contracts found</p>
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

function statusVariant(status: string): "default" | "secondary" | "destructive" | "success" | "warning" {
  switch (status) {
    case 'active':
    case 'approved':
      return 'success';
    case 'in_review':
    case 'expiring':
      return 'warning';
    case 'expired':
      return 'secondary';
    case 'terminated':
      return 'destructive';
    case 'draft':
      return 'default';
    default:
      return 'default';
  }
}

function riskClass(risk: string): string {
  switch (risk) {
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
