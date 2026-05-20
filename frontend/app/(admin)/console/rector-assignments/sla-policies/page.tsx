'use client';

/**
 * SLA Policy Manager — /console/rector-assignments/sla-policies
 *
 * Manage SLA thresholds for rector assignments by priority.
 * Requires sla.manage permission.
 */

import React from 'react';
import { PERMISSIONS } from '@/shared/config/permissions';
import { RequirePermission } from '@/shared/auth/permission-gate';
import { PageHeader } from '@/shared/ui/page-header';
import { SlaPolicyManager } from '@/modules/rector-assignments/components/SlaPolicyManager';

export default function SlaPoliciesPage() {
  return (
    <RequirePermission permission={PERMISSIONS.RECTOR_ASSIGNMENTS_SLA_MANAGE}>
      <div className="min-h-screen bg-gray-50">
        <PageHeader
          title="SLA Policies"
          description="Configure SLA thresholds for rector assignment priorities."
        />

        <div className="max-w-6xl mx-auto px-4 py-8">
          <SlaPolicyManager />
        </div>
      </div>
    </RequirePermission>
  );
}
