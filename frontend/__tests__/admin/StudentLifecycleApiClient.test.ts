import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockApiGet = vi.fn();
const mockApiPost = vi.fn();
const mockApiPatch = vi.fn();

vi.mock('@/shared/api/client', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  apiPost: (...args: unknown[]) => mockApiPost(...args),
  apiPatch: (...args: unknown[]) => mockApiPatch(...args),
}));

describe('studentLifecycleApi', () => {
  beforeEach(() => {
    mockApiGet.mockReset();
    mockApiPost.mockReset();
    mockApiPatch.mockReset();
    mockApiGet.mockResolvedValue({});
    mockApiPost.mockResolvedValue({});
    mockApiPatch.mockResolvedValue({});
  });

  it('uses the admin BFF namespace for dashboard and health reads', async () => {
    const { studentLifecycleApi } = await import('@/modules/student-lifecycle/api');

    await studentLifecycleApi.getStudentLifecycleDashboard();
    await studentLifecycleApi.getStudentLifecycleHealth();

    expect(mockApiGet).toHaveBeenNthCalledWith(1, '/api/admin/student-lifecycle/dashboard');
    expect(mockApiGet).toHaveBeenNthCalledWith(2, '/api/admin/student-lifecycle/health');
  });

  it('uses GET for registry/detail reads only', async () => {
    const { studentLifecycleApi } = await import('@/modules/student-lifecycle/api');

    await studentLifecycleApi.listApplicants();
    await studentLifecycleApi.getApplicant(12);
    await studentLifecycleApi.listStudents();
    await studentLifecycleApi.getStudentProfile(15);
    await studentLifecycleApi.listEnrollments();
    await studentLifecycleApi.getAcademicRecord(8);
    await studentLifecycleApi.listTranscriptPreviews();
    await studentLifecycleApi.getDegreeProgress(200);
    await studentLifecycleApi.listStudentRequests();
    await studentLifecycleApi.listStudentAppeals();
    await studentLifecycleApi.listInterventionPlans();
    await studentLifecycleApi.listStudentLifecycleAuditEvents();
    await studentLifecycleApi.listStudentLifecycleEvidence();

    const calledPaths = mockApiGet.mock.calls.map((call) => call[0]);
    expect(calledPaths.every((path) => String(path).startsWith('/api/admin/student-lifecycle'))).toBe(true);
    expect(calledPaths.some((path) => /platonus|sis|provider/i.test(String(path)))).toBe(false);
  });

  it('uses POST for controlled workflow mutations', async () => {
    const { studentLifecycleApi } = await import('@/modules/student-lifecycle/api');

    await studentLifecycleApi.createApplicant({ applicant_code: 'A-1', program_interest: 'CS', entry_term: '2026-FALL' });
    await studentLifecycleApi.submitApplicant(1);
    await studentLifecycleApi.updateApplicantStatus(1, { new_status: 'UNDER_REVIEW' as const, reason: 'Review' });
    await studentLifecycleApi.createTranscriptPreview({ student_id: 7, academic_record_id: 9 });
    await studentLifecycleApi.reviewGraduationReadiness(7, { new_status: 'HUMAN_REVIEW_REQUIRED' as const, note: 'Advisor step' });
    await studentLifecycleApi.attachStudentLifecycleEvidenceMetadata({ audit_event_id: 5, entity_type: 'request', entity_id: 10, evidence_type: 'NOTE', evidence_ref: 'e-1' });

    expect(mockApiPost.mock.calls.map((call) => call[0])).toEqual([
      '/api/admin/student-lifecycle/applicants',
      '/api/admin/student-lifecycle/applicants/1/submit',
      '/api/admin/student-lifecycle/applicants/1/status',
      '/api/admin/student-lifecycle/transcripts/preview',
      '/api/admin/student-lifecycle/degree-progress/7/graduation-review',
      '/api/admin/student-lifecycle/evidence',
    ]);
  });

  it('uses PATCH only for update endpoints', async () => {
    const { studentLifecycleApi } = await import('@/modules/student-lifecycle/api');

    await studentLifecycleApi.updateApplicant(1, { notes: 'Updated' });
    await studentLifecycleApi.updateStudentProfile(2, { notes: 'Updated' });
    await studentLifecycleApi.updateEnrollment(3, { notes: 'Updated' });

    expect(mockApiPatch.mock.calls.map((call) => call[0])).toEqual([
      '/api/admin/student-lifecycle/applicants/1',
      '/api/admin/student-lifecycle/students/2',
      '/api/admin/student-lifecycle/enrollment/3',
    ]);
  });

  it('does not export provider, platonus, sis, or official transcript issuing methods', async () => {
    const { studentLifecycleApi } = await import('@/modules/student-lifecycle/api');
    const keys = Object.keys(studentLifecycleApi).join(' ');
    expect(keys).not.toMatch(/provider|platonus|sis|official/i);
    expect(keys).toMatch(/Preview/);
  });
});