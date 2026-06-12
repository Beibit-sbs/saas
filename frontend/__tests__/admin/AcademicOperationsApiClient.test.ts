import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockApiGet = vi.fn();
const mockApiPost = vi.fn();
const mockApiPatch = vi.fn();

vi.mock('@/shared/api/client', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  apiPost: (...args: unknown[]) => mockApiPost(...args),
  apiPatch: (...args: unknown[]) => mockApiPatch(...args),
}));

describe('academicOperationsApi', () => {
  beforeEach(() => {
    mockApiGet.mockReset();
    mockApiPost.mockReset();
    mockApiPatch.mockReset();
    mockApiGet.mockResolvedValue({});
    mockApiPost.mockResolvedValue({});
    mockApiPatch.mockResolvedValue({});
  });

  it('uses the admin BFF namespace for health, dashboard, and matrix reads', async () => {
    const { academicOperationsApi } = await import('@/modules/academic-operations/api');

    await academicOperationsApi.getAcademicOperationsHealth();
    await academicOperationsApi.getAcademicOperationsDashboard();
    await academicOperationsApi.getAcademicOperationsMatrixSummary();
    await academicOperationsApi.getAcademicOperationsCanonicalReuseSummary();

    expect(mockApiGet.mock.calls.map((call) => call[0])).toEqual([
      '/api/admin/academic-operations/health',
      '/api/admin/academic-operations/dashboard',
      '/api/admin/academic-operations/matrix-summary',
      '/api/admin/academic-operations/canonical-reuse-summary',
    ]);
  });

  it('exports all expected registry and bridge client methods', async () => {
    const { academicOperationsApi } = await import('@/modules/academic-operations/api');
    const keys = Object.keys(academicOperationsApi).sort();

    expect(keys).toEqual(expect.arrayContaining([
      'listAcademicGroups',
      'getAcademicGroup',
      'listCohorts',
      'listCourseRegistrationMetadata',
      'listGradebookMetadata',
      'listRetakePlans',
      'listSummerSemesterTerms',
      'listAdvisorTutorAssignments',
      'listBridges',
      'getStudentLifecycleBridgeSummary',
      'listAuditEvents',
      'listEvidence',
      'attachEvidence',
    ]));
  });

  it('uses PATCH only for safe update endpoints', async () => {
    const { academicOperationsApi } = await import('@/modules/academic-operations/api');

    await academicOperationsApi.updateAcademicGroup(1, { group_name: 'Updated' });
    await academicOperationsApi.updateCohort(2, { cohort_name: 'Updated' });
    await academicOperationsApi.updateGradebookMetadata(3, { metadata: { grading: 'manual' } });
    await academicOperationsApi.updateRetakePlan(4, { retake_window: '2026-08' });
    await academicOperationsApi.updateSummerSemesterTerm(5, { display_name: 'Updated term' });
    await academicOperationsApi.updateAdvisorTutorAssignment(6, { assignment_code: 'AT-2' });

    expect(mockApiPatch.mock.calls.map((call) => call[0])).toEqual([
      '/api/admin/academic-operations/academic-groups/1',
      '/api/admin/academic-operations/cohorts/2',
      '/api/admin/academic-operations/gradebook-metadata/3',
      '/api/admin/academic-operations/retakes/4',
      '/api/admin/academic-operations/summer-semesters/5',
      '/api/admin/academic-operations/advisor-tutor/6',
    ]);
  });

  it('does not expose forbidden delete, publish, sync, sanction, or approve-grade methods', async () => {
    const { academicOperationsApi } = await import('@/modules/academic-operations/api');
    const keys = Object.keys(academicOperationsApi).join(' ');

    expect(keys).not.toMatch(/delete|publish|sync|sanction|approve|transcript|order|decree/i);
  });

  it('uses the expected evidence and bridge endpoints', async () => {
    const { academicOperationsApi } = await import('@/modules/academic-operations/api');

    await academicOperationsApi.listBridges();
    await academicOperationsApi.getQualityAccreditationBridgeSummary();
    await academicOperationsApi.listEvidence();

    expect(mockApiGet.mock.calls.map((call) => call[0])).toEqual([
      '/api/admin/academic-operations/bridges',
      '/api/admin/academic-operations/bridges/quality-accreditation',
      '/api/admin/academic-operations/evidence',
    ]);
  });
});

describe('academicOperationsRuntimeApi', () => {
  beforeEach(() => {
    mockApiGet.mockReset();
    mockApiPost.mockReset();
    mockApiPatch.mockReset();
    mockApiGet.mockResolvedValue({});
    mockApiPost.mockResolvedValue({});
    mockApiPatch.mockResolvedValue({});
  });

  it('uses the v1 runtime-shell endpoint', async () => {
    const { academicOperationsRuntimeApi } = await import('@/modules/academic-operations-runtime/api');

    await academicOperationsRuntimeApi.getRuntimeShell();

    expect(mockApiGet).toHaveBeenCalledWith('/api/v1/academic-operations/runtime-shell');
  });

  it('uses the academic registry runtime endpoint', async () => {
    const { academicOperationsRuntimeApi } = await import('@/modules/academic-operations-runtime/api');

    await academicOperationsRuntimeApi.getAcademicRegistryRuntime();

    expect(mockApiGet).toHaveBeenCalledWith('/api/academic-operations/runtime/academic-registry');
  });

  it('uses the curriculum runtime endpoint', async () => {
    const { academicOperationsRuntimeApi } = await import('@/modules/academic-operations-runtime/api');

    await academicOperationsRuntimeApi.getCurriculumRuntime();

    expect(mockApiGet).toHaveBeenCalledWith('/api/academic-operations/runtime/curriculum');
  });

  it('uses the timetable runtime endpoint', async () => {
    const { academicOperationsRuntimeApi } = await import('@/modules/academic-operations-runtime/api');

    await academicOperationsRuntimeApi.getTimetableRuntime();

    expect(mockApiGet).toHaveBeenCalledWith('/api/academic-operations/runtime/timetable');
  });

  it('uses the attendance runtime endpoint', async () => {
    const { academicOperationsRuntimeApi } = await import('@/modules/academic-operations-runtime/api');

    await academicOperationsRuntimeApi.getAttendanceRuntime();

    expect(mockApiGet).toHaveBeenCalledWith('/api/academic-operations/runtime/attendance');
  });

  it('uses the assessment runtime endpoint', async () => {
    const { academicOperationsRuntimeApi } = await import('@/modules/academic-operations-runtime/api');

    await academicOperationsRuntimeApi.getAssessmentRuntime();

    expect(mockApiGet).toHaveBeenCalledWith('/api/academic-operations/runtime/assessment');
  });
});