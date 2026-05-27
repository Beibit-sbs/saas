import { beforeEach, describe, expect, it, vi } from 'vitest';

const client = vi.hoisted(() => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
}));

vi.mock('@/shared/api/client', () => client);

import { studentServicesSupportApi } from '@/modules/student_services_support/api';
import { STUDENT_SERVICES_SUPPORT_API_PATHS } from '@/modules/student_services_support/constants';

describe('Student Services Support API client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    client.apiGet.mockResolvedValue(undefined);
    client.apiPost.mockResolvedValue(undefined);
    client.apiPatch.mockResolvedValue(undefined);
  });

  it('maps request and case read endpoints', async () => {
    await studentServicesSupportApi.listServiceRequests();
    await studentServicesSupportApi.getServiceRequest(10);
    await studentServicesSupportApi.listSupportCases();
    await studentServicesSupportApi.getSupportCase(11);
    await studentServicesSupportApi.getDashboardSummary();

    expect(client.apiGet).toHaveBeenCalledWith(STUDENT_SERVICES_SUPPORT_API_PATHS.requests);
    expect(client.apiGet).toHaveBeenCalledWith(STUDENT_SERVICES_SUPPORT_API_PATHS.requestById(10));
    expect(client.apiGet).toHaveBeenCalledWith(STUDENT_SERVICES_SUPPORT_API_PATHS.cases);
    expect(client.apiGet).toHaveBeenCalledWith(STUDENT_SERVICES_SUPPORT_API_PATHS.caseById(11));
    expect(client.apiGet).toHaveBeenCalledWith(STUDENT_SERVICES_SUPPORT_API_PATHS.dashboardSummary);
  });

  it('maps create endpoints', async () => {
    await studentServicesSupportApi.createServiceRequest({ request_type: 'general_support', student_id: 'S-1' });
    await studentServicesSupportApi.createSupportCase({ case_type: 'support_case' });
    await studentServicesSupportApi.addSupportCaseNote(11, { note: 'n1' });
    await studentServicesSupportApi.attachSupportEvidenceMetadata(11, { evidence_type: 'document_metadata' });
    await studentServicesSupportApi.createHardshipRequest({ request_id: 10 });
    await studentServicesSupportApi.createAccommodationRequest({ request_id: 10 });
    await studentServicesSupportApi.createComplaint({ complaint_summary: 'summary' });
    await studentServicesSupportApi.createEscalation({ case_id: 11, reason: 'reason' });

    expect(client.apiPost).toHaveBeenCalledWith(STUDENT_SERVICES_SUPPORT_API_PATHS.requests, { request_type: 'general_support', student_id: 'S-1' });
    expect(client.apiPost).toHaveBeenCalledWith(STUDENT_SERVICES_SUPPORT_API_PATHS.cases, { case_type: 'support_case' });
    expect(client.apiPost).toHaveBeenCalledWith(STUDENT_SERVICES_SUPPORT_API_PATHS.caseNotes(11), { note: 'n1' });
    expect(client.apiPost).toHaveBeenCalledWith(STUDENT_SERVICES_SUPPORT_API_PATHS.caseEvidence(11), { evidence_type: 'document_metadata' });
    expect(client.apiPost).toHaveBeenCalledWith(STUDENT_SERVICES_SUPPORT_API_PATHS.hardship, { request_id: 10 });
    expect(client.apiPost).toHaveBeenCalledWith(STUDENT_SERVICES_SUPPORT_API_PATHS.accommodations, { request_id: 10 });
    expect(client.apiPost).toHaveBeenCalledWith(STUDENT_SERVICES_SUPPORT_API_PATHS.complaints, { complaint_summary: 'summary' });
    expect(client.apiPost).toHaveBeenCalledWith(STUDENT_SERVICES_SUPPORT_API_PATHS.escalations, { case_id: 11, reason: 'reason' });
  });

  it('maps assign and status patch endpoints', async () => {
    await studentServicesSupportApi.assignServiceRequest(1, { assigned_to_user_id: 'U-2' });
    await studentServicesSupportApi.updateServiceRequestStatus(1, { status: 'in_progress' });

    expect(client.apiPatch).toHaveBeenCalledWith(STUDENT_SERVICES_SUPPORT_API_PATHS.requestAssign(1), { assigned_to_user_id: 'U-2' });
    expect(client.apiPatch).toHaveBeenCalledWith(STUDENT_SERVICES_SUPPORT_API_PATHS.requestStatus(1), { status: 'in_progress' });
  });

  it('does not expose forbidden executors', () => {
    expect('approveHardshipAutomatically' in studentServicesSupportApi).toBe(false);
    expect('approveAccommodationAutomatically' in studentServicesSupportApi).toBe(false);
    expect('resolveComplaintAutomatically' in studentServicesSupportApi).toBe(false);
    expect('submitToGovernment' in studentServicesSupportApi).toBe(false);
    expect('hiddenScore' in studentServicesSupportApi).toBe(false);
  });
});
