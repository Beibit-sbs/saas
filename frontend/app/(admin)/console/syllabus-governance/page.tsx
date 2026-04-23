'use client';

/**
 * Syllabus Governance Admin Page
 * Provides oversight of syllabus lifecycle, approval workflows, and content governance
 */

import React, { useState } from 'react';
import {
  useSyllabusDashboardSummary,
  useSyllabusList,
  useApprovalWorkflow,
} from '@/modules/syllabus-governance/hooks';
import { PERMISSIONS } from '@/shared/config/permissions';
import { RequirePermission } from '@/shared/auth/permission-gate';
import { PageHeader } from '@/shared/ui/page-header';
import { LoadingState, ErrorState } from '@/shared/ui/page-states';
import { Badge } from '@/shared/ui/badge';

export default function SyllabusGovernancePage() {
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedDepartment, setSelectedDepartment] = useState<string>('');

  const { data: dashboardData, isLoading, isError } = useSyllabusDashboardSummary();
  const {
    data: syllabusListData,
    isLoading: isListLoading,
    refetch: refetchList,
  } = useSyllabusList({
    status: selectedStatus !== 'all' ? selectedStatus : undefined,
    department_id: selectedDepartment || undefined,
  });

  if (isLoading) {
    return <LoadingState message="Loading syllabus governance dashboard..." />;
  }

  if (isError) {
    return <ErrorState message="Failed to load syllabus dashboard" />;
  }

  return (
    <RequirePermission permission={PERMISSIONS.DASHBOARD_READ}>
      <div className="min-h-screen bg-gray-50">
        <PageHeader title="Syllabus Governance" />

        <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
          {/* Dashboard Summary Section */}
          <section data-testid="dashboard-summary-section">
            <h2 className="text-xl font-semibold mb-4">Summary Overview</h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Total Syllabi</p>
                <p
                  className="text-2xl font-bold text-gray-900"
                  data-testid="total-syllabi"
                >
                  {dashboardData?.total_syllabi || 0}
                </p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Published</p>
                <p
                  className="text-2xl font-bold text-green-600"
                  data-testid="published-count"
                >
                  {dashboardData?.status_breakdown?.published || 0}
                </p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Under Review</p>
                <p
                  className="text-2xl font-bold text-blue-600"
                  data-testid="under-review-count"
                >
                  {dashboardData?.status_breakdown?.under_review || 0}
                </p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Drafts</p>
                <p
                  className="text-2xl font-bold text-gray-600"
                  data-testid="draft-count"
                >
                  {dashboardData?.status_breakdown?.draft || 0}
                </p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Pending Approvals</p>
                <p
                  className="text-2xl font-bold text-orange-600"
                  data-testid="pending-approvals"
                >
                  {dashboardData?.pending_approvals || 0}
                </p>
              </div>
            </div>
          </section>

          {/* Alerts Section */}
          {(dashboardData?.expiring_syllabi ?? 0) > 0 && (
            <section data-testid="alerts-section">
              <h2 className="text-xl font-semibold mb-4">Alerts</h2>
              <div className="bg-yellow-50 border border-yellow-200 p-4 rounded-lg">
                <p className="text-sm text-yellow-800">
                  ⚠️ {dashboardData?.expiring_syllabi ?? 0} syllabi are expiring soon and need renewal
                </p>
              </div>
            </section>
          )}

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
                  <option value="under_review">Under Review</option>
                  <option value="approved">Approved</option>
                  <option value="published">Published</option>
                  <option value="archived">Archived</option>
                </select>
              </div>
              <div>
                <label htmlFor="department-filter" className="block text-sm font-medium mb-2">
                  Department
                </label>
                <input
                  id="department-filter"
                  type="text"
                  placeholder="Filter by department..."
                  value={selectedDepartment}
                  onChange={(e) => setSelectedDepartment(e.target.value)}
                  className="w-full md:w-48 px-3 py-2 border border-gray-300 rounded-md"
                  data-testid="department-filter"
                />
              </div>
            </div>
          </section>

          {/* Syllabi List Section */}
          <section data-testid="syllabi-list-section">
            <h2 className="text-xl font-semibold mb-4">Syllabus Management</h2>
            {isListLoading ? (
              <LoadingState message="Loading syllabi..." />
            ) : syllabusListData && syllabusListData.length > 0 ? (
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Course
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Faculty
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Term
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Last Updated
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {syllabusListData.map((syllabus) => (
                      <tr key={syllabus.syllabi_id} data-testid={`syllabus-row-${syllabus.syllabi_id}`}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex flex-col">
                            <span className="text-sm font-medium text-gray-900">
                              {syllabus.course_code}
                            </span>
                            <span className="text-xs text-gray-600">{syllabus.course_title}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {syllabus.faculty_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge
                            variant={getStatusVariant(syllabus.status)}
                            data-testid={`status-badge-${syllabus.status}`}
                          >
                            {formatStatus(syllabus.status)}
                          </Badge>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {syllabus.term_id}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {new Date(syllabus.updated_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <p className="text-gray-500">No syllabi found</p>
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
    case 'published':
      return 'success';
    case 'approved':
      return 'info';
    case 'under_review':
      return 'warning';
    case 'draft':
      return 'secondary';
    case 'archived':
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
