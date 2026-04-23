'use client';

/**
 * Exam Governance Admin Page
 * Provides oversight of exam scheduling, proctoring, and accessibility accommodations
 */

import React, { useState } from 'react';
import {
  useExamDashboardSummary,
  useExamsList,
  useExamStatistics,
} from '@/modules/exam-governance/hooks';
import { PERMISSIONS } from '@/shared/config/permissions';
import { RequirePermission } from '@/shared/auth/permission-gate';
import { PageHeader } from '@/shared/ui/page-header';
import { LoadingState, ErrorState } from '@/shared/ui/page-states';
import { Badge } from '@/shared/ui/badge';

export default function ExamGovernancePage() {
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedTerm, setSelectedTerm] = useState<string>('');

  const { data: dashboardData, isLoading, isError } = useExamDashboardSummary();
  const {
    data: examsListData,
    isLoading: isListLoading,
    refetch: refetchList,
  } = useExamsList({
    status: selectedStatus !== 'all' ? selectedStatus : undefined,
    term_id: selectedTerm || undefined,
  });

  if (isLoading) {
    return <LoadingState message="Loading exam governance dashboard..." />;
  }

  if (isError) {
    return <ErrorState message="Failed to load exam dashboard" />;
  }

  return (
    <RequirePermission permission={PERMISSIONS.DASHBOARD_READ}>
      <div className="min-h-screen bg-gray-50">
        <PageHeader title="Exam Governance" />

        <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
          {/* Dashboard Summary Section */}
          <section data-testid="dashboard-summary-section">
            <h2 className="text-xl font-semibold mb-4">Summary Overview</h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Total Exams</p>
                <p
                  className="text-2xl font-bold text-gray-900"
                  data-testid="total-exams"
                >
                  {dashboardData?.total_exams || 0}
                </p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Scheduled</p>
                <p
                  className="text-2xl font-bold text-blue-600"
                  data-testid="scheduled-count"
                >
                  {dashboardData?.status_breakdown?.scheduled || 0}
                </p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">In Progress</p>
                <p
                  className="text-2xl font-bold text-orange-600"
                  data-testid="in-progress-count"
                >
                  {dashboardData?.status_breakdown?.in_progress || 0}
                </p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Completed</p>
                <p
                  className="text-2xl font-bold text-green-600"
                  data-testid="completed-count"
                >
                  {dashboardData?.status_breakdown?.completed || 0}
                </p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow">
                <p className="text-sm text-gray-600">Proctors Needed</p>
                <p
                  className="text-2xl font-bold text-purple-600"
                  data-testid="proctors-needed"
                >
                  {dashboardData?.proctors_needed || 0}
                </p>
              </div>
            </div>
          </section>

          {/* Accessibility Accommodations Alert */}
          {dashboardData && dashboardData.students_with_accommodations > 0 && (
            <section data-testid="accommodations-alert-section">
              <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
                <p className="text-sm text-blue-800">
                  ℹ️ {dashboardData.students_with_accommodations} students with registered accessibility accommodations
                </p>
              </div>
            </section>
          )}

          {/* Upcoming Exams Alert */}
          {dashboardData && dashboardData.upcoming_exams_count > 0 && (
            <section data-testid="upcoming-exams-alert-section">
              <div className="bg-green-50 border border-green-200 p-4 rounded-lg">
                <p className="text-sm text-green-800">
                  ✓ {dashboardData.upcoming_exams_count} exams scheduled in the next 7 days
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
                  <option value="scheduled">Scheduled</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>
              <div>
                <label htmlFor="term-filter" className="block text-sm font-medium mb-2">
                  Term
                </label>
                <input
                  id="term-filter"
                  type="text"
                  placeholder="Filter by term (e.g., Spring2026)..."
                  value={selectedTerm}
                  onChange={(e) => setSelectedTerm(e.target.value)}
                  className="w-full md:w-48 px-3 py-2 border border-gray-300 rounded-md"
                  data-testid="term-filter"
                />
              </div>
            </div>
          </section>

          {/* Exams List Section */}
          <section data-testid="exams-list-section">
            <h2 className="text-xl font-semibold mb-4">Exam Management</h2>
            {isListLoading ? (
              <LoadingState message="Loading exams..." />
            ) : examsListData && examsListData.length > 0 ? (
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
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Scheduled Date
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Registrations
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {examsListData.map((exam) => (
                      <tr key={exam.exam_id} data-testid={`exam-row-${exam.exam_id}`}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex flex-col">
                            <span className="text-sm font-medium text-gray-900">
                              {exam.course_code}
                            </span>
                            <span className="text-xs text-gray-600">{exam.course_title}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {exam.faculty_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {exam.exam_type}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                          {new Date(exam.scheduled_date).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Badge
                            variant={getStatusVariant(exam.status)}
                            data-testid={`status-badge-${exam.status}`}
                          >
                            {formatStatus(exam.status)}
                          </Badge>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {exam.registered_count}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <p className="text-gray-500">No exams found</p>
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

function getStatusVariant(status: string): "default" | "success" | "info" | "warning" | "outline" {
  switch (status) {
    case 'scheduled':
      return 'info';
    case 'in_progress':
      return 'warning';
    case 'completed':
      return 'success';
    case 'cancelled':
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
