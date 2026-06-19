import { describe, expect, it } from 'vitest';
import {
  FINANCE_PROCUREMENT_ASSET_PERMISSIONS,
  FINANCE_PROCUREMENT_ASSET_PERMISSION_COUNT,
  FINANCE_PROCUREMENT_ASSET_ROUTE_PERMISSION_MAP,
  getAllowedFpaRoutes,
  hasAnyFpaPermission,
  hasFpaPermission,
} from '@/modules/finance-procurement-asset/guards';
import { FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES } from '@/modules/finance-procurement-asset/constants';

describe('Finance Procurement Asset guards', () => {
  it('keeps the full permission inventory explicit at 51 entries', () => {
    expect(FINANCE_PROCUREMENT_ASSET_PERMISSION_COUNT).toBe(51);
    expect(FINANCE_PROCUREMENT_ASSET_PERMISSIONS).toHaveLength(51);
  });

  it('fails closed when user permissions are missing', () => {
    expect(hasFpaPermission(undefined, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.overviewRead)).toBe(false);
    expect(hasFpaPermission(undefined, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.dashboardRead)).toBe(false);
  });

  it('denies unknown permissions and only matches exact strings', () => {
    expect(hasFpaPermission(['finance_procurement_asset.unknown'], FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.overviewRead)).toBe(false);
    expect(hasAnyFpaPermission(['finance_procurement_asset.unknown'], [FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.overviewRead])).toBe(false);
  });

  it('maps all 23 routes to required permissions', () => {
    expect(Object.keys(FINANCE_PROCUREMENT_ASSET_ROUTE_PERMISSION_MAP)).toHaveLength(23);
    expect(FINANCE_PROCUREMENT_ASSET_ROUTE_PERMISSION_MAP.overview).toBe(FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.overviewRead);
    expect(FINANCE_PROCUREMENT_ASSET_ROUTE_PERMISSION_MAP['provider-readiness']).toBe(FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.providerReadinessRead);
    expect(FINANCE_PROCUREMENT_ASSET_ROUTE_PERMISSION_MAP['student-finance']).toBe(FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.bridgesStudentFinanceRead);
    expect(FINANCE_PROCUREMENT_ASSET_ROUTE_PERMISSION_MAP.audit).toBe(FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.auditRead);
  });

  it('returns only allowed routes for the current permission set', () => {
    const allowed = getAllowedFpaRoutes([
      FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.overviewRead,
      FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.billingRead,
      FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.limitationsRead,
    ]);

    expect(allowed.map((route) => route.key)).toEqual(['overview', 'billing', 'limitations']);
  });

  it('accepts review/manage permissions only when explicitly granted', () => {
    expect(hasFpaPermission([FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.budgetControlsRead], FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.budgetControlsReview)).toBe(false);
    expect(hasFpaPermission([FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.budgetControlsReview], FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.budgetControlsReview)).toBe(true);
    expect(hasFpaPermission([FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.procurementRequestsRead], FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.procurementRequestsManage)).toBe(false);
    expect(hasFpaPermission([FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.procurementRequestsManage], FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.procurementRequestsManage)).toBe(true);
  });

  it('keeps readiness, bridge, and audit flows fail-closed', () => {
    expect(hasFpaPermission([FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.paymentReadinessRead], FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.paymentReadinessRead)).toBe(true);
    expect(hasFpaPermission([FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.bridgesExecutiveRead], FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.bridgesExecutiveRead)).toBe(true);
    expect(hasFpaPermission([FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.auditRead], FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.auditWrite)).toBe(false);
  });

  it('does not contain forbidden execution, live sync, auto approval, or hidden score permissions', () => {
    expect(FINANCE_PROCUREMENT_ASSET_PERMISSIONS.some((permission) => permission.includes('execute'))).toBe(false);
    expect(FINANCE_PROCUREMENT_ASSET_PERMISSIONS.some((permission) => permission.includes('sync'))).toBe(false);
    expect(FINANCE_PROCUREMENT_ASSET_PERMISSIONS.some((permission) => permission.includes('automatic'))).toBe(false);
    expect(FINANCE_PROCUREMENT_ASSET_PERMISSIONS.some((permission) => permission.includes('score'))).toBe(false);
  });
});
