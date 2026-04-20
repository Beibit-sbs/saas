'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import type { CohortReadSchema } from '@/shared/hooks/useInterventionCohorts';

export interface CohortsTableProps {
  cohorts: CohortReadSchema[];
  isLoading?: boolean;
}

type SortField = 'cohort_name' | 'student_count' | 'created_at';
type SortDirection = 'asc' | 'desc';
type StatusFilter = 'draft' | 'finalized' | 'analyzed' | undefined;

const getCohortStatus = (cohort: CohortReadSchema): NonNullable<StatusFilter> =>
  cohort.status;

/**
 * Cohorts Data Table Component
 *
 * Displays cohorts in a sortable, filterable table with:
 * - Columns: ID, Name, Student Count, Status, Date Created, Actions
 * - Sorting by Name and Date Created (click header to toggle)
 * - Status filtering (draft, finalized, analyzed)
 * - Row actions (View, Edit, Delete)
 * - Responsive design
 *
 * @example
 * <CohortsTable cohorts={cohorts} isLoading={isLoading} />
 */
export function CohortsTable({ cohorts, isLoading = false }: CohortsTableProps) {
  const [sortField, setSortField] = useState<SortField>('created_at');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>(undefined);

  // Filter by status
  const filtered = useMemo(() => {
    if (!statusFilter) {
      return cohorts;
    }
    return cohorts.filter((c) => getCohortStatus(c) === statusFilter);
  }, [cohorts, statusFilter]);

  // Sort by field
  const sorted = useMemo(() => {
    const copy = [...filtered];
    copy.sort((a, b) => {
      let aVal: any;
      let bVal: any;

      switch (sortField) {
        case 'cohort_name':
          aVal = a.cohort_name.toLowerCase();
          bVal = b.cohort_name.toLowerCase();
          break;
        case 'student_count':
          aVal = a.student_count;
          bVal = b.student_count;
          break;
        case 'created_at':
          aVal = new Date(a.created_at).getTime();
          bVal = new Date(b.created_at).getTime();
          break;
        default:
          return 0;
      }

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
    return copy;
  }, [filtered, sortField, sortDirection]);

  // Handle column header click to toggle sort
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      // Toggle direction
      setSortDirection((curr) => (curr === 'asc' ? 'desc' : 'asc'));
    } else {
      // New field, default to ascending
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Status badge component
  const StatusBadge = ({ status }: { status: 'draft' | 'finalized' | 'analyzed' }) => {
    const colorClass = {
      draft: 'bg-yellow-100 text-yellow-800',
      finalized: 'bg-blue-100 text-blue-800',
      analyzed: 'bg-green-100 text-green-800',
    }[status];

    return (
      <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ${colorClass}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  // Sort indicator component
  const SortIndicator = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null;
    return <span className="ml-1 text-xs">{sortDirection === 'asc' ? '↑' : '↓'}</span>;
  };

  return (
    <div className="space-y-4">
      {/* Filter Bar */}
      <div className="flex items-center gap-4">
        <label className="text-sm font-medium text-gray-700">Filter by Status:</label>
        <select
          value={statusFilter || ''}
          onChange={(e) => setStatusFilter((e.target.value as StatusFilter) || undefined)}
          className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-blue-500"
        >
          <option value="">All Statuses</option>
          <option value="draft">Draft</option>
          <option value="finalized">Finalized</option>
          <option value="analyzed">Analyzed</option>
        </select>
        {statusFilter && (
          <button
            onClick={() => setStatusFilter(undefined)}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium underline"
          >
            Clear filters
          </button>
        )}
        <span className="text-xs text-gray-600">
          Showing {sorted.length} of {cohorts.length} cohort{cohorts.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto border border-gray-200 rounded-lg">
        <table className="w-full border-collapse text-sm" aria-label="Cohorts">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-700">ID</th>
              <th
                className="px-4 py-3 text-left font-medium text-gray-700 cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('cohort_name')}
                aria-sort={sortField === 'cohort_name' ? (sortDirection === 'asc' ? 'ascending' : 'descending') : 'none'}
              >
                Name <SortIndicator field="cohort_name" />
              </th>
              <th
                className="px-4 py-3 text-left font-medium text-gray-700 cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('student_count')}
                aria-sort={sortField === 'student_count' ? (sortDirection === 'asc' ? 'ascending' : 'descending') : 'none'}
              >
                Size <SortIndicator field="student_count" />
              </th>
              <th className="px-4 py-3 text-left font-medium text-gray-700">Status</th>
              <th
                className="px-4 py-3 text-left font-medium text-gray-700 cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('created_at')}
                aria-sort={sortField === 'created_at' ? (sortDirection === 'asc' ? 'ascending' : 'descending') : 'none'}
              >
                Created <SortIndicator field="created_at" />
              </th>
              <th className="px-4 py-3 text-right font-medium text-gray-700">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading
              ? [1, 2, 3].map((i) => (
                  <tr key={i} className="border-b border-gray-200">
                    <td className="px-4 py-3 h-12 bg-gray-100 animate-pulse" colSpan={6} />
                  </tr>
                ))
              : sorted.map((cohort) => (
                  <tr key={cohort.id} className="border-b border-gray-200 hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-600">#{cohort.id}</td>
                    <td className="px-4 py-3 font-medium text-gray-900">{cohort.cohort_name}</td>
                    <td className="px-4 py-3 text-gray-700">{cohort.student_count} students</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={getCohortStatus(cohort)} />
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {new Date(cohort.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right space-x-2">
                      <Link
                        href={`/console/interventions/cohorts/${cohort.id}`}
                        className="inline-text-xs text-blue-600 hover:text-blue-700 font-medium"
                        aria-label={`View cohort ${cohort.cohort_name}`}
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
          </tbody>
        </table>
      </div>

      {/* Empty state */}
      {!isLoading && sorted.length === 0 && (
        <div className="rounded-lg bg-gray-50 p-8 text-center">
          <p className="text-gray-600">No cohorts match your filters</p>
          <button
            onClick={() => setStatusFilter(undefined)}
            className="mt-2 text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            Clear filters
          </button>
        </div>
      )}
    </div>
  );
}
