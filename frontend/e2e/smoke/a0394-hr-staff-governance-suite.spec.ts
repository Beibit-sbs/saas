import { expect, test, type Browser, type Page, type Route } from '@playwright/test';

const API_BASE = '/api/admin/hr-staff-governance';
const BFF_BASE = '/api/bff/admin/hr-staff-governance';
const BASE_URL = process.env.E2E_BASE_URL ?? 'https://nginx';

const FULL_PERMISSIONS = [
  'platform.admin.read',
  'hr_staff_governance.overview.read',
  'hr_staff_governance.dashboard.read',
  'hr_staff_governance.health.read',
  'hr_staff_governance.limitations.read',
  'hr_staff_governance.audit.read',
  'hr_staff_governance.staff_profiles.read',
  'hr_staff_governance.staff_profiles.create',
  'hr_staff_governance.staff_profiles.update',
  'hr_staff_governance.employee_records.read',
  'hr_staff_governance.employee_records.create',
  'hr_staff_governance.employee_records.update',
  'hr_staff_governance.faculty_profiles.read',
  'hr_staff_governance.faculty_profiles.update',
  'hr_staff_governance.recruitment.read',
  'hr_staff_governance.recruitment.create',
  'hr_staff_governance.recruitment.review',
  'hr_staff_governance.hiring_evidence.read',
  'hr_staff_governance.hiring_evidence.create',
  'hr_staff_governance.onboarding.read',
  'hr_staff_governance.onboarding.create',
  'hr_staff_governance.onboarding.update',
  'hr_staff_governance.probation.read',
  'hr_staff_governance.probation.review',
  'hr_staff_governance.leave.read',
  'hr_staff_governance.leave.create',
  'hr_staff_governance.leave.review',
  'hr_staff_governance.attendance.read',
  'hr_staff_governance.staff_requests.read',
  'hr_staff_governance.staff_requests.create',
  'hr_staff_governance.staff_requests.review',
  'hr_staff_governance.staff_appeals.read',
  'hr_staff_governance.staff_appeals.create',
  'hr_staff_governance.staff_appeals.review',
  'hr_staff_governance.policy_exceptions.read',
  'hr_staff_governance.policy_exceptions.create',
  'hr_staff_governance.policy_exceptions.review',
  'hr_staff_governance.appraisals.read',
  'hr_staff_governance.appraisals.create',
  'hr_staff_governance.appraisals.review',
  'hr_staff_governance.training.read',
  'hr_staff_governance.training.create',
  'hr_staff_governance.training.update',
  'hr_staff_governance.disciplinary_cases.read',
  'hr_staff_governance.disciplinary_cases.create',
  'hr_staff_governance.disciplinary_cases.review',
  'hr_staff_governance.disciplinary_evidence.read',
  'hr_staff_governance.disciplinary_evidence.create',
  'hr_staff_governance.offboarding.read',
  'hr_staff_governance.offboarding.create',
  'hr_staff_governance.offboarding.update',
  'hr_staff_governance.access_lifecycle.read',
  'hr_staff_governance.access_lifecycle.review',
  'hr_staff_governance.workload_bridge.read',
  'hr_staff_governance.payroll_readiness.read',
  'hr_staff_governance.payroll_readiness.review',
  'hr_staff_governance.provider_readiness.read',
] as const;

const REQUIRED_BOUNDARY_LABELS = [
  'Metadata/evidence-only HR foundation',
  'Human review required',
  'No automatic hiring/firing',
  'No automatic disciplinary decision',
  'No automatic leave approval/rejection',
  'No payroll execution',
  'No provider live sync',
  'No hidden employee/faculty score',
  'No production-ready claim',
  'No sales-ready claim',
  'No GCC-ready claim',
  'Incomplete data supported',
  'Provider readiness only',
  'Payroll readiness only',
  'Access lifecycle review only',
  'Bridge-first / read-only-first',
  'fakeMetrics=false',
  'fakeHrData=false',
] as const;

const FORBIDDEN_DOM_LABELS = [
  'Auto hire',
  'Auto fire',
  'Auto approve leave',
  'Auto reject leave',
  'Auto discipline',
  'Execute payroll',
  'Sync 1C now',
  'Connect provider live',
  'Publish employee score',
  'Hidden faculty score',
  'Hidden employee score',
  'Production ready',
  'Sales ready',
  'GCC ready',
  'L5/L6 ready',
  'Official HR decision',
  'Automatic dismissal',
  'Automatic sanction',
  'Payroll sent',
  'Provider connected live',
  '1C synced',
  'Real employee record',
  'Real payroll data',
  'Real performance score',
] as const;

const FORBIDDEN_EXACT_TEXTS = [
  /^Production ready$/i,
  /^Sales ready$/i,
  /^GCC ready$/i,
  /^L5\/L6 ready$/i,
  /^Official HR decision$/i,
  /^Automatic dismissal$/i,
  /^Automatic sanction$/i,
  /^Payroll sent$/i,
  /^Provider connected live$/i,
  /^1C synced$/i,
  /^Real employee record$/i,
  /^Real payroll data$/i,
  /^Real performance score$/i,
] as const;

const BASE_FLAGS = {
  fake_metrics: false,
  fake_hr_data: false,
  provider_connected: false,
  live_provider_sync: false,
  payroll_execution_enabled: false,
  automatic_decision_enabled: false,
  hidden_score_present: false,
  human_review_required: true,
  incomplete_data: true,
  limitations: [
    'Metadata/evidence/human-review-only HR runtime.',
    'No provider live sync, payroll execution, or hidden score surfaces are implemented.',
  ],
  created_at: '2026-05-26T00:00:00Z',
  updated_at: '2026-05-26T00:00:00Z',
} as const;

function makeRecord(id: number, recordKey: string, title: string, description: string, extra: Record<string, unknown> = {}) {
  return {
    id,
    tenant_id: 1,
    title,
    description,
    status: 'ACTIVE',
    review_mode: 'HUMAN_REVIEW_ONLY',
    metadata_only: true,
    mutation_allowed: false,
    no_real_hr_data: true,
    no_real_payroll_data: true,
    no_hidden_score: true,
    ...BASE_FLAGS,
    ...extra,
    record_key: recordKey,
  };
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

const hrOverviewFixture = {
  tenant_id: 1,
  module: 'hr_staff_governance',
  product_vertical: 'HR / Staff Governance Suite',
  contract_version: 'A-039.4-E2E',
  route_count: 20,
  scenario_group_count: 21,
  runtime_mode: 'METADATA_EVIDENCE_HUMAN_REVIEW_ONLY',
  data_source: 'computed_from_hr_staff_governance_metadata',
  ...BASE_FLAGS,
};

const hrDashboardFixture = {
  tenant_id: 1,
  module: 'hr_staff_governance',
  generated_at: '2026-05-26T00:00:00Z',
  contract_version: 'A-039.4-E2E',
  route_count: 20,
  widget_count: 12,
  data_source: 'computed_from_hr_staff_governance_metadata',
  ...BASE_FLAGS,
};

const hrReadinessFixture = {
  tenant_id: 1,
  module: 'hr_staff_governance',
  provider_readiness_only: true,
  payroll_readiness_only: true,
  bridge_first_read_only_first: true,
  ...BASE_FLAGS,
};

const hrLimitationsFixture = {
  items: [
    'No fake HR data or fake payroll data is generated in this runtime.',
    'No provider live sync or payroll execution is implemented.',
    'No automatic hiring/firing, disciplinary decision, or leave approval/rejection is implemented.',
    'No hidden employee/faculty score or production/sales/GCC/L5/L6 claim is implemented.',
  ],
};

const hrRecruitmentFixture = {
  items: [
    makeRecord(1, 'REQ-HR-001', 'Recruitment request metadata', 'Hiring readiness metadata only.', {
      workflow_state: 'REVIEW_PENDING',
      committee_review_required: true,
      automatic_decision_enabled: false,
    }),
  ],
};

const hrOnboardingFixture = {
  items: [
    makeRecord(2, 'ONB-HR-001', 'Onboarding checklist metadata', 'Checklist and probation metadata only.', {
      probation_review_required: true,
      incomplete_data: true,
    }),
  ],
};

const hrEmployeeRecordFixture = {
  items: [
    makeRecord(3, 'EMP-META-001', 'Employee record metadata', 'Tenant-scoped employee record metadata only.', {
      hidden_score_present: false,
      profile_status: 'INCOMPLETE_METADATA',
    }),
  ],
};

const hrStaffProfileFixture = {
  items: [
    makeRecord(4, 'STAFF-PROFILE-001', 'Staff profile metadata', 'Staff profile and evidence links only.', {
      linked_employee_record_key: 'EMP-META-001',
      evidence_count: 2,
    }),
  ],
};

const hrLeaveFixture = {
  items: [
    makeRecord(5, 'LEAVE-001', 'Leave request metadata', 'Leave review metadata only.', {
      review_status: 'PENDING_HUMAN_REVIEW',
      automatic_decision_enabled: false,
    }),
  ],
};

const hrAppraisalFixture = {
  items: [
    makeRecord(6, 'APPRAISAL-001', 'Appraisal metadata', 'Performance review metadata without hidden scores.', {
      hidden_score_present: false,
      score_published: false,
    }),
  ],
};

const hrTrainingFixture = {
  items: [
    makeRecord(7, 'TRAINING-001', 'Training certification metadata', 'Expiry and compliance evidence metadata only.', {
      compliance_state: 'REVIEW_REQUIRED',
      incomplete_data: true,
    }),
  ],
};

const hrRequestAppealFixture = {
  requests: [
    makeRecord(8, 'REQUEST-001', 'Staff request metadata', 'Staff request metadata routed into human review.', {
      review_status: 'OPEN',
    }),
  ],
  appeals: [
    makeRecord(9, 'APPEAL-001', 'Staff appeal metadata', 'Appeal metadata with review-only workflow.', {
      review_status: 'UNDER_REVIEW',
    }),
  ],
};

const hrPolicyExceptionFixture = {
  items: [
    makeRecord(10, 'POLICY-EX-001', 'Policy exception metadata', 'Policy exception review evidence only.', {
      approval_mode: 'HUMAN_REVIEW_ONLY',
    }),
  ],
};

const hrDisciplinaryFixture = {
  cases: [
    makeRecord(11, 'DISC-001', 'Disciplinary metadata', 'Disciplinary case metadata without automatic outcomes.', {
      automatic_decision_enabled: false,
      sanction_decision: 'DEFERRED_TO_HUMAN_REVIEW',
    }),
  ],
  evidence: [
    makeRecord(12, 'DISC-EVIDENCE-001', 'Disciplinary evidence metadata', 'Evidence metadata for disciplinary review only.'),
  ],
};

const hrOffboardingFixture = {
  items: [
    makeRecord(13, 'OFFBOARD-001', 'Offboarding metadata', 'Offboarding metadata coordinated with access lifecycle review.', {
      access_revocation_mode: 'REVIEW_ONLY',
      payroll_execution_enabled: false,
    }),
  ],
};

const hrAccessLifecycleFixture = {
  items: [
    makeRecord(14, 'ACCESS-001', 'Access lifecycle review metadata', 'Access lifecycle review with no autonomous revocation.', {
      autonomous_access_revocation: false,
      bridge_target: 'IAM_ACCESS',
    }),
  ],
};

const hrWorkloadBridgeFixture = {
  items: [
    makeRecord(15, 'WORKLOAD-001', 'Workload bridge metadata', 'Read-only academic workload bridge metadata.', {
      bridge_target: 'ACADEMIC_OPERATIONS',
      read_only_first: true,
    }),
  ],
};

const hrPayrollReadinessFixture = {
  items: [
    makeRecord(16, 'PAYROLL-001', 'Payroll readiness metadata', 'Payroll readiness metadata only.', {
      payroll_execution_enabled: false,
      provider_connected: false,
    }),
  ],
};

const hrProviderReadinessFixture = {
  items: [
    makeRecord(17, 'PROVIDER-001', 'Provider readiness metadata', 'Provider readiness evidence only.', {
      provider_connected: false,
      live_provider_sync: false,
      credentials_present: false,
    }),
  ],
};

const hrBrainSignalsFixture = {
  items: [
    makeRecord(18, 'BRAIN-001', 'HR brain signal metadata', 'Read-only metadata signal for HR governance visibility.', {
      severity: 'INFO',
      automatic_decision_enabled: false,
    }),
  ],
};

const fullAccessHrAdminFixture = {
  sub: 'hr-staff-governance-admin',
  displayName: 'HR Staff Governance E2E Admin',
  roles: ['admin'],
  permissions: FULL_PERMISSIONS,
  tenantId: 1,
} as const;

const restrictedUserFixture = {
  sub: 'hr-staff-governance-restricted',
  displayName: 'HR Staff Governance Restricted User',
  roles: ['admin'],
  permissions: ['platform.admin.read'],
  tenantId: 1,
} as const;

const HR_ROUTES = [
  {
    key: 'overview',
    path: '/console/hr-staff-governance',
    title: 'HR / Staff Governance Suite',
    boundary: 'Metadata/evidence-only HR foundation',
    permission: 'hr_staff_governance.overview.read',
    assertRoute: async (page: Page) => {
      await expect(page.getByTestId('hr-page-overview')).toContainText('Operational overview of the HR metadata and safety boundary baseline.');
      await expect(page.getByTestId('hr-readiness-runtime-baseline')).toContainText('Backend route count used: 62');
      await expect(page.getByTestId('hr-no-overclaim-footer')).toContainText('No provider live sync UI.');
    },
  },
  {
    key: 'dashboard',
    path: '/console/hr-staff-governance/dashboard',
    title: 'HR Operations Dashboard',
    boundary: 'fakeMetrics=false',
    permission: 'hr_staff_governance.dashboard.read',
    assertRoute: async (page: Page) => {
      await expect(page.getByTestId('hr-page-dashboard')).toContainText('Dashboard visibility across recruitment, onboarding, leave, training, discipline, offboarding, and readiness.');
      await expect(page.getByTestId('hr-dashboard-grid')).toContainText('Recruitment Readiness');
      await expect(page.getByTestId('hr-metric-fakemetrics')).toContainText('false');
    },
  },
  {
    key: 'recruitment',
    path: '/console/hr-staff-governance/recruitment',
    title: 'Recruitment / Hiring Readiness',
    boundary: 'No automatic hiring/firing',
    permission: 'hr_staff_governance.recruitment.read',
    assertRoute: async (page: Page) => {
      await expect(page.getByTestId('hr-page-recruitment')).toContainText('Metadata and evidence-only recruitment review surface.');
      await expect(page.getByTestId('hr-evidence-table')).toContainText('GET /api/admin/hr-staff-governance/recruitment-requests');
      await expect(page.getByTestId('hr-boundary-no-automatic-hiring-firing')).toBeVisible();
    },
  },
  {
    key: 'onboarding',
    path: '/console/hr-staff-governance/onboarding',
    title: 'Staff Onboarding',
    boundary: 'Human review required',
    permission: 'hr_staff_governance.onboarding.read',
    assertRoute: async (page: Page) => {
      await expect(page.getByTestId('hr-page-onboarding')).toContainText('Onboarding checklist and probation metadata managed under human review.');
      await expect(page.getByTestId('hr-form-shell-staff-onboarding-surface')).toContainText('review-only');
    },
  },
  {
    key: 'employee-records',
    path: '/console/hr-staff-governance/employee-records',
    title: 'Employee Records',
    boundary: 'No hidden employee/faculty score',
    permission: 'hr_staff_governance.employee_records.read',
    assertRoute: async (page: Page) => {
      await expect(page.getByTestId('hr-page-employee-records')).toContainText('Tenant-scoped employee record metadata without hidden scoring.');
      await expect(page.getByTestId('hr-boundary-no-hidden-employee-faculty-score')).toBeVisible();
    },
  },
  {
    key: 'staff-profiles',
    path: '/console/hr-staff-governance/staff-profiles',
    title: 'Staff Profiles',
    boundary: 'Metadata/evidence-only HR foundation',
    permission: 'hr_staff_governance.staff_profiles.read',
    assertRoute: async (page: Page) => {
      await expect(page.getByTestId('hr-page-staff-profiles')).toContainText('Core staff profile metadata and evidence links.');
      await expect(page.getByTestId('hr-evidence-table')).toContainText('GET /api/admin/hr-staff-governance/staff-profiles');
    },
  },
  {
    key: 'faculty-profile',
    path: '/console/hr-staff-governance/faculty-profile',
    title: 'Faculty Profile / Academic Staff Portfolio',
    boundary: 'Bridge-first / read-only-first',
    permission: 'hr_staff_governance.faculty_profiles.read',
    assertRoute: async (page: Page) => {
      await expect(page.getByTestId('hr-page-faculty-profile')).toContainText('Read-only faculty portfolio context bridged from HR and academic operations.');
      await expect(page.getByTestId('hr-bridge-one-c-kz')).toBeVisible();
    },
  },
  {
    key: 'leave',
    path: '/console/hr-staff-governance/leave',
    title: 'Leave / Absence Review',
    boundary: 'No automatic leave approval/rejection',
    permission: 'hr_staff_governance.leave.read',
    assertRoute: async (page: Page) => {
      await expect(page.getByTestId('hr-page-leave')).toContainText('Leave metadata and human review outcomes only.');
      await expect(page.getByTestId('hr-boundary-no-automatic-leave-approval-rejection')).toBeVisible();
    },
  },
  {
    key: 'performance',
    path: '/console/hr-staff-governance/performance',
    title: 'Performance Appraisal Metadata',
    boundary: 'No hidden employee/faculty score',
    permission: 'hr_staff_governance.appraisals.read',
    assertRoute: async (page: Page) => {
      await expect(page.getByTestId('hr-page-performance')).toContainText('Performance cycle and review metadata without hidden employee scores.');
      await expect(page.getByTestId('hr-boundary-no-hidden-employee-faculty-score')).toBeVisible();
    },
  },
  {
    key: 'training',
    path: '/console/hr-staff-governance/training',
    title: 'Training / Certification Compliance',
    boundary: 'Incomplete data supported',
    permission: 'hr_staff_governance.training.read',
    assertRoute: async (page: Page) => {
      await expect(page.getByTestId('hr-page-training')).toContainText('Certification compliance evidence and expiry metadata.');
      await expect(page.getByTestId('hr-boundary-incomplete-data-supported')).toBeVisible();
    },
  },
  {
    key: 'requests',
    path: '/console/hr-staff-governance/requests',
    title: 'Staff Requests',
    boundary: 'Human review required',
    permission: 'hr_staff_governance.staff_requests.read',
    assertRoute: async (page: Page) => {
      await expect(page.getByTestId('hr-page-requests')).toContainText('Staff request metadata routed into human review.');
      await expect(page.getByTestId('hr-human-review-badge').first()).toBeVisible();
    },
  },
  {
    key: 'appeals',
    path: '/console/hr-staff-governance/appeals',
    title: 'Staff Appeals',
    boundary: 'Human review required',
    permission: 'hr_staff_governance.staff_appeals.read',
    assertRoute: async (page: Page) => {
      await expect(page.getByTestId('hr-page-appeals')).toContainText('Appeal metadata with review-only actions.');
      await expect(page.getByTestId('hr-human-review-badge').first()).toBeVisible();
    },
  },
  {
    key: 'policy-exceptions',
    path: '/console/hr-staff-governance/policy-exceptions',
    title: 'HR Policy Exceptions',
    boundary: 'Human review required',
    permission: 'hr_staff_governance.policy_exceptions.read',
    assertRoute: async (page: Page) => {
      await expect(page.getByTestId('hr-page-policy-exceptions')).toContainText('Policy exception tracking and review evidence only.');
      await expect(page.getByTestId('hr-review-panel-human-review-boundary')).toContainText('Sensitive actions require explicit review permission.');
    },
  },
  {
    key: 'disciplinary',
    path: '/console/hr-staff-governance/disciplinary',
    title: 'Disciplinary Case Governance',
    boundary: 'No automatic disciplinary decision',
    permission: 'hr_staff_governance.disciplinary_cases.read',
    assertRoute: async (page: Page) => {
      await expect(page.getByTestId('hr-page-disciplinary')).toContainText('Disciplinary case metadata and evidence without automatic outcomes.');
      await expect(page.getByTestId('hr-boundary-no-automatic-disciplinary-decision')).toBeVisible();
    },
  },
  {
    key: 'offboarding',
    path: '/console/hr-staff-governance/offboarding',
    title: 'Exit / Offboarding',
    boundary: 'Access lifecycle review only',
    permission: 'hr_staff_governance.offboarding.read',
    assertRoute: async (page: Page) => {
      await expect(page.getByTestId('hr-page-offboarding')).toContainText('Offboarding metadata coordinated with access review and payroll readiness.');
      await expect(page.getByTestId('hr-boundary-access-lifecycle-review-only')).toBeVisible();
    },
  },
  {
    key: 'access-lifecycle',
    path: '/console/hr-staff-governance/access-lifecycle',
    title: 'Access Lifecycle Review',
    boundary: 'Access lifecycle review only',
    permission: 'hr_staff_governance.access_lifecycle.read',
    assertRoute: async (page: Page) => {
      await expect(page.getByTestId('hr-page-access-lifecycle')).toContainText('Access lifecycle review metadata with no autonomous revocation.');
      await expect(page.getByTestId('hr-boundary-bridge-first-read-only-first')).toBeVisible();
    },
  },
  {
    key: 'workload-bridge',
    path: '/console/hr-staff-governance/workload-bridge',
    title: 'Teaching Load / Workload Bridge',
    boundary: 'Bridge-first / read-only-first',
    permission: 'hr_staff_governance.workload_bridge.read',
    assertRoute: async (page: Page) => {
      await expect(page.getByTestId('hr-page-workload-bridge')).toContainText('Read-only-first bridge into academic operations workload context.');
      await expect(page.getByTestId('hr-boundary-bridge-first-read-only-first')).toBeVisible();
    },
  },
  {
    key: 'payroll-readiness',
    path: '/console/hr-staff-governance/payroll-readiness',
    title: 'Payroll / 1C Readiness',
    boundary: 'No payroll execution',
    permission: 'hr_staff_governance.payroll_readiness.read',
    assertRoute: async (page: Page) => {
      await expect(page.getByTestId('hr-page-payroll-readiness')).toContainText('Payroll readiness metadata only with no payroll execution UI.');
      await expect(page.getByTestId('hr-payroll-readiness-badge')).toContainText('payrollExecutionEnabled=false');
    },
  },
  {
    key: 'provider-readiness',
    path: '/console/hr-staff-governance/provider-readiness',
    title: 'Provider Readiness',
    boundary: 'No provider live sync',
    permission: 'hr_staff_governance.provider_readiness.read',
    assertRoute: async (page: Page) => {
      await expect(page.getByTestId('hr-page-provider-readiness')).toContainText('Provider readiness evidence with providerConnected=false and liveProviderSync=false.');
      await expect(page.getByTestId('hr-provider-deferred-badge')).toContainText('providerConnected=false / liveProviderSync=false');
    },
  },
  {
    key: 'limitations',
    path: '/console/hr-staff-governance/limitations',
    title: 'Limitations / Safety Boundaries',
    boundary: 'No production-ready claim',
    permission: 'hr_staff_governance.limitations.read',
    assertRoute: async (page: Page) => {
      await expect(page.getByTestId('hr-page-limitations')).toContainText('Explicit limitations, no-overclaim boundaries, and safety assertions for the HR frontend runtime.');
      await expectRequiredBoundaryLabels(page);
      await expect(page.getByTestId('hr-limitations-panel')).toContainText('No provider live sync, payroll execution, or hidden score surfaces are implemented.');
    },
  },
] as const;

const ROUTE_TITLE_GROUPS = [
  { label: 'A', routes: HR_ROUTES.slice(0, 5) },
  { label: 'B', routes: HR_ROUTES.slice(5, 10) },
  { label: 'C', routes: HR_ROUTES.slice(10, 15) },
  { label: 'D', routes: HR_ROUTES.slice(15, 20) },
] as const;

if (HR_ROUTES.length !== 20) {
  throw new Error(`HR browser route flow must stay at 20, received ${HR_ROUTES.length}`);
}

function pageUrl(path: string) {
  return new URL(path, BASE_URL).toString();
}

async function forceEnglishLocale(page: Page) {
  const url = pageUrl('/');
  const parsedUrl = new URL(url);
  const cookieOrigins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);

  await page.context().addCookies(
    Array.from(cookieOrigins).map((origin) => ({
      name: 'app.locale',
      value: 'en',
      url: origin,
      httpOnly: false,
      secure: new URL(origin).protocol === 'https:',
      sameSite: 'Lax' as const,
    })),
  );

  await page.addInitScript(() => {
    document.cookie = 'app.locale=en; Path=/; SameSite=Lax';
    window.localStorage.setItem('app.language', 'en');
  });
}

async function stubSharedBootstrap(page: Page) {
  await page.route('**/api/auth/csrf*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ csrfToken: 'hr-staff-governance-csrf-token' }),
    });
  });

  await page.route('**/api/auth/me/preferences/language*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ ok: true, language: 'en' }),
    });
  });

  await page.route('**/api/public/tenants/login-directory*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            tenantId: 1,
            tenantCode: 'hr-staff-governance-demo',
            tenantName: 'HR Staff Governance Demo Tenant',
            authMethods: ['password'],
          },
        ],
      }),
    });
  });

  await page.route('**/api/i18n/languages*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        languages: [
          { code: 'en', label: 'English', default: true },
          { code: 'ru', label: 'Russian', default: false },
        ],
      }),
    });
  });
}

async function stubAuth(page: Page, userFixture: typeof fullAccessHrAdminFixture | typeof restrictedUserFixture) {
  const parsedUrl = new URL(BASE_URL);
  const cookieOrigins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);
  const payloadJson = JSON.stringify({
    sub: userFixture.sub,
    display_name: userFixture.displayName,
    roles: userFixture.roles,
    permissions: userFixture.permissions,
    tenant_id: userFixture.tenantId,
    exp: Math.floor(Date.now() / 1000) + 3600,
  });
  const payload = Buffer.from(payloadJson).toString('base64url');
  const fakeToken = `fakeheader.${payload}.fakesig`;

  await page.context().addCookies(
    Array.from(cookieOrigins).flatMap((origin) => {
      const secure = new URL(origin).protocol === 'https:';
      return [
        { name: 'admin_token', value: fakeToken, url: origin, httpOnly: true, secure, sameSite: 'Lax' as const },
        { name: 'app_access_token', value: fakeToken, url: origin, httpOnly: true, secure, sameSite: 'Lax' as const },
      ];
    }),
  );

  for (const pattern of ['**/api/auth/me*', '**/api/bff/auth/me*']) {
    await page.route(pattern, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: true,
          user: userFixture,
        }),
      });
    });
  }
}

function matchHrFixture(path: string) {
  if (path === `${API_BASE}/health` || path === `${BFF_BASE}/health`) return hrReadinessFixture;
  if (path === `${API_BASE}/overview` || path === `${BFF_BASE}/overview`) return hrOverviewFixture;
  if (path === `${API_BASE}/dashboard` || path === `${BFF_BASE}/dashboard`) return hrDashboardFixture;
  if (path === `${API_BASE}/safety-boundaries` || path === `${BFF_BASE}/safety-boundaries`) return { labels: REQUIRED_BOUNDARY_LABELS, flags: BASE_FLAGS };
  if (path === `${API_BASE}/readiness` || path === `${BFF_BASE}/readiness`) return hrReadinessFixture;
  if (path === `${API_BASE}/brain-signals` || path === `${BFF_BASE}/brain-signals`) return hrBrainSignalsFixture;
  if (path === `${API_BASE}/staff-profiles` || path === `${BFF_BASE}/staff-profiles`) return hrStaffProfileFixture;
  if (path === `${API_BASE}/employee-records` || path === `${BFF_BASE}/employee-records`) return hrEmployeeRecordFixture;
  if (path === `${API_BASE}/faculty-profiles` || path === `${BFF_BASE}/faculty-profiles`) return hrWorkloadBridgeFixture;
  if (path === `${API_BASE}/recruitment-requests` || path === `${BFF_BASE}/recruitment-requests`) return hrRecruitmentFixture;
  if (path === `${API_BASE}/hiring-evidence` || path === `${BFF_BASE}/hiring-evidence`) return hrRecruitmentFixture;
  if (path === `${API_BASE}/onboarding-cases` || path === `${BFF_BASE}/onboarding-cases`) return hrOnboardingFixture;
  if (path === `${API_BASE}/probation-reviews` || path === `${BFF_BASE}/probation-reviews`) return hrOnboardingFixture;
  if (path === `${API_BASE}/leave-requests` || path === `${BFF_BASE}/leave-requests`) return hrLeaveFixture;
  if (path === `${API_BASE}/attendance` || path === `${BFF_BASE}/attendance`) return hrReadinessFixture;
  if (path === `${API_BASE}/staff-requests` || path === `${BFF_BASE}/staff-requests`) return hrRequestAppealFixture.requests;
  if (path === `${API_BASE}/staff-appeals` || path === `${BFF_BASE}/staff-appeals`) return hrRequestAppealFixture.appeals;
  if (path === `${API_BASE}/policy-exceptions` || path === `${BFF_BASE}/policy-exceptions`) return hrPolicyExceptionFixture;
  if (path === `${API_BASE}/appraisals` || path === `${BFF_BASE}/appraisals`) return hrAppraisalFixture;
  if (path === `${API_BASE}/appraisal-reviews` || path === `${BFF_BASE}/appraisal-reviews`) return hrAppraisalFixture;
  if (path === `${API_BASE}/training-certifications` || path === `${BFF_BASE}/training-certifications`) return hrTrainingFixture;
  if (path === `${API_BASE}/disciplinary-cases` || path === `${BFF_BASE}/disciplinary-cases`) return hrDisciplinaryFixture.cases;
  if (path === `${API_BASE}/disciplinary-evidence` || path === `${BFF_BASE}/disciplinary-evidence`) return hrDisciplinaryFixture.evidence;
  if (path === `${API_BASE}/offboarding-cases` || path === `${BFF_BASE}/offboarding-cases`) return hrOffboardingFixture;
  if (path === `${API_BASE}/access-lifecycle-reviews` || path === `${BFF_BASE}/access-lifecycle-reviews`) return hrAccessLifecycleFixture;
  if (path === `${API_BASE}/workload-bridge-records` || path === `${BFF_BASE}/workload-bridge-records`) return hrWorkloadBridgeFixture;
  if (path === `${API_BASE}/payroll-readiness-profiles` || path === `${BFF_BASE}/payroll-readiness-profiles`) return hrPayrollReadinessFixture;
  if (path === `${API_BASE}/provider-readiness-evidence` || path === `${BFF_BASE}/provider-readiness-evidence`) return hrProviderReadinessFixture;
  if (path === `${API_BASE}/audit` || path === `${BFF_BASE}/audit`) return hrBrainSignalsFixture;
  if (path === `${API_BASE}/limitations` || path === `${BFF_BASE}/limitations`) return hrLimitationsFixture;
  if (path === `${API_BASE}/roles` || path === `${BFF_BASE}/roles`) return { items: [{ key: 'hr_admin', title: 'HR Admin', permissions: FULL_PERMISSIONS }] };
  if (path === `${API_BASE}/permissions` || path === `${BFF_BASE}/permissions`) return { items: FULL_PERMISSIONS };
  if (path === `${API_BASE}/metadata-contract` || path === `${BFF_BASE}/metadata-contract`) return hrOverviewFixture;
  if (path.endsWith('/workload-bridge/academic-operations/summary')) return hrWorkloadBridgeFixture;
  if (path.endsWith('/workload-bridge/finance-payroll/summary')) return hrPayrollReadinessFixture;
  if (path.endsWith('/workload-bridge/document-contracts/summary')) return hrProviderReadinessFixture;
  if (path.endsWith('/workload-bridge/iam-access/summary')) return hrAccessLifecycleFixture;
  return null;
}

async function stubHrApi(page: Page) {
  const fulfillHrRoute = async (route: Route) => {
    const request = route.request();
    const url = new URL(request.url());
    const payload = matchHrFixture(url.pathname);

    const ok = async (body: unknown, status = 200) => {
      await route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify(body),
      });
    };

    if (payload) {
      await ok(payload);
      return;
    }

    if (request.method() === 'POST' || request.method() === 'PATCH') {
      await ok({
        ok: true,
        mutation_applied: false,
        mode: 'metadata_review_only',
        ...BASE_FLAGS,
      });
      return;
    }

    await ok({ detail: `Unhandled HR Staff Governance stub path: ${url.pathname}` }, 404);
  };

  await page.route(`**${API_BASE}**`, fulfillHrRoute);
  await page.route(`**${BFF_BASE}**`, fulfillHrRoute);
}

async function setAuthenticatedHrAdmin(page: Page) {
  await forceEnglishLocale(page);
  await stubSharedBootstrap(page);
  await stubAuth(page, fullAccessHrAdminFixture);
  await stubHrApi(page);
}

async function setRestrictedHrUser(page: Page) {
  await forceEnglishLocale(page);
  await stubSharedBootstrap(page);
  await stubAuth(page, restrictedUserFixture);
  await stubHrApi(page);
}

async function gotoHrRoute(page: Page, path: string) {
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      await page.goto(pageUrl(path), { waitUntil: 'domcontentloaded' });
      return;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const isTransientNavigationFailure = /ERR_ABORTED|frame was detached/i.test(message);
      if (!isTransientNavigationFailure || attempt === 2) {
        throw error;
      }
    }
  }
}

async function expectRequiredBoundaryLabels(page: Page) {
  for (const label of REQUIRED_BOUNDARY_LABELS) {
    await expect(page.locator('body')).toContainText(label);
  }
}

async function expectForbiddenDomAbsent(page: Page) {
  for (const label of FORBIDDEN_DOM_LABELS) {
    const exactLabelPattern = new RegExp(`^${escapeRegExp(label)}$`, 'i');
    await expect(page.getByRole('button', { name: exactLabelPattern })).toHaveCount(0);
    await expect(page.getByRole('link', { name: exactLabelPattern })).toHaveCount(0);
    await expect(page.getByText(exactLabelPattern)).toHaveCount(0);
  }

  for (const pattern of FORBIDDEN_EXACT_TEXTS) {
    await expect(page.getByText(pattern)).toHaveCount(0);
  }

  await expect(page.locator('body')).not.toContainText(/provider connected live/i);
  await expect(page.locator('body')).not.toContainText(/real payroll data/i);
  await expect(page.locator('body')).not.toContainText(/real performance score/i);
  await expect(page.locator('body')).not.toContainText(/real employee record/i);
}

async function expectCommonRuntimeSafety(page: Page) {
  await expect(page.getByTestId('hr-safety-checklist')).toContainText('fakeMetrics=false');
  await expect(page.getByTestId('hr-safety-checklist')).toContainText('fakeHrData=false');
  await expect(page.getByTestId('hr-safety-checklist')).toContainText('providerConnected=false');
  await expect(page.getByTestId('hr-safety-checklist')).toContainText('liveProviderSync=false');
  await expect(page.getByTestId('hr-safety-checklist')).toContainText('payrollExecutionEnabled=false');
  await expect(page.getByTestId('hr-safety-checklist')).toContainText('automaticDecisionEnabled=false');
  await expect(page.getByTestId('hr-safety-checklist')).toContainText('hiddenScorePresent=false');
  await expect(page.getByTestId('hr-safety-checklist')).toContainText('humanReviewRequired=true');
  await expect(page.getByTestId('hr-incomplete-data-notice')).toContainText('incompleteData=true');
  await expect(page.locator('body')).not.toContainText(/real employee/i);
  await expect(page.locator('body')).not.toContainText(/real payroll/i);
}

async function expectRouteShell(page: Page, title: string) {
  const shell = page.getByTestId('hr-page-shell');
  await expect(shell).toBeVisible();
  await expect(page.getByRole('heading', { name: title, level: 1 })).toBeVisible();
  await expect(shell).toContainText('HR / Staff Governance Suite');
  await expect(page.locator('nav[aria-label="HR staff governance navigation"] a')).toHaveCount(20);
  await expect(page.getByRole('link', { name: 'HR / Staff Governance Suite' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'HR Operations Dashboard' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Recruitment / Hiring Readiness' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Limitations / Safety Boundaries' })).toBeVisible();
}

async function expectPermissionDeniedOrSafeFallback(page: Page) {
  const deniedPanel = page.getByTestId('hr-permission-denied-panel');
  const outerAccessDenied = page.getByRole('heading', { name: /Access Denied/i });

  if (await deniedPanel.count()) {
    await expect(deniedPanel).toBeVisible();
    await expect(deniedPanel).toContainText('Permission required');
    await expect(deniedPanel).toContainText('fail-closed');
  } else if (await outerAccessDenied.count()) {
    await expect(outerAccessDenied).toBeVisible();
    await expect(page.locator('body')).toContainText(/platform administrators/i);
  } else {
    await expect(page.locator('body')).toContainText(/fail-closed/i);
  }

  await expect(page.getByTestId('hr-dashboard-grid')).toHaveCount(0);
  await expect(page.getByTestId('hr-payroll-readiness-badge')).toHaveCount(0);
  await expect(page.getByTestId('hr-provider-deferred-badge')).toHaveCount(0);
  await expectForbiddenDomAbsent(page);
}

async function openAndAssertRoute(page: Page, route: (typeof HR_ROUTES)[number]) {
  await gotoHrRoute(page, route.path);
  await expectRouteShell(page, route.title);
  await expect(page.locator('body')).toContainText(route.boundary);
  await expect(page.locator('body')).toContainText(route.permission);
  await route.assertRoute(page);
  await expectCommonRuntimeSafety(page);
  await expectForbiddenDomAbsent(page);
}

async function visitRouteTitleWithFreshPage(browser: Browser, route: (typeof HR_ROUTES)[number]) {
  const page = await browser.newPage({ ignoreHTTPSErrors: true });

  try {
    page.setDefaultTimeout(15_000);
    page.setDefaultNavigationTimeout(15_000);
    await setAuthenticatedHrAdmin(page);
    await gotoHrRoute(page, route.path);
    await expectRouteShell(page, route.title);
    await expectCommonRuntimeSafety(page);
    await expectForbiddenDomAbsent(page);
  } finally {
    await page.close();
  }
}

test.describe('A-039.4 HR / Staff Governance route coverage', () => {
  test.describe.configure({ timeout: 180_000 });

  test('route inventory has exactly 20 routes', async () => {
    expect(HR_ROUTES).toHaveLength(20);
  });

  test('full access HR admin can visit all 20 routes', async ({ page }) => {
    await setAuthenticatedHrAdmin(page);

    for (const route of HR_ROUTES) {
      await gotoHrRoute(page, route.path);
      await expectRouteShell(page, route.title);
    }
  });

  for (const group of ROUTE_TITLE_GROUPS) {
    test(`route-title group ${group.label} shows route-specific titles`, async ({ browser }) => {
      for (const route of group.routes) {
        await test.step(`route-title ${route.key} ${route.path} -> ${route.title}`, async () => {
          await visitRouteTitleWithFreshPage(browser, route);
        });
      }
    });
  }

  test('each route shows at least one HR boundary label or the no-overclaim footer', async ({ page }) => {
    await setAuthenticatedHrAdmin(page);

    for (const route of HR_ROUTES) {
      await gotoHrRoute(page, route.path);
      const boundaryBanner = page.getByTestId('hr-boundary-banner');
      const noOverclaimFooter = page.getByTestId('hr-no-overclaim-footer');
      const bodyText = await page.locator('body').innerText();
      const hasBoundaryLabel = REQUIRED_BOUNDARY_LABELS.some((label) => bodyText.includes(label));
      const noOverclaimFooterCount = await noOverclaimFooter.count();

      expect(hasBoundaryLabel || noOverclaimFooterCount > 0).toBe(true);

      if (noOverclaimFooterCount > 0) {
        await expect(noOverclaimFooter.first()).toBeVisible();
      }
    }
  });

  test('all routes avoid forbidden DOM labels and actions', async ({ page }) => {
    await setAuthenticatedHrAdmin(page);

    for (const route of HR_ROUTES) {
      await gotoHrRoute(page, route.path);
      await expectForbiddenDomAbsent(page);
    }
  });
});

test.describe('A-039.4 HR / Staff Governance scenario groups', () => {
  test.describe.configure({ timeout: 120_000 });

  test('Scenario 1 — Authenticated admin entry and shell bootstrap', async ({ page }) => {
    await setAuthenticatedHrAdmin(page);
    await openAndAssertRoute(page, HR_ROUTES[0]);
    await expect(page.locator('nav[aria-label="HR staff governance navigation"] a')).toHaveCount(20);
  });

  test('Scenario 2 — HR overview / readiness / limitations', async ({ page }) => {
    await setAuthenticatedHrAdmin(page);
    await openAndAssertRoute(page, HR_ROUTES[0]);
    await gotoHrRoute(page, '/console/hr-staff-governance/limitations');
    await expectRequiredBoundaryLabels(page);
  });

  test('Scenario 3 — Dashboard incomplete-data and fakeMetrics=false boundary', async ({ page }) => {
    await setAuthenticatedHrAdmin(page);
    await openAndAssertRoute(page, HR_ROUTES[1]);
    await expect(page.getByTestId('hr-boundary-fakemetrics-false')).toBeVisible();
    await expect(page.getByTestId('hr-boundary-fakehrdata-false')).toBeVisible();
  });

  test('Scenario 4 — Recruitment metadata and hiring human-review-only boundary', async ({ page }) => {
    await setAuthenticatedHrAdmin(page);
    await openAndAssertRoute(page, HR_ROUTES[2]);
    await expect(page.getByTestId('hr-review-panel-human-review-boundary')).toContainText('No automatic HR decisions are available.');
  });

  test('Scenario 5 — Onboarding and probation metadata evidence', async ({ page }) => {
    await setAuthenticatedHrAdmin(page);
    await openAndAssertRoute(page, HR_ROUTES[3]);
    await expect(page.getByTestId('hr-evidence-table')).toContainText('PATCH /api/admin/hr-staff-governance/onboarding-cases/{resource_id}');
  });

  test('Scenario 6 — Employee records and staff profile evidence', async ({ page }) => {
    await setAuthenticatedHrAdmin(page);
    await openAndAssertRoute(page, HR_ROUTES[4]);
    await gotoHrRoute(page, HR_ROUTES[5].path);
    await openAndAssertRoute(page, HR_ROUTES[5]);
  });

  test('Scenario 7 — Faculty profile and workload visibility bridge', async ({ page }) => {
    await setAuthenticatedHrAdmin(page);
    await openAndAssertRoute(page, HR_ROUTES[6]);
    await gotoHrRoute(page, HR_ROUTES[16].path);
    await openAndAssertRoute(page, HR_ROUTES[16]);
  });

  test('Scenario 8 — Leave request human-review-only boundary', async ({ page }) => {
    await setAuthenticatedHrAdmin(page);
    await openAndAssertRoute(page, HR_ROUTES[7]);
    await expect(page.getByTestId('hr-review-panel-human-review-boundary')).toContainText('No automatic HR decisions are available.');
  });

  test('Scenario 9 — Performance appraisal no hidden score boundary', async ({ page }) => {
    await setAuthenticatedHrAdmin(page);
    await openAndAssertRoute(page, HR_ROUTES[8]);
    await expect(page.getByTestId('hr-boundary-no-hidden-employee-faculty-score')).toBeVisible();
  });

  test('Scenario 10 — Training certification expiry and compliance evidence', async ({ page }) => {
    await setAuthenticatedHrAdmin(page);
    await openAndAssertRoute(page, HR_ROUTES[9]);
    await expect(page.getByTestId('hr-boundary-incomplete-data-supported')).toBeVisible();
  });

  test('Scenario 11 — Staff requests and appeals review boundary', async ({ page }) => {
    await setAuthenticatedHrAdmin(page);
    await openAndAssertRoute(page, HR_ROUTES[10]);
    await gotoHrRoute(page, HR_ROUTES[11].path);
    await openAndAssertRoute(page, HR_ROUTES[11]);
  });

  test('Scenario 12 — HR policy exceptions review boundary', async ({ page }) => {
    await setAuthenticatedHrAdmin(page);
    await openAndAssertRoute(page, HR_ROUTES[12]);
    await expect(page.getByTestId('hr-human-review-badge').first()).toBeVisible();
  });

  test('Scenario 13 — Disciplinary case human-review-only boundary', async ({ page }) => {
    await setAuthenticatedHrAdmin(page);
    await openAndAssertRoute(page, HR_ROUTES[13]);
    await expect(page.getByTestId('hr-boundary-no-automatic-disciplinary-decision')).toBeVisible();
  });

  test('Scenario 14 — Offboarding and access lifecycle review-only boundary', async ({ page }) => {
    await setAuthenticatedHrAdmin(page);
    await openAndAssertRoute(page, HR_ROUTES[14]);
    await gotoHrRoute(page, HR_ROUTES[15].path);
    await openAndAssertRoute(page, HR_ROUTES[15]);
  });

  test('Scenario 15 — Workload bridge read-only academic context', async ({ page }) => {
    await setAuthenticatedHrAdmin(page);
    await openAndAssertRoute(page, HR_ROUTES[16]);
    await expect(page.getByTestId('hr-bridge-idp-sso-kz')).toBeVisible();
  });

  test('Scenario 16 — Payroll readiness provider-deferred boundary', async ({ page }) => {
    await setAuthenticatedHrAdmin(page);
    await openAndAssertRoute(page, HR_ROUTES[17]);
    await expect(page.getByTestId('hr-boundary-no-payroll-execution')).toBeVisible();
  });

  test('Scenario 17 — Provider readiness non-live boundary', async ({ page }) => {
    await setAuthenticatedHrAdmin(page);
    await openAndAssertRoute(page, HR_ROUTES[18]);
    await expect(page.getByTestId('hr-boundary-no-provider-live-sync')).toBeVisible();
  });

  test('Scenario 18 — Limitations and safety-boundary page', async ({ page }) => {
    await setAuthenticatedHrAdmin(page);
    await openAndAssertRoute(page, HR_ROUTES[19]);
    await expect(page.getByTestId('hr-no-overclaim-footer')).toContainText('No production/sales/GCC/L5/L6 claim.');
  });

  test('Scenario 19 — No-overclaim DOM scan across all routes', async ({ page }) => {
    await setAuthenticatedHrAdmin(page);

    for (const route of HR_ROUTES) {
      await gotoHrRoute(page, route.path);
      await expectForbiddenDomAbsent(page);
    }
  });

  test('Scenario 20 — Permission-denial fail-closed smoke', async ({ page }) => {
    await setRestrictedHrUser(page);

    for (const path of [
      '/console/hr-staff-governance/dashboard',
      '/console/hr-staff-governance/disciplinary',
      '/console/hr-staff-governance/payroll-readiness',
      '/console/hr-staff-governance/provider-readiness',
      '/console/hr-staff-governance/limitations',
    ]) {
      await gotoHrRoute(page, path);
      await expectPermissionDeniedOrSafeFallback(page);
    }
  });

  test('Scenario 21 — Suite closeout and route count assertion', async ({ page }) => {
    await setAuthenticatedHrAdmin(page);
    await openAndAssertRoute(page, HR_ROUTES[0]);
    expect(HR_ROUTES).toHaveLength(20);
    await expect(page.locator('nav[aria-label="HR staff governance navigation"] a')).toHaveCount(20);
  });
});