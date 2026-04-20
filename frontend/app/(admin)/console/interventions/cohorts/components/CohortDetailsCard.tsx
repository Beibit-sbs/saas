import type { CohortReadSchema } from '@/shared/hooks/useInterventionCohorts';

interface CohortDetailsCardProps {
  cohort: CohortReadSchema;
}

export function CohortDetailsCard({ cohort }: CohortDetailsCardProps) {
  const statusClass = {
    draft: 'bg-yellow-100 text-yellow-800',
    finalized: 'bg-blue-100 text-blue-800',
    analyzed: 'bg-green-100 text-green-800',
  }[cohort.status];

  return (
    <div className="grid grid-cols-1 gap-4 rounded-lg border border-gray-200 bg-white p-6 md:grid-cols-2">
      <div>
        <p className="text-sm font-medium text-gray-500">Status</p>
        <span className={`mt-1 inline-flex items-center rounded-md px-2 py-1 text-sm font-medium ${statusClass}`}>
          {cohort.status.charAt(0).toUpperCase() + cohort.status.slice(1)}
        </span>
      </div>
      <div>
        <p className="text-sm font-medium text-gray-500">Student Count</p>
        <p className="text-2xl font-bold text-gray-900">{cohort.student_count}</p>
      </div>
      <div>
        <p className="text-sm font-medium text-gray-500">Data Completeness</p>
        <p className="text-2xl font-bold text-gray-900">
          {cohort.data_completeness_pct != null ? `${Number(cohort.data_completeness_pct).toFixed(1)}%` : 'N/A'}
        </p>
      </div>
      <div>
        <p className="text-sm font-medium text-gray-500">Analysis Window</p>
        <p className="text-gray-900">
          {new Date(cohort.analysis_window_start).toLocaleDateString()} to{' '}
          {new Date(cohort.analysis_window_end).toLocaleDateString()}
        </p>
      </div>
      <div>
        <p className="text-sm font-medium text-gray-500">Created By</p>
        <p className="text-gray-900">{cohort.created_by}</p>
      </div>
    </div>
  );
}