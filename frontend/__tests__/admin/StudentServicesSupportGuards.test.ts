import { describe, expect, it } from 'vitest';
import {
  STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES,
  STUDENT_SERVICES_SUPPORT_ROUTES,
} from '@/modules/student_services_support/constants';
import {
  getAllowedStudentServicesSupportRoutes,
  hasAnyStudentServicesSupportPermission,
  hasStudentServicesSupportPermission,
} from '@/modules/student_services_support/guards';

describe('Student Services Support guards', () => {
  it('grants exact permission checks', () => {
    const permissions = [
      STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.read,
      STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.dashboardRead,
    ];

    expect(hasStudentServicesSupportPermission(permissions, STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.read)).toBe(true);
    expect(hasStudentServicesSupportPermission(permissions, STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.write)).toBe(false);
  });

  it('returns only allowed routes for read + dashboard permission set', () => {
    const permissions = [
      STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.read,
      STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.dashboardRead,
    ];

    const allowed = getAllowedStudentServicesSupportRoutes(permissions);
    const allowedKeys = allowed.map((route) => route.key);

    expect(allowedKeys).toContain('overview');
    expect(allowedKeys).toContain('requests');
    expect(allowedKeys).toContain('request-detail');
    expect(allowedKeys).toContain('cases');
    expect(allowedKeys).toContain('case-detail');
    expect(allowedKeys).toContain('dashboard');
    expect(allowedKeys).not.toContain('hardship');
    expect(allowedKeys).not.toContain('accommodations');
    expect(allowedKeys).not.toContain('complaints');
    expect(allowedKeys).not.toContain('escalations');
  });

  it('supports hasAny checks', () => {
    const permissions = [STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.assign];
    expect(hasAnyStudentServicesSupportPermission(permissions, [STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.assign, STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.escalate])).toBe(true);
    expect(hasAnyStudentServicesSupportPermission(permissions, [STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.read, STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.dashboardRead])).toBe(false);
  });

  it('keeps route permission map in sync with route inventory', () => {
    expect(STUDENT_SERVICES_SUPPORT_ROUTES).toHaveLength(10);
  });
});
