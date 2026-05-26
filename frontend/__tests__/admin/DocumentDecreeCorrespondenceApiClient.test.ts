import { beforeEach, describe, expect, it, vi } from 'vitest';

const client = vi.hoisted(() => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
}));

vi.mock('@/shared/api/client', () => client);

import { documentDecreeCorrespondenceApi } from '@/modules/document-decree-correspondence/api';
import { DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS } from '@/modules/document-decree-correspondence/constants';

describe('Document Decree Correspondence API client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    client.apiGet.mockResolvedValue(undefined);
    client.apiPost.mockResolvedValue(undefined);
  });

  it('maps core overview/readiness/dashboard reads', async () => {
    await documentDecreeCorrespondenceApi.getDdcOverview();
    await documentDecreeCorrespondenceApi.getDdcReadiness();
    await documentDecreeCorrespondenceApi.getDdcLimitations();
    await documentDecreeCorrespondenceApi.getDdcSafetyBoundaries();
    await documentDecreeCorrespondenceApi.getDdcDashboard();
    await documentDecreeCorrespondenceApi.getDdcHealth();

    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.overview);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.readiness);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.limitations);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.safetyBoundaries);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.dashboard);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.health);
  });

  it('maps document/decree/correspondence reads', async () => {
    await documentDecreeCorrespondenceApi.getDdcDocuments();
    await documentDecreeCorrespondenceApi.getDdcDocumentIntake();
    await documentDecreeCorrespondenceApi.getDdcDocumentRouting();
    await documentDecreeCorrespondenceApi.getDdcRectorResolutions();
    await documentDecreeCorrespondenceApi.getDdcDecrees();
    await documentDecreeCorrespondenceApi.getDdcDecreeDrafts();
    await documentDecreeCorrespondenceApi.getDdcIncomingCorrespondence();
    await documentDecreeCorrespondenceApi.getDdcOutgoingCorrespondence();

    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.documents);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.documentIntake);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.documentRouting);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.rectorResolutions);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.decrees);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.decreeDrafts);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.incomingCorrespondence);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.outgoingCorrespondence);
  });

  it('maps template/bridge/governance reads', async () => {
    await documentDecreeCorrespondenceApi.getDdcTemplates();
    await documentDecreeCorrespondenceApi.getDdcCommitteeDecisions();
    await documentDecreeCorrespondenceApi.getDdcAssignments();
    await documentDecreeCorrespondenceApi.getDdcExecutionControl();
    await documentDecreeCorrespondenceApi.getDdcSlaDeadlines();

    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.templates);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.committeeDecisions);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.assignments);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.executionControl);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.slaDeadlines);
  });

  it('maps evidence/audit/archive/readiness reads', async () => {
    await documentDecreeCorrespondenceApi.getDdcEvidence();
    await documentDecreeCorrespondenceApi.getDdcAttachments();
    await documentDecreeCorrespondenceApi.getDdcAuditEvents();
    await documentDecreeCorrespondenceApi.getDdcArchive();
    await documentDecreeCorrespondenceApi.getDdcSignatureReadiness();
    await documentDecreeCorrespondenceApi.getDdcDeliveryReadiness();

    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.evidence);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.attachments);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.auditEvents);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.archive);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.signatureReadiness);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.deliveryReadiness);
  });

  it('maps bridge/role/permission/meta reads', async () => {
    await documentDecreeCorrespondenceApi.getDdcBridgeExecutive();
    await documentDecreeCorrespondenceApi.getDdcBridgeAssignments();
    await documentDecreeCorrespondenceApi.getDdcRoles();
    await documentDecreeCorrespondenceApi.getDdcPermissions();
    await documentDecreeCorrespondenceApi.getDdcMetadataContract();

    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.bridgesExecutive);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.bridgesAssignments);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.roles);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.permissions);
    expect(client.apiGet).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.metadataContract);
  });

  it('maps document lifecycle post helpers', async () => {
    await documentDecreeCorrespondenceApi.createDdcDocumentIntake({ title: 'intake' });
    await documentDecreeCorrespondenceApi.createDdcDocumentRegistrationMetadata({ title: 'registration' });
    await documentDecreeCorrespondenceApi.createDdcDocumentRoutingMetadata({ title: 'routing' });
    await documentDecreeCorrespondenceApi.createDdcRectorResolutionMetadata({ title: 'resolution' });
    await documentDecreeCorrespondenceApi.createDdcDecreeMetadata({ title: 'decree' });
    await documentDecreeCorrespondenceApi.createDdcDecreeDraft({ title: 'draft' });

    expect(client.apiPost).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.documentIntake, { title: 'intake' });
    expect(client.apiPost).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.documentRegistration, { title: 'registration' });
    expect(client.apiPost).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.documentRouting, { title: 'routing' });
    expect(client.apiPost).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.rectorResolutionsMetadata, { title: 'resolution' });
    expect(client.apiPost).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.decreesMetadata, { title: 'decree' });
    expect(client.apiPost).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.decreeDrafts, { title: 'draft' });
  });

  it('maps correspondence/template/bridge post helpers', async () => {
    await documentDecreeCorrespondenceApi.createDdcIncomingCorrespondence({ title: 'incoming' });
    await documentDecreeCorrespondenceApi.createDdcOutgoingCorrespondence({ title: 'outgoing' });
    await documentDecreeCorrespondenceApi.createDdcTemplateMetadata({ title: 'template' });
    await documentDecreeCorrespondenceApi.createDdcCommitteeDecisionBridge({ title: 'committee' });
    await documentDecreeCorrespondenceApi.createDdcAssignmentBridge({ title: 'assignment' });

    expect(client.apiPost).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.incomingCorrespondence, { title: 'incoming' });
    expect(client.apiPost).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.outgoingCorrespondence, { title: 'outgoing' });
    expect(client.apiPost).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.templatesMetadata, { title: 'template' });
    expect(client.apiPost).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.committeeDecisionsBridge, { title: 'committee' });
    expect(client.apiPost).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.assignmentsBridge, { title: 'assignment' });
  });

  it('maps controls/evidence/audit/archive post helpers', async () => {
    await documentDecreeCorrespondenceApi.createDdcExecutionControlMetadata({ title: 'control' });
    await documentDecreeCorrespondenceApi.createDdcSlaDeadline({ title: 'sla' });
    await documentDecreeCorrespondenceApi.createDdcEvidence({ title: 'evidence' });
    await documentDecreeCorrespondenceApi.createDdcAttachmentMetadata({ title: 'attachment' });
    await documentDecreeCorrespondenceApi.createDdcAuditEvent({ title: 'audit' });
    await documentDecreeCorrespondenceApi.createDdcArchiveReadiness({ title: 'archive' });
    await documentDecreeCorrespondenceApi.createDdcRetentionMetadata({ title: 'retention' });

    expect(client.apiPost).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.executionControlMetadata, { title: 'control' });
    expect(client.apiPost).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.slaDeadlines, { title: 'sla' });
    expect(client.apiPost).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.evidence, { title: 'evidence' });
    expect(client.apiPost).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.attachmentsMetadata, { title: 'attachment' });
    expect(client.apiPost).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.auditEvents, { title: 'audit' });
    expect(client.apiPost).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.archiveReadiness, { title: 'archive' });
    expect(client.apiPost).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.retentionMetadata, { title: 'retention' });
  });

  it('maps readiness bridge and limitations post helpers', async () => {
    await documentDecreeCorrespondenceApi.createDdcSignatureReadinessEvidence({ title: 'signature' });
    await documentDecreeCorrespondenceApi.createDdcDeliveryReadinessEvidence({ title: 'delivery' });
    await documentDecreeCorrespondenceApi.createDdcBridgeExecutive({ title: 'executive' });
    await documentDecreeCorrespondenceApi.createDdcBridgeAssignments({ title: 'assignments' });
    await documentDecreeCorrespondenceApi.createDdcLimitation({ title: 'limitation' });

    expect(client.apiPost).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.signatureReadinessEvidence, { title: 'signature' });
    expect(client.apiPost).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.deliveryReadinessEvidence, { title: 'delivery' });
    expect(client.apiPost).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.bridgesExecutive, { title: 'executive' });
    expect(client.apiPost).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.bridgesAssignments, { title: 'assignments' });
    expect(client.apiPost).toHaveBeenCalledWith(DOCUMENT_DECREE_CORRESPONDENCE_API_PATHS.limitations, { title: 'limitation' });
  });

  it('does not expose forbidden executor helpers', () => {
    expect('signDocument' in documentDecreeCorrespondenceApi).toBe(false);
    expect('issueOfficialDecree' in documentDecreeCorrespondenceApi).toBe(false);
    expect('autoApproveDecree' in documentDecreeCorrespondenceApi).toBe(false);
    expect('submitToMinistry' in documentDecreeCorrespondenceApi).toBe(false);
    expect('confirmLegalArchive' in documentDecreeCorrespondenceApi).toBe(false);
    expect('hiddenDepartmentScore' in documentDecreeCorrespondenceApi).toBe(false);
  });
});
