"use client";

export function TenantScopeNotice({ tenantId }: { tenantId?: number }) {
  if (!tenantId) {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900" data-testid="acrm-tenant-missing">
        Tenant context is required. This module is fail-closed without tenant scope.
      </div>
    );
  }
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700" data-testid="acrm-tenant-scope">
      Tenant scope active: {tenantId}
    </div>
  );
}
