'use client';

/**
 * Notification Registry — /console/rector-assignments/notifications
 *
 * Global outbox event registry.
 * Requires outbox.read permission.
 * Live email/SMS dispatch is NOT enabled.
 */

import React from 'react';
import { PERMISSIONS } from '@/shared/config/permissions';
import { RequirePermission } from '@/shared/auth/permission-gate';
import { PageHeader } from '@/shared/ui/page-header';
import { OutboxRegistry } from '@/modules/rector-assignments/components/OutboxRegistry';

export default function NotificationsPage() {
  return (
    <RequirePermission permission={PERMISSIONS.RECTOR_ASSIGNMENTS_OUTBOX_READ}>
      <div className="min-h-screen bg-gray-50">
        <PageHeader
          title="Notification Registry"
          description="Notification intent records. Live dispatch is not enabled for this release."
        />

        <div className="max-w-7xl mx-auto px-4 py-8">
          <OutboxRegistry />
        </div>
      </div>
    </RequirePermission>
  );
}
