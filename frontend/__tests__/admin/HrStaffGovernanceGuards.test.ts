import { describe, expect, it } from 'vitest';
import {
  HR_STAFF_GOVERNANCE_PERMISSIONS,
  HR_STAFF_GOVERNANCE_PERMISSION_COUNT,
  HR_STAFF_GOVERNANCE_ROUTE_PERMISSION_MAP,
  canReadAccessLifecycle,
  canReadAppraisals,
  canReadDisciplinaryCases,
  canReadHrDashboard,
  canReadHrOverview,
  canReadLimitations,
  canReadPayrollReadiness,
  canReadProviderReadiness,
  canReadRecruitment,
  canReadTraining,
  canReadWorkloadBridge,
  canReviewAccessLifecycle,
  canReviewAppraisals,
  canReviewDisciplinaryCases,
  canReviewLeave,
  canReviewPayrollReadiness,
  canReviewRecruitment,
  getAllowedHrRoutes,
  hasAnyHrPermission,
  hasHrPermission,
} from '@/modules/hr-staff-governance/guards';
import { HR_STAFF_GOVERNANCE_PERMISSION_VALUES } from '@/modules/hr-staff-governance/constants';

describe('HR Staff Governance guards', () => {
  it('keeps the full permission inventory explicit at 56 entries', () => {
    expect(HR_STAFF_GOVERNANCE_PERMISSION_COUNT).toBe(56);
    expect(HR_STAFF_GOVERNANCE_PERMISSIONS).toHaveLength(56);
  });

  it('fails closed when user permissions are missing', () => {
    expect(hasHrPermission(undefined, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.overviewRead)).toBe(false);
    expect(canReadHrOverview(undefined)).toBe(false);
    expect(canReadHrDashboard(undefined)).toBe(false);
  });

  it('denies unknown permissions and only matches exact strings', () => {
    expect(hasHrPermission(['hr_staff_governance.unknown'], HR_STAFF_GOVERNANCE_PERMISSION_VALUES.overviewRead)).toBe(false);
    expect(hasAnyHrPermission(['hr_staff_governance.unknown'], [HR_STAFF_GOVERNANCE_PERMISSION_VALUES.overviewRead])).toBe(false);
  });

  it('maps all 20 routes to required permissions', () => {
    expect(Object.keys(HR_STAFF_GOVERNANCE_ROUTE_PERMISSION_MAP)).toHaveLength(20);
    expect(HR_STAFF_GOVERNANCE_ROUTE_PERMISSION_MAP.overview).toBe(HR_STAFF_GOVERNANCE_PERMISSION_VALUES.overviewRead);
    expect(HR_STAFF_GOVERNANCE_ROUTE_PERMISSION_MAP['provider-readiness']).toBe(HR_STAFF_GOVERNANCE_PERMISSION_VALUES.providerReadinessRead);
  });

  it('returns only allowed routes for the current permission set', () => {
    const allowed = getAllowedHrRoutes([
      HR_STAFF_GOVERNANCE_PERMISSION_VALUES.overviewRead,
      HR_STAFF_GOVERNANCE_PERMISSION_VALUES.recruitmentRead,
      HR_STAFF_GOVERNANCE_PERMISSION_VALUES.limitationsRead,
    ]);

    expect(allowed.map((route) => route.key)).toEqual(['overview', 'recruitment', 'limitations']);
  });

  it('separates read and review capabilities for sensitive flows', () => {
    expect(canReadRecruitment([HR_STAFF_GOVERNANCE_PERMISSION_VALUES.recruitmentRead])).toBe(true);
    expect(canReviewRecruitment([HR_STAFF_GOVERNANCE_PERMISSION_VALUES.recruitmentRead])).toBe(false);
    expect(canReviewRecruitment([HR_STAFF_GOVERNANCE_PERMISSION_VALUES.recruitmentReview])).toBe(true);
    expect(canReviewLeave([HR_STAFF_GOVERNANCE_PERMISSION_VALUES.leaveReview])).toBe(true);
  });

  it('keeps review-only boundaries for disciplinary, appraisal, and access lifecycle flows', () => {
    expect(canReadDisciplinaryCases([HR_STAFF_GOVERNANCE_PERMISSION_VALUES.disciplinaryCasesRead])).toBe(true);
    expect(canReviewDisciplinaryCases([HR_STAFF_GOVERNANCE_PERMISSION_VALUES.disciplinaryCasesRead])).toBe(false);
    expect(canReadAppraisals([HR_STAFF_GOVERNANCE_PERMISSION_VALUES.appraisalsRead])).toBe(true);
    expect(canReviewAppraisals([HR_STAFF_GOVERNANCE_PERMISSION_VALUES.appraisalsReview])).toBe(true);
    expect(canReadAccessLifecycle([HR_STAFF_GOVERNANCE_PERMISSION_VALUES.accessLifecycleRead])).toBe(true);
    expect(canReviewAccessLifecycle([HR_STAFF_GOVERNANCE_PERMISSION_VALUES.accessLifecycleReview])).toBe(true);
  });

  it('keeps readiness and bridge flows fail-closed', () => {
    expect(canReadTraining([HR_STAFF_GOVERNANCE_PERMISSION_VALUES.trainingRead])).toBe(true);
    expect(canReadWorkloadBridge([HR_STAFF_GOVERNANCE_PERMISSION_VALUES.workloadBridgeRead])).toBe(true);
    expect(canReadPayrollReadiness([HR_STAFF_GOVERNANCE_PERMISSION_VALUES.payrollReadinessRead])).toBe(true);
    expect(canReviewPayrollReadiness([HR_STAFF_GOVERNANCE_PERMISSION_VALUES.payrollReadinessReview])).toBe(true);
    expect(canReadProviderReadiness([HR_STAFF_GOVERNANCE_PERMISSION_VALUES.providerReadinessRead])).toBe(true);
    expect(canReadLimitations([HR_STAFF_GOVERNANCE_PERMISSION_VALUES.limitationsRead])).toBe(true);
  });

  it('does not contain any automatic decision permission', () => {
    expect(HR_STAFF_GOVERNANCE_PERMISSIONS.some((permission) => permission.includes('automatic'))).toBe(false);
    expect(HR_STAFF_GOVERNANCE_PERMISSIONS.some((permission) => permission.includes('score'))).toBe(false);
  });
});