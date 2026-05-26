import { describe, expect, it } from 'vitest';
import {
  DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_COUNT,
  DOCUMENT_DECREE_CORRESPONDENCE_PERMISSIONS,
  DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_PERMISSION_MAP,
  getAllowedDdcRoutes,
  hasAnyDdcPermission,
  hasDdcPermission,
} from '@/modules/document-decree-correspondence/guards';
import {
  DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES,
  DOCUMENT_DECREE_CORRESPONDENCE_ROUTES,
} from '@/modules/document-decree-correspondence/constants';

describe('Document Decree Correspondence guards', () => {
  it('keeps permission inventory at 50', () => {
    expect(DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_COUNT).toBe(50);
    expect(DOCUMENT_DECREE_CORRESPONDENCE_PERMISSIONS).toHaveLength(50);
  });

  it('keeps route permission map at 23 routes', () => {
    expect(Object.keys(DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_PERMISSION_MAP)).toHaveLength(23);
    expect(DOCUMENT_DECREE_CORRESPONDENCE_ROUTES).toHaveLength(23);
  });

  it('checks direct permission membership', () => {
    expect(hasDdcPermission([DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.overviewRead], DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.overviewRead)).toBe(true);
    expect(hasDdcPermission([DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.overviewRead], DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.decreesRead)).toBe(false);
  });

  it('checks any-permission membership', () => {
    const granted = [DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.auditRead];
    expect(hasAnyDdcPermission(granted, [DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.auditRead, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.auditWrite])).toBe(true);
    expect(hasAnyDdcPermission(granted, [DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.limitationsRead])).toBe(false);
  });

  it('supports object-shaped permission sources', () => {
    const objectSource = {
      permissions: [DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.overviewRead],
      rolePermissions: [DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.dashboardRead],
      grantedPermissions: [DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.auditRead],
    };

    expect(hasDdcPermission(objectSource, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.dashboardRead)).toBe(true);
    expect(hasDdcPermission(objectSource, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.limitationsRead)).toBe(false);
  });

  it('returns allowed routes based on permission set', () => {
    const routes = getAllowedDdcRoutes([
      DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.overviewRead,
      DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.dashboardRead,
    ]);

    expect(routes.map((route) => route.key)).toEqual(['overview', 'dashboard']);
  });

  it('fail-closes when permissions are missing', () => {
    expect(getAllowedDdcRoutes([])).toEqual([]);
    expect(getAllowedDdcRoutes(undefined)).toEqual([]);
    expect(hasDdcPermission(undefined, DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.overviewRead)).toBe(false);
  });

  it('keeps specific route mapping stable', () => {
    expect(DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_PERMISSION_MAP['signature-readiness']).toBe(
      DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.signatureReadinessRead,
    );
    expect(DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_PERMISSION_MAP.limitations).toBe(
      DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.limitationsRead,
    );
  });
});
