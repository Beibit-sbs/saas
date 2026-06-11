import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockApiGet = vi.fn();
const mockApiPost = vi.fn();
const mockApiPatch = vi.fn();

vi.mock('@/shared/api/client', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  apiPost: (...args: unknown[]) => mockApiPost(...args),
  apiPatch: (...args: unknown[]) => mockApiPatch(...args),
}));

describe('qualityAccreditationApi', () => {
  beforeEach(() => {
    mockApiGet.mockReset();
    mockApiPost.mockReset();
    mockApiPatch.mockReset();
    mockApiGet.mockResolvedValue({ items: [] });
    mockApiPost.mockResolvedValue({});
    mockApiPatch.mockResolvedValue({});
  });

  it('uses runtime shell and admin quality-accreditation namespaces for baseline endpoints', async () => {
    const { qualityAccreditationApi } = await import('@/modules/quality-accreditation/api');

    await qualityAccreditationApi.getQualityAccreditationRuntimeShell();
    await qualityAccreditationApi.getAccreditationRegistry();
    await qualityAccreditationApi.getAccreditationEvidenceRuntime();
    await qualityAccreditationApi.getSelfAssessmentRuntime();
    await qualityAccreditationApi.getCorrectiveActionRuntime();
    await qualityAccreditationApi.getImprovementPlanRuntime();
    await qualityAccreditationApi.getQualityAccreditationHealth();
    await qualityAccreditationApi.getQualityAccreditationOverview();
    await qualityAccreditationApi.getQualityAccreditationDashboard();
    await qualityAccreditationApi.getQualityAccreditationMatrixSummary();
    await qualityAccreditationApi.getQualityAccreditationLimitations();

    expect(mockApiGet.mock.calls.map((call) => call[0])).toEqual([
      '/api/v1/quality-accreditation/runtime-shell',
      '/api/v1/quality-accreditation/accreditation-registry',
      '/api/v1/quality-accreditation/accreditation-evidence',
      '/api/v1/quality-accreditation/self-assessment',
      '/api/v1/quality-accreditation/corrective-actions',
      '/api/v1/quality-accreditation/improvement-plan-runtime',
      '/api/admin/quality-accreditation/health',
      '/api/admin/quality-accreditation/overview',
      '/api/admin/quality-accreditation/dashboard',
      '/api/admin/quality-accreditation/matrix-summary',
      '/api/admin/quality-accreditation/limitations',
    ]);
  });

  it('exports the expected registry, review, bridge, and audit client methods', async () => {
    const { qualityAccreditationApi } = await import('@/modules/quality-accreditation/api');
    const keys = Object.keys(qualityAccreditationApi).sort();

    expect(keys).toEqual(expect.arrayContaining([
      'listQualityFrameworks',
      'getAccreditationRegistry',
      'getAccreditationEvidenceRuntime',
      'getSelfAssessmentRuntime',
      'getCorrectiveActionRuntime',
      'getImprovementPlanRuntime',
      'useImprovementPlanRuntime',
      'listAccreditationStandards',
      'listStandardCriteria',
      'listQualityEvidence',
      'reviewQualityEvidence',
      'listProgramReadiness',
      'listInstitutionalReadiness',
      'listSelfAssessmentReports',
      'listQualityImprovementPlans',
      'listInternalQualityAudits',
      'listProgramReviewCycles',
      'listLearningOutcomesAssessments',
      'listStakeholderFeedback',
      'listAccreditationCommitteeWorkflows',
      'listExternalExpertReviews',
      'listComplianceGapAnalysis',
      'listAccreditationCalendar',
      'listQualityRisks',
      'listQualityBridges',
      'listQualityBrainSignals',
      'listQualityAuditEvents',
      'listQualityStatusHistory',
    ]));
  });

  it('uses PATCH only for safe update endpoints', async () => {
    const { qualityAccreditationApi } = await import('@/modules/quality-accreditation/api');

    await qualityAccreditationApi.updateQualityFramework(1, { title: 'Updated framework' });
    await qualityAccreditationApi.updateAccreditationStandard(2, { title: 'Updated standard' });
    await qualityAccreditationApi.updateQualityEvidence(3, { title: 'Updated evidence' });
    await qualityAccreditationApi.updateProgramReadiness(4, { status: 'UPDATED' });
    await qualityAccreditationApi.updateInstitutionalReadiness(5, { status: 'UPDATED' });
    await qualityAccreditationApi.updateSelfAssessmentReport(6, { title: 'Updated report' });
    await qualityAccreditationApi.updateQualityImprovementPlan(7, { status: 'UPDATED' });
    await qualityAccreditationApi.updateInternalQualityAudit(8, { status: 'UPDATED' });
    await qualityAccreditationApi.updateExternalExpertReview(9, { status: 'UPDATED' });

    expect(mockApiPatch.mock.calls.map((call) => call[0])).toEqual([
      '/api/admin/quality-accreditation/frameworks/1',
      '/api/admin/quality-accreditation/standards/2',
      '/api/admin/quality-accreditation/evidence/3',
      '/api/admin/quality-accreditation/program-readiness/4',
      '/api/admin/quality-accreditation/institutional-readiness/5',
      '/api/admin/quality-accreditation/self-assessment/6',
      '/api/admin/quality-accreditation/improvement-plans/7',
      '/api/admin/quality-accreditation/internal-audits/8',
      '/api/admin/quality-accreditation/external-review/9',
    ]);
  });

  it('uses evidence review, brain, bridge, and audit-history endpoints as specified', async () => {
    const { qualityAccreditationApi } = await import('@/modules/quality-accreditation/api');

    await qualityAccreditationApi.reviewQualityEvidence(11, { status: 'REVIEWED_METADATA_ONLY' });
    await qualityAccreditationApi.listQualityBridges();
    await qualityAccreditationApi.listQualityBrainSignals();
    await qualityAccreditationApi.listQualityAuditEvents();
    await qualityAccreditationApi.listQualityStatusHistory();

    expect(mockApiPost.mock.calls.map((call) => call[0])).toContain('/api/admin/quality-accreditation/evidence/11/review');
    expect(mockApiGet.mock.calls.map((call) => call[0])).toEqual(expect.arrayContaining([
      '/api/admin/quality-accreditation/bridges',
      '/api/admin/quality-accreditation/brain-signals',
      '/api/admin/quality-accreditation/audit',
      '/api/admin/quality-accreditation/status-history',
    ]));
  });

  it('does not expose forbidden approval, sync, fake, hidden-score, or ranking methods', async () => {
    const { qualityAccreditationApi } = await import('@/modules/quality-accreditation/api');
    const keys = Object.keys(qualityAccreditationApi).join(' ');

    expect(keys).not.toMatch(/approveAccreditationOfficially|submitToMinistry|claimRankingImprovement|autoApproveAccreditation/i);
    expect(keys).not.toMatch(/createFakeAccreditationEvidence|createFakeQualityScore|createFakeSurveyResult/i);
    expect(keys).not.toMatch(/HiddenProgramScore|HiddenFacultyScore|HiddenStudentScore|OfficialRanking/i);
    expect(keys).not.toMatch(/syncProvider|syncExternalDatabase/i);
  });
});