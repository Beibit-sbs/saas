'use client';

/**
 * Escalation Policy Manager — /console/rector-assignments/escalation-policies
 *
 * Manage escalation rules for rector assignments.
 * Requires escalation_policy.manage permission.
 * All escalations require manual confirmation — no autonomous dispatch.
 */

import React from 'react';
import { PERMISSIONS } from '@/shared/config/permissions';
import { RequirePermission } from '@/shared/auth/permission-gate';
import { PageHeader } from '@/shared/ui/page-header';
import { EscalationPolicyManager } from '@/modules/rector-assignments/components/EscalationPolicyManager';

export default function EscalationPoliciesPage() {
  return (
    <RequirePermission permission={PERMISSIONS.RECTOR_ASSIGNMENTS_ESCALATION_POLICY_MANAGE}>
      <div className="min-h-screen bg-gray-50">
        <PageHeader
          title="Escalation Policies"
          description="Configure escalation rules for rector assignments. All escalations require manual confirmation."
        />

        <div className="max-w-6xl mx-auto px-4 py-8">
          <EscalationPolicyManager />
        </div>
      </div>
    </RequirePermission>
  );
}
