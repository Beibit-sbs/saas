'use client';

import { Suspense } from 'react';
import Link from 'next/link';
import { useAdminAuth } from '@/shared/auth/context';
import { useCohortsQuery } from '@/shared/hooks/useInterventionCohorts';
import { CohortsTable } from './components/CohortsTable';
import { LoadingState, ErrorState } from '@/shared/ui/page-states';

/**
 * Intervention Cohorts List Page
 *
 * Displays all intervention cohorts for the current tenant with
 * filtering, sorting, and actions (view, edit, delete).
 *
 * @route /console/interventions/cohorts
 */
export default function CohortsListPage() {
  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Intervention Cohorts</h1>
          <p className="text-gray-600 mt-1">Manage and analyze intervention effectiveness studies</p>
        </div>
        <Link
          href="/console/interventions/cohorts/create"
          className="inline-flex items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          Create Cohort
        </Link>
      </div>

      <Suspense fallback={<LoadingState />}>
        <CohortsList />
      </Suspense>
    </div>
  );
}

/**
 * Cohorts list component
 *
 * Renders the list of cohorts with loading, error, and empty states.
 * Phase 2 placeholder: shows skeleton only.
 * Phase 3: will replace with full data table including filtering and sorting.
 */
function CohortsList() {
  const { user, isLoading: authLoading } = useAdminAuth();
  const tenantId = user?.tenantId;
  const { data: cohorts, isLoading, error } = useCohortsQuery(tenantId);

  if (authLoading) {
    return <LoadingState title="Loading cohorts" message="Resolving your tenant context." />;
  }

  if (tenantId === undefined) {
    return (
      <ErrorState
        title="Tenant context unavailable"
        message="This page requires a tenant-scoped admin session before cohorts can be loaded."
      />
    );
  }

  if (error) {
    return <ErrorState error={error} title="Failed to load cohorts" />;
  }

  if (isLoading || !cohorts) {
    return <LoadingState title="Loading cohorts" message="Fetching the latest cohort snapshots." />;
  }

  return <CohortsTable cohorts={cohorts} isLoading={isLoading} />;
}
