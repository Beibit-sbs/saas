import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES } from '@/modules/document-decree-correspondence/constants';
import {
  DdcArchiveReadinessBadge,
  DdcDeliveryReadinessBadge,
  DdcHumanReviewBadge,
  DdcSignatureReadinessBadge,
  DocumentDecreeCorrespondencePage,
} from '@/modules/document-decree-correspondence/pages';

describe('Document Decree Correspondence readiness and bridges', () => {
  it('renders human review badge', () => {
    render(<DdcHumanReviewBadge />);
    expect(screen.getByTestId('ddc-human-review-badge')).toBeInTheDocument();
  });

  it('renders signature readiness badge', () => {
    render(<DdcSignatureReadinessBadge />);
    expect(screen.getByTestId('ddc-signature-readiness-badge')).toBeInTheDocument();
  });

  it('renders delivery readiness badge', () => {
    render(<DdcDeliveryReadinessBadge />);
    expect(screen.getByTestId('ddc-delivery-readiness-badge')).toBeInTheDocument();
  });

  it('renders archive readiness badge', () => {
    render(<DdcArchiveReadinessBadge />);
    expect(screen.getByTestId('ddc-archive-readiness-badge')).toBeInTheDocument();
  });

  it('renders bridge cards on bridges page', () => {
    render(<DocumentDecreeCorrespondencePage routeKey="bridges" userPermissions={[DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.bridgesExecutiveRead]} />);
    expect(screen.getByTestId('ddc-bridge-executive')).toBeInTheDocument();
    expect(screen.getByTestId('ddc-bridge-assignments')).toBeInTheDocument();
    expect(screen.getByTestId('ddc-bridge-archive-readiness')).toBeInTheDocument();
  });

  it('renders readiness badges on dedicated pages', () => {
    render(<DocumentDecreeCorrespondencePage routeKey="signature-readiness" userPermissions={[DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.signatureReadinessRead]} />);
    render(<DocumentDecreeCorrespondencePage routeKey="delivery-readiness" userPermissions={[DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.deliveryReadinessRead]} />);

    expect(screen.getAllByTestId('ddc-signature-readiness-badge').length).toBeGreaterThan(0);
    expect(screen.getAllByTestId('ddc-delivery-readiness-badge').length).toBeGreaterThan(0);
  });
});
