import { describe, expect, it } from 'vitest';
import {
  HR_STAFF_GOVERNANCE_API_BASE,
  HR_STAFF_GOVERNANCE_BACKEND_ROUTE_COUNT,
  HR_STAFF_GOVERNANCE_DATA_SOURCE,
  HR_STAFF_GOVERNANCE_PERMISSION_COUNT,
  HR_STAFF_GOVERNANCE_PROVIDER_PROFILES,
  HR_STAFF_GOVERNANCE_ROUTE_COUNT,
  HR_STAFF_GOVERNANCE_ROUTE_FAMILY,
  HR_STAFF_GOVERNANCE_ROUTES,
  HR_STAFF_GOVERNANCE_RUNTIME_MODE,
  HR_STAFF_GOVERNANCE_SAFETY_FLAGS,
  HR_STAFF_GOVERNANCE_SOURCE_SPEC_COMMIT,
  HR_STAFF_GOVERNANCE_WORKFLOWS,
  HR_STAFF_GOVERNANCE_DASHBOARD_WIDGETS,
} from '@/modules/hr-staff-governance/constants';
import type {
  HrDashboardSummary,
  HrFoundationSummary,
  HrSafetyFlags,
  HrStaffProfile,
} from '@/modules/hr-staff-governance/types';

describe('HR Staff Governance types', () => {
  it('exports the expected module constants', () => {
    expect(HR_STAFF_GOVERNANCE_API_BASE).toBe('/api/admin/hr-staff-governance');
    expect(HR_STAFF_GOVERNANCE_ROUTE_FAMILY).toBe('/console/hr-staff-governance');
    expect(HR_STAFF_GOVERNANCE_ROUTE_COUNT).toBe(20);
    expect(HR_STAFF_GOVERNANCE_BACKEND_ROUTE_COUNT).toBe(62);
    expect(HR_STAFF_GOVERNANCE_PERMISSION_COUNT).toBe(56);
    expect(HR_STAFF_GOVERNANCE_RUNTIME_MODE).toBe('METADATA_EVIDENCE_HUMAN_REVIEW_ONLY');
    expect(HR_STAFF_GOVERNANCE_SOURCE_SPEC_COMMIT).toBe('4fa0ff0');
    expect(HR_STAFF_GOVERNANCE_DATA_SOURCE).toBe('computed_from_hr_staff_governance_metadata');
  });

  it('keeps the full 20-route contract explicit', () => {
    expect(HR_STAFF_GOVERNANCE_ROUTES).toHaveLength(20);
    expect(HR_STAFF_GOVERNANCE_ROUTES[0]?.path).toBe('/console/hr-staff-governance');
    expect(HR_STAFF_GOVERNANCE_ROUTES[1]?.path).toBe('/console/hr-staff-governance/dashboard');
    expect(HR_STAFF_GOVERNANCE_ROUTES.at(-1)?.path).toBe('/console/hr-staff-governance/limitations');
  });

  it('defines the expected dashboard widgets and workflows', () => {
    expect(HR_STAFF_GOVERNANCE_DASHBOARD_WIDGETS).toHaveLength(12);
    expect(HR_STAFF_GOVERNANCE_WORKFLOWS).toHaveLength(12);
  });

  it('defines the expected deferred provider profiles', () => {
    expect(HR_STAFF_GOVERNANCE_PROVIDER_PROFILES.map((profile) => profile.key)).toEqual([
      'ONE_C_KZ',
      'HR_PAYROLL_PROVIDER',
      'IDP_SSO_KZ',
      'EDS_KZ',
      'EGOV_LABOR_REGISTRY',
    ]);
  });

  it('models safety flags explicitly', () => {
    const flags: HrSafetyFlags = {
      fake_metrics: false,
      fake_hr_data: false,
      provider_connected: false,
      live_provider_sync: false,
      payroll_execution_enabled: false,
      automatic_decision_enabled: false,
      hidden_score_present: false,
      human_review_required: true,
      incomplete_data: true,
      limitations: ['Metadata/evidence-only HR foundation'],
    };

    expect(flags.fake_metrics).toBe(false);
    expect(flags.fake_hr_data).toBe(false);
    expect(flags.hidden_score_present).toBe(false);
  });

  it('models summary and dashboard trust fields', () => {
    const summary: HrFoundationSummary = {
      ...HR_STAFF_GOVERNANCE_SAFETY_FLAGS,
      tenant_id: 1,
      module: 'hr-staff-governance',
      product_vertical: 'HR / Staff Governance Suite',
      contract_version: 'A-039.3',
      runtime_mode: HR_STAFF_GOVERNANCE_RUNTIME_MODE,
      table_count: 36,
      route_count: 62,
      permission_count: 56,
      detailed_capability_count: 54,
      capability_family_count: 14,
      workflow_group_count: 12,
      role_count: 15,
      data_source: HR_STAFF_GOVERNANCE_DATA_SOURCE,
      boundary_summary: { fake_metrics: false },
    };

    const dashboard: HrDashboardSummary = {
      ...HR_STAFF_GOVERNANCE_SAFETY_FLAGS,
      tenant_id: 1,
      generated_at: '2026-05-26T00:00:00Z',
      contract_version: 'A-039.3',
      source_spec_commit: '4fa0ff0',
      source_backend_baseline_commit: 'c72e6c0',
      data_source: HR_STAFF_GOVERNANCE_DATA_SOURCE,
      staff_lifecycle_summary: { active: 12 },
      recruitment_summary: { pending: 3 },
      onboarding_summary: { active: 2 },
      employee_record_summary: { complete: 10 },
      leave_summary: { review: 4 },
      training_summary: { expiring: 5 },
      disciplinary_summary: { review: 1 },
      offboarding_summary: { active: 2 },
      workload_bridge_summary: { academic_operations: 2 },
      payroll_readiness_summary: { deferred: 1 },
      provider_readiness_summary: { deferred: 5 },
      boundary_summary: { fake_metrics: false },
    };

    expect(summary.permission_count).toBe(56);
    expect(dashboard.data_source).toBe(HR_STAFF_GOVERNANCE_DATA_SOURCE);
  });

  it('models entity metadata without hidden scoring', () => {
    const staffProfile: HrStaffProfile = {
      ...HR_STAFF_GOVERNANCE_SAFETY_FLAGS,
      id: 1,
      tenant_id: 1,
      status: 'ACTIVE',
      title: 'Faculty Advisor Profile',
      description: null,
      notes: null,
      metadata: {},
      department_ref: 'HR-ACADEMIC',
      faculty_ref: 'FAC-01',
      read_only_first: true,
      mutation_allowed: false,
    };

    expect(staffProfile.mutation_allowed).toBe(false);
    expect(staffProfile.hidden_score_present).toBe(false);
  });
});