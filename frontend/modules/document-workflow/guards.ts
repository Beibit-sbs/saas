import {
  CorrespondenceDirection,
  DashboardSummary,
  DecreeStatus,
  DocumentStatus,
} from './types';

export function assertTrustedDocumentDashboard(dashboard: DashboardSummary) {
  if (dashboard.fake_metrics !== false) {
    throw new Error('Dashboard data could not be verified: fake_metrics=true');
  }
  if (dashboard.data_source !== 'computed_from_documents') {
    throw new Error(
      `Dashboard data source mismatch: expected computed_from_documents, received ${dashboard.data_source}`,
    );
  }
}

export function canRegisterDocument(status?: string) {
  return status === DocumentStatus.DRAFT;
}

export function canSubmitDocumentReview(status?: string) {
  return status === DocumentStatus.REGISTERED || status === DocumentStatus.RETURNED_FOR_REVISION;
}

export function canReturnDocument(status?: string) {
  return status === DocumentStatus.UNDER_REVIEW;
}

export function canApproveDocument(status?: string) {
  return status === DocumentStatus.UNDER_REVIEW;
}

export function canRecordDocumentSignedMetadata(status?: string) {
  return status === DocumentStatus.APPROVED;
}

export function canArchiveDocument(status?: string) {
  return Boolean(status && status !== DocumentStatus.ARCHIVED);
}

export function canStartDecreeLegalReview(status?: string) {
  return status === DecreeStatus.DRAFT_ORDER;
}

export function canApproveDecreeSigning(status?: string) {
  return status === DecreeStatus.RECTOR_REVIEW || status === DecreeStatus.LEGAL_REVIEW;
}

export function canRecordDecreeSignedMetadata(status?: string) {
  return status === DecreeStatus.APPROVED_FOR_SIGNING;
}

export function canRegisterDecree(status?: string) {
  return status === DecreeStatus.SIGNED;
}

export function canArchiveDecree(status?: string) {
  return Boolean(status && status !== DecreeStatus.ARCHIVED);
}

export function canRecordOutgoingSentMetadata(direction?: string, status?: string) {
  return direction === CorrespondenceDirection.OUTGOING && status === 'REGISTERED';
}

export function isArchiveRecord(archivedAt?: string | null) {
  return Boolean(archivedAt);
}

export function formatUnavailableMetric(value?: number | null) {
  return value === undefined ? 'Unavailable' : value === null ? 'Unavailable' : String(value);
}