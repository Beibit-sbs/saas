'use client';

/**
 * Executor Report Submission Form
 * POST /api/admin/rector-assignments/{id}/reports
 */

import React, { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  useRectorAssignmentDetail,
  useSubmitReport,
} from '@/modules/rector-assignments/hooks';
import { canSubmitReportByStatus } from '@/modules/rector-assignments/status';
import { PERMISSIONS } from '@/shared/config/permissions';
import { RequirePermission } from '@/shared/auth/permission-gate';
import { PageHeader } from '@/shared/ui/page-header';
import { LoadingState, ErrorState } from '@/shared/ui/page-states';

export default function SubmitReportPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const { data: a, isLoading: detailLoading, isError: detailError } = useRectorAssignmentDetail(id);
  const submitMut = useSubmitReport(id);

  const today = new Date().toISOString().split('T')[0];
  const [summary, setSummary] = useState('');
  const [nextSteps, setNextSteps] = useState('');
  const [progressPercent, setProgressPercent] = useState(100);
  const [periodStart, setPeriodStart] = useState(today);
  const [periodEnd, setPeriodEnd] = useState(today);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [globalError, setGlobalError] = useState('');
  const [submitted, setSubmitted] = useState(false);

  if (detailLoading) return <LoadingState message="Loading assignment..." />;
  if (detailError || !a) return <ErrorState message="Failed to load assignment." />;

  if (!canSubmitReportByStatus(a.status)) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow p-10 text-center">
          <p className="text-gray-700 font-medium mb-2">Report submission not available</p>
          <p className="text-sm text-gray-500 mb-4">
            Assignments in status &ldquo;{a.status}&rdquo; cannot receive new reports.
          </p>
          <button
            onClick={() => router.back()}
            className="text-blue-600 hover:underline text-sm"
          >
            Go back
          </button>
        </div>
      </div>
    );
  }

  function validate(): boolean {
    const errors: Record<string, string> = {};
    if (!summary.trim()) {
      errors.summary = 'Summary is required.';
    } else if (summary.trim().length < 10) {
      errors.summary = 'Summary must be at least 10 characters.';
    } else if (summary.trim().length > 5000) {
      errors.summary = 'Summary must be 5000 characters or fewer.';
    }
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setGlobalError('');
    if (!validate()) return;

    try {
      await submitMut.mutateAsync({
        summary: summary.trim(),
        next_steps: nextSteps.trim() || undefined,
        progress_percent: progressPercent,
        reporting_period_start: periodStart,
        reporting_period_end: periodEnd,
      });
      setSubmitted(true);
    } catch {
      setGlobalError('Failed to submit report. Please try again.');
    }
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow p-10 text-center" data-testid="report-submitted-success">
          <p className="text-green-700 font-medium text-lg mb-2">Report Submitted</p>
          <p className="text-sm text-gray-500 mb-6">
            Your report for &ldquo;{a.title}&rdquo; has been submitted successfully.
          </p>
          <button
            onClick={() => router.push(`/console/my-assignments/${id}`)}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700"
          >
            Back to Assignment
          </button>
        </div>
      </div>
    );
  }

  return (
    <RequirePermission permission={PERMISSIONS.RECTOR_ASSIGNMENTS_REPORT_SUBMIT}>
      <div className="min-h-screen bg-gray-50">
        <PageHeader
          title="Submit Report"
        />

        <div className="max-w-2xl mx-auto px-4 py-8">
          <div className="bg-white rounded-lg shadow p-6">
            {globalError && (
              <div
                className="mb-4 p-3 border border-red-200 bg-red-50 text-red-700 text-sm rounded"
                role="alert"
                data-testid="global-error"
              >
                {globalError}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5" data-testid="report-form" noValidate>
              <div>
                <label htmlFor="summary" className="block text-sm font-medium text-gray-700 mb-1">
                  Execution Summary <span className="text-red-500">*</span>
                </label>
                <textarea
                  id="summary"
                  value={summary}
                  onChange={(e) => setSummary(e.target.value)}
                  rows={6}
                  placeholder="Describe what was accomplished..."
                  className={`w-full px-3 py-2 border rounded-md text-sm ${
                    fieldErrors.summary ? 'border-red-400' : 'border-gray-300'
                  }`}
                  data-testid="summary-input"
                  required
                />
                {fieldErrors.summary && (
                  <p className="mt-1 text-xs text-red-600" role="alert">{fieldErrors.summary}</p>
                )}
                <p className="mt-1 text-xs text-gray-500">{summary.length} / 5000</p>
              </div>

              <div>
                <label htmlFor="next-steps" className="block text-sm font-medium text-gray-700 mb-1">
                  Next Steps
                </label>
                <textarea
                  id="next-steps"
                  value={nextSteps}
                  onChange={(e) => setNextSteps(e.target.value)}
                  rows={3}
                  placeholder="List next steps..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  data-testid="next-steps-input"
                />
              </div>

              <div className="flex gap-3">
                <button
                  type="submit"
                  disabled={submitMut.isPending}
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  data-testid="submit-report-btn"
                >
                  {submitMut.isPending ? 'Submitting...' : 'Submit Report'}
                </button>
                <button
                  type="button"
                  onClick={() => router.back()}
                  className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                  data-testid="cancel-report-btn"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </RequirePermission>
  );
}
