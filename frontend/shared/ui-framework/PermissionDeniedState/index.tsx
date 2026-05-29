'use client';

const roleCopy: Record<'superadmin' | 'tenant_admin' | 'read_only', string> = {
  superadmin: 'This action is blocked by route-level permission policy for the current context.',
  tenant_admin: 'Your tenant-admin scope does not include the required permission for this surface.',
  read_only: 'This surface is read-restricted for read-only users.',
};

export function PermissionDeniedState({
  role,
  requiredPermission,
  reason,
}: {
  role: 'superadmin' | 'tenant_admin' | 'read_only';
  requiredPermission: string;
  reason?: string;
}) {
  return (
    <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6" data-testid="ui-framework-permission-denied-state">
      <h3 className="text-lg font-semibold">Access unavailable</h3>
      <p className="mt-2 text-sm text-muted-foreground">{reason ?? roleCopy[role]}</p>
      <p className="mt-3 text-xs text-muted-foreground">Required permission: {requiredPermission}</p>
    </div>
  );
}