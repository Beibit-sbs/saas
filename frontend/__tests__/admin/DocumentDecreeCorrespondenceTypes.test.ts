import { describe, expect, it } from 'vitest';
import {
  automaticDecreeApprovalEnabled,
  automaticDocumentSigningEnabled,
  automaticRectorDecisionEnabled,
  DOCUMENT_DECREE_CORRESPONDENCE_API_BASE,
  DOCUMENT_DECREE_CORRESPONDENCE_BACKEND_ROUTE_COUNT,
  DOCUMENT_DECREE_CORRESPONDENCE_DATA_SOURCE,
  DOCUMENT_DECREE_CORRESPONDENCE_DASHBOARD_WIDGETS,
  DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_COUNT,
  DOCUMENT_DECREE_CORRESPONDENCE_PLANNED_ROUTE_COUNT,
  DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_COUNT,
  DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY,
  DOCUMENT_DECREE_CORRESPONDENCE_ROUTES,
  DOCUMENT_DECREE_CORRESPONDENCE_RUNTIME_MODE,
  DOCUMENT_DECREE_CORRESPONDENCE_SAFETY_FLAGS,
  DOCUMENT_DECREE_CORRESPONDENCE_SOURCE_BACKEND_B1_COMMIT,
  DOCUMENT_DECREE_CORRESPONDENCE_SOURCE_BACKEND_RUNTIME_COMMIT,
  DOCUMENT_DECREE_CORRESPONDENCE_WORKFLOWS,
  externalSubmissionEnabled,
  fakeArchiveLegalRecord,
  fakeDecrees,
  fakeDeliveryConfirmations,
  fakeDocuments,
  fakeSignatures,
  hiddenScorePresent,
  humanReviewRequired,
  officialLegalEffect,
} from '@/modules/document-decree-correspondence/constants';
import type { DdcOverview, DdcSafetyFlags } from '@/modules/document-decree-correspondence/types';

describe('Document Decree Correspondence types', () => {
  it('exports the expected module constants', () => {
    expect(DOCUMENT_DECREE_CORRESPONDENCE_API_BASE).toBe('/api/admin/document-decree-correspondence');
    expect(DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_FAMILY).toBe('/console/document-decree-correspondence');
    expect(DOCUMENT_DECREE_CORRESPONDENCE_PLANNED_ROUTE_COUNT).toBe(23);
    expect(DOCUMENT_DECREE_CORRESPONDENCE_ROUTE_COUNT).toBe(23);
    expect(DOCUMENT_DECREE_CORRESPONDENCE_BACKEND_ROUTE_COUNT).toBe(53);
    expect(DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_COUNT).toBe(50);
    expect(DOCUMENT_DECREE_CORRESPONDENCE_RUNTIME_MODE).toBe('METADATA_EVIDENCE_READINESS_AUDIT_ARCHIVE_HUMAN_REVIEW_ONLY');
    expect(DOCUMENT_DECREE_CORRESPONDENCE_SOURCE_BACKEND_RUNTIME_COMMIT).toBe('b9a6188');
    expect(DOCUMENT_DECREE_CORRESPONDENCE_SOURCE_BACKEND_B1_COMMIT).toBe('d483c59');
    expect(DOCUMENT_DECREE_CORRESPONDENCE_DATA_SOURCE).toBe('computed_from_document_decree_correspondence_metadata');
  });

  it('keeps route inventory explicit with first and last routes', () => {
    expect(DOCUMENT_DECREE_CORRESPONDENCE_ROUTES).toHaveLength(23);
    expect(DOCUMENT_DECREE_CORRESPONDENCE_ROUTES[0]?.path).toBe('/console/document-decree-correspondence');
    expect(DOCUMENT_DECREE_CORRESPONDENCE_ROUTES.at(-1)?.path).toBe('/console/document-decree-correspondence/limitations');
  });

  it('defines the expected widget and workflow counts', () => {
    expect(DOCUMENT_DECREE_CORRESPONDENCE_DASHBOARD_WIDGETS).toHaveLength(12);
    expect(DOCUMENT_DECREE_CORRESPONDENCE_WORKFLOWS).toHaveLength(10);
  });

  it('models explicit safety flags with human review true', () => {
    const flags: DdcSafetyFlags = {
      fake_documents: false,
      fake_decrees: false,
      fake_signatures: false,
      fake_delivery_confirmations: false,
      fake_archive_legal_record: false,
      official_legal_effect: false,
      external_submission_enabled: false,
      automatic_rector_decision_enabled: false,
      automatic_decree_approval_enabled: false,
      automatic_document_signing_enabled: false,
      hidden_score_present: false,
      human_review_required: true,
      incomplete_data: true,
      limitations: ['runtime metadata only'],
    };

    expect(flags.fake_documents).toBe(false);
    expect(flags.official_legal_effect).toBe(false);
    expect(flags.human_review_required).toBe(true);
  });

  it('models overview without legal-effect fields', () => {
    const overview: DdcOverview = {
      ...DOCUMENT_DECREE_CORRESPONDENCE_SAFETY_FLAGS,
      tenant_id: 1,
      module: 'document-decree-correspondence',
      product_vertical: 'Document / Decree / Correspondence Suite',
      runtime_mode: DOCUMENT_DECREE_CORRESPONDENCE_RUNTIME_MODE,
      table_count: 26,
      route_count: 53,
      permission_count: 50,
      planned_route_count: 23,
      backend_route_count: 53,
      backend_permission_count: 50,
      boundary_summary: { no_legal_effect: true },
    };

    expect(overview.permission_count).toBe(50);
    expect(overview.backend_route_count).toBe(53);
  });

  it('keeps top-level boolean boundaries explicit', () => {
    expect(fakeDocuments).toBe(false);
    expect(fakeDecrees).toBe(false);
    expect(fakeSignatures).toBe(false);
    expect(fakeDeliveryConfirmations).toBe(false);
    expect(fakeArchiveLegalRecord).toBe(false);
  });

  it('keeps execution/autonomy boundaries explicit', () => {
    expect(officialLegalEffect).toBe(false);
    expect(externalSubmissionEnabled).toBe(false);
    expect(automaticRectorDecisionEnabled).toBe(false);
    expect(automaticDecreeApprovalEnabled).toBe(false);
    expect(automaticDocumentSigningEnabled).toBe(false);
    expect(hiddenScorePresent).toBe(false);
    expect(humanReviewRequired).toBe(true);
  });

  it('includes safety flags object for incomplete data support', () => {
    expect(DOCUMENT_DECREE_CORRESPONDENCE_SAFETY_FLAGS.incomplete_data).toBe(true);
    expect(DOCUMENT_DECREE_CORRESPONDENCE_SAFETY_FLAGS.limitations.length).toBeGreaterThan(0);
  });
});
