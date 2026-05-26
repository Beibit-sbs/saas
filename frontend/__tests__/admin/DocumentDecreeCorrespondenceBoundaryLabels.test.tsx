import { describe, expect, it } from 'vitest';
import {
  DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_COPY,
  DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_LABELS,
  DOCUMENT_DECREE_CORRESPONDENCE_FORBIDDEN_LABELS,
  DOCUMENT_DECREE_CORRESPONDENCE_PAGE_BOUNDARY_LABELS,
  getDdcBoundaryLabels,
} from '@/modules/document-decree-correspondence/boundaryLabels';

describe('Document Decree Correspondence boundary labels', () => {
  it('includes required explicit boundary labels', () => {
    expect(DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_COPY).toContain('Metadata/evidence-only document foundation');
    expect(DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_COPY).toContain('Human review required');
    expect(DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_COPY).toContain('No fake official documents');
    expect(DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_COPY).toContain('No fake decrees');
    expect(DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_COPY).toContain('No fake signatures');
  });

  it('includes no-overclaim labels for readiness and claims', () => {
    expect(DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_COPY).toContain('No production-ready claim');
    expect(DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_COPY).toContain('No sales-ready claim');
    expect(DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_COPY).toContain('No GCC-ready claim');
    expect(DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_COPY).toContain('Bridge-first / read-only-first');
  });

  it('tracks forbidden labels inventory', () => {
    expect(DOCUMENT_DECREE_CORRESPONDENCE_FORBIDDEN_LABELS).toContain('Sign document');
    expect(DOCUMENT_DECREE_CORRESPONDENCE_FORBIDDEN_LABELS).toContain('Issue official decree');
    expect(DOCUMENT_DECREE_CORRESPONDENCE_FORBIDDEN_LABELS).toContain('Submit to ministry');
    expect(DOCUMENT_DECREE_CORRESPONDENCE_FORBIDDEN_LABELS).toContain('Production ready');
    expect(DOCUMENT_DECREE_CORRESPONDENCE_FORBIDDEN_LABELS).toContain('L5/L6 ready');
  });

  it('provides route boundary map for all 23 routes', () => {
    expect(Object.keys(DOCUMENT_DECREE_CORRESPONDENCE_PAGE_BOUNDARY_LABELS)).toHaveLength(23);
    expect(getDdcBoundaryLabels('overview')).toContain(DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_LABELS.humanReviewRequired);
    expect(getDdcBoundaryLabels('archive')).toContain(DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_LABELS.archiveReadinessOnly);
  });

  it('keeps limitations route anchored to copy list', () => {
    expect(getDdcBoundaryLabels('limitations')).toEqual(DOCUMENT_DECREE_CORRESPONDENCE_BOUNDARY_COPY);
  });

  it('keeps false-flag labels explicit in overview boundaries', () => {
    const overview = getDdcBoundaryLabels('overview');
    expect(overview).toContain('fakeDocuments=false');
    expect(overview).toContain('fakeDecrees=false');
    expect(overview).toContain('fakeSignatures=false');
  });
});
