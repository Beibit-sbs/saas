import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockApiGet = vi.fn();
const mockApiPost = vi.fn();
const mockApiPatch = vi.fn();

vi.mock('@/shared/api/client', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  apiPost: (...args: unknown[]) => mockApiPost(...args),
  apiPatch: (...args: unknown[]) => mockApiPatch(...args),
}));

describe('researchScienceApi', () => {
  beforeEach(() => {
    mockApiGet.mockReset();
    mockApiPost.mockReset();
    mockApiPatch.mockReset();
    mockApiGet.mockResolvedValue({});
    mockApiPost.mockResolvedValue({});
    mockApiPatch.mockResolvedValue({});
  });

  it('uses the admin research-science namespace for health, dashboard, matrix, and limitations', async () => {
    const { researchScienceApi } = await import('@/modules/research-science/api');

    await researchScienceApi.getResearchScienceHealth();
    await researchScienceApi.getResearchScienceDashboard();
    await researchScienceApi.getResearchScienceMatrixSummary();
    await researchScienceApi.getResearchScienceLimitations();

    expect(mockApiGet.mock.calls.map((call) => call[0])).toEqual([
      '/api/admin/research-science/health',
      '/api/admin/research-science/dashboard',
      '/api/admin/research-science/matrix-summary',
      '/api/admin/research-science/limitations',
    ]);
  });

  it('exports the expected registry and evidence client methods', async () => {
    const { researchScienceApi } = await import('@/modules/research-science/api');
    const keys = Object.keys(researchScienceApi).sort();

    expect(keys).toEqual(expect.arrayContaining([
      'listResearchProjects',
      'listStudentResearchWork',
      'listScientificSupervision',
      'listPublications',
      'listConferences',
      'listGrants',
      'listGrantDeliverables',
      'listEthicsRequests',
      'listEthicsAmendments',
      'listResearchEvidence',
      'listResearchAuditEvents',
      'listResearchBridges',
      'getResearchBridgeSummary',
    ]));
  });

  it('uses PATCH only for safe update endpoints', async () => {
    const { researchScienceApi } = await import('@/modules/research-science/api');

    await researchScienceApi.updateResearchProject(1, { title: 'Updated' });
    await researchScienceApi.updateStudentResearchWork(2, { topic_title: 'Updated topic' });
    await researchScienceApi.updateScientificSupervision(3, { supervision_ref: 'SUP-2' });
    await researchScienceApi.updatePublicationMetadata(4, { title: 'Updated publication' });
    await researchScienceApi.updateConferenceParticipation(5, { title: 'Updated conference' });
    await researchScienceApi.updateGrantApplication(6, { title: 'Updated grant' });
    await researchScienceApi.updateGrantDeliverable(7, { title: 'Updated deliverable' });
    await researchScienceApi.updateEthicsRequest(8, { title: 'Updated ethics' });

    expect(mockApiPatch.mock.calls.map((call) => call[0])).toEqual([
      '/api/admin/research-science/projects/1',
      '/api/admin/research-science/student-research/2',
      '/api/admin/research-science/supervision/3',
      '/api/admin/research-science/publications/4',
      '/api/admin/research-science/conferences/5',
      '/api/admin/research-science/grants/6',
      '/api/admin/research-science/grant-deliverables/7',
      '/api/admin/research-science/ethics/8',
    ]);
  });

  it('uses evidence, bridge summary, and audit endpoints as specified', async () => {
    const { researchScienceApi } = await import('@/modules/research-science/api');

    await researchScienceApi.listResearchEvidence();
    await researchScienceApi.listResearchAuditEvents();
    await researchScienceApi.getResearchBridgeSummary();

    expect(mockApiGet.mock.calls.map((call) => call[0])).toEqual([
      '/api/admin/research-science/evidence',
      '/api/admin/research-science/audit',
      '/api/admin/research-science/bridges/summary',
    ]);
  });

  it('does not expose forbidden sync, fake, score, or autonomous methods', async () => {
    const { researchScienceApi } = await import('@/modules/research-science/api');
    const keys = Object.keys(researchScienceApi).join(' ');

    expect(keys).not.toMatch(/autoApprove|autoSubmit|autoVerify|syncScopus|syncWebOfScience|syncORCID|syncMinistry/i);
    expect(keys).not.toMatch(/CitationScore|ResearcherScore|OfficialRanking|FakePublication|FakeCertificate|FakeGrantEvidence/i);
  });
});