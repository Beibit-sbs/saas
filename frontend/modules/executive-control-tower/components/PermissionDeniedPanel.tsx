'use client';

import { AccessDenied } from '@/shared/ui/permission-gate';

export function PermissionDeniedPanel({ message }: { message?: string }) {
  return <AccessDenied message={message ?? 'You do not have permission to view this section.'} />;
}