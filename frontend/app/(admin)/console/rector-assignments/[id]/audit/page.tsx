'use client';

/**
 * Assignment Audit Trail — read-only, requires AUDIT_READ permission.
 */

import React from 'react';
import { useParams } from 'next/navigation';
import { useAssignmentAudit } from '@/modules/rector-assignments/hooks';
import { PERMISSIONS } from '@/shared/config/permissions';
import { RequirePermission } from '@/shared/auth/permission-gate';
import { PageHeader } from '@/shared/ui/page-header';
import { LoadingState, ErrorState } from '@/shared/ui/page-states';

export default function AssignmentAuditPage() {
  const params = useParams();
  const id = params.id as string;

  const { data: audit, isLoading, isError } = useAssignmentAudit(id);

  if (isLoading) return <LoadingState message="Loading audit trail..." />;
  if (isError) return <ErrorState message="Failed to load audit trail." />;

  return (
    <RequirePermission permission={PERMISSIONS.RECTOR_ASSIGNMENTS_AUDIT_READ}>
      <div className="min-h-screen bg-gray-50">
        <PageHeader
          title="Audit Trail"
        />

        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="bg-white rounded-lg shadow overflow-hidden">
            {audit && audit.length > 0 ? (
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-5 py-3 text-left text-xs font-medium text-gray-600 uppercase">
                      Timestamp
                    </th>
                    <th scope="col" className="px-5 py-3 text-left text-xs font-medium text-gray-600 uppercase">
                      Action
                    </th>
                    <th scope="col" className="px-5 py-3 text-left text-xs font-medium text-gray-600 uppercase">
                      Actor
                    </th>
                    <th scope="col" className="px-5 py-3 text-left text-xs font-medium text-gray-600 uppercase">
                      Details
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {audit.map((event) => (
                    <tr key={event.id} data-testid={`audit-row-${event.id}`}>
                      <td className="px-5 py-3 text-xs text-gray-600 whitespace-nowrap">
                        {new Date(event.created_at).toLocaleString()}
                      </td>
                      <td className="px-5 py-3 text-sm font-medium text-gray-800">
                        {event.event_type}
                      </td>
                      <td className="px-5 py-3 text-sm text-gray-700">
                        {event.actor_id ?? '—'}
                      </td>
                      <td className="px-5 py-3 text-xs text-gray-500">
                        {event.payload ? (
                          <pre className="whitespace-pre-wrap max-w-xs overflow-hidden text-xs">
                            {JSON.stringify(event.payload, null, 2)}
                          </pre>
                        ) : (
                          '—'
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-10 text-center" data-testid="empty-audit">
                <p className="text-gray-500">No audit events found for this assignment.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </RequirePermission>
  );
}
