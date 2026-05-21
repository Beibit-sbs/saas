import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockApiGet = vi.fn();
const mockApiPatch = vi.fn();
const mockApiPost = vi.fn();

vi.mock('@/shared/api/client', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  apiPatch: (...args: unknown[]) => mockApiPatch(...args),
  apiPost: (...args: unknown[]) => mockApiPost(...args),
}));

describe('documentWorkflowApi', () => {
  beforeEach(() => {
    mockApiGet.mockReset();
    mockApiPatch.mockReset();
    mockApiPost.mockReset();
    mockApiGet.mockResolvedValue({});
    mockApiPatch.mockResolvedValue({});
    mockApiPost.mockResolvedValue({});
  });

  it('uses the shared BFF-compatible admin documents base path', async () => {
    const { documentWorkflowApi } = await import('@/modules/document-workflow/api');
    await documentWorkflowApi.listDocuments({ status: 'UNDER_REVIEW', page_size: 25 });
    expect(mockApiGet).toHaveBeenCalledWith('/api/admin/documents', {
      status: 'UNDER_REVIEW',
      page_size: 25,
    });
  });

  it('calls document lifecycle endpoints with typed payloads', async () => {
    const { documentWorkflowApi } = await import('@/modules/document-workflow/api');
    await documentWorkflowApi.registerDocument(12, { registry_number: 'DOC-001', version: 3 });
    await documentWorkflowApi.submitDocumentReview(12, { reviewer_user_id: 4, note: 'review', version: 3 });
    await documentWorkflowApi.approveDocument(12, { comment: 'approved', version: 3 });

    expect(mockApiPost).toHaveBeenNthCalledWith(1, '/api/admin/documents/12/register', {
      registry_number: 'DOC-001',
      version: 3,
    });
    expect(mockApiPost).toHaveBeenNthCalledWith(2, '/api/admin/documents/12/submit-review', {
      reviewer_user_id: 4,
      note: 'review',
      version: 3,
    });
    expect(mockApiPost).toHaveBeenNthCalledWith(3, '/api/admin/documents/12/approve', {
      comment: 'approved',
      version: 3,
    });
  });

  it('calls decree and correspondence endpoints without bypassing the admin namespace', async () => {
    const { documentWorkflowApi } = await import('@/modules/document-workflow/api');
    await documentWorkflowApi.submitDecreeLegalReview(8, { note: 'legal', version: 2 });
    await documentWorkflowApi.recordOutgoingSentMetadata(22);
    await documentWorkflowApi.getDocumentWorkflowDashboardSummary();

    expect(mockApiPost).toHaveBeenCalledWith('/api/admin/documents/decrees/8/legal-review', {
      note: 'legal',
      version: 2,
    });
    expect(mockApiPost).toHaveBeenCalledWith('/api/admin/documents/correspondence/22/sent-metadata', {});
    expect(mockApiGet).toHaveBeenCalledWith('/api/admin/documents/dashboard/summary');
  });

  it('uses patch for update endpoints', async () => {
    const { documentWorkflowApi } = await import('@/modules/document-workflow/api');
    await documentWorkflowApi.updateDocument(9, { title: 'Updated', version: 4 });
    await documentWorkflowApi.updateDecree(13, { title: 'Updated decree', version: 2 });

    expect(mockApiPatch).toHaveBeenCalledWith('/api/admin/documents/9', {
      title: 'Updated',
      version: 4,
    });
    expect(mockApiPatch).toHaveBeenCalledWith('/api/admin/documents/decrees/13', {
      title: 'Updated decree',
      version: 2,
    });
  });
});