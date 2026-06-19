import { describe, expect, it } from 'vitest';
import {
  STUDENT_SERVICES_SUPPORT_BACKEND_ROUTE_COUNT,
  STUDENT_SERVICES_SUPPORT_PERMISSION_COUNT,
  STUDENT_SERVICES_SUPPORT_PLANNED_ROUTE_COUNT,
  STUDENT_SERVICES_SUPPORT_ROUTES,
  STUDENT_SERVICES_SUPPORT_SAFETY_FLAGS,
} from '@/modules/student_services_support/constants';

describe('Student Services Support types and constants', () => {
  it('keeps planned route count fixed at 10', () => {
    expect(STUDENT_SERVICES_SUPPORT_PLANNED_ROUTE_COUNT).toBe(10);
    expect(STUDENT_SERVICES_SUPPORT_BACKEND_ROUTE_COUNT).toBe(21);
    expect(STUDENT_SERVICES_SUPPORT_ROUTES).toHaveLength(10);
  });

  it('keeps permission inventory fixed at 6', () => {
    expect(STUDENT_SERVICES_SUPPORT_PERMISSION_COUNT).toBe(6);
  });

  it('keeps fail-closed safety flags explicit', () => {
    expect(STUDENT_SERVICES_SUPPORT_SAFETY_FLAGS.fake_metrics).toBe(false);
    expect(STUDENT_SERVICES_SUPPORT_SAFETY_FLAGS.provider_live_enabled).toBe(false);
    expect(STUDENT_SERVICES_SUPPORT_SAFETY_FLAGS.autonomous_decision_enabled).toBe(false);
    expect(STUDENT_SERVICES_SUPPORT_SAFETY_FLAGS.hidden_score_present).toBe(false);
    expect(STUDENT_SERVICES_SUPPORT_SAFETY_FLAGS.human_review_required).toBe(true);
  });
});
