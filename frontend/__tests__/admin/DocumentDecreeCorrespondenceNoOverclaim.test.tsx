import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import {
  DOCUMENT_DECREE_CORRESPONDENCE_FORBIDDEN_LABELS,
} from '@/modules/document-decree-correspondence/boundaryLabels';
import {
  DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES,
  DOCUMENT_DECREE_CORRESPONDENCE_ROUTES,
} from '@/modules/document-decree-correspondence/constants';
import { documentDecreeCorrespondenceApi } from '@/modules/document-decree-correspondence/api';
import { DocumentDecreeCorrespondencePage } from '@/modules/document-decree-correspondence/pages';

describe('Document Decree Correspondence no-overclaim boundaries', () => {
  it('does not render forbidden labels on overview page', () => {
    render(<DocumentDecreeCorrespondencePage routeKey="overview" userPermissions={[DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.overviewRead]} />);

    for (const label of DOCUMENT_DECREE_CORRESPONDENCE_FORBIDDEN_LABELS) {
      expect(screen.queryByText(label)).not.toBeInTheDocument();
    }
  });

  it('does not render forbidden labels on bridges page', () => {
    render(<DocumentDecreeCorrespondencePage routeKey="bridges" userPermissions={[DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.bridgesExecutiveRead]} />);

    for (const label of DOCUMENT_DECREE_CORRESPONDENCE_FORBIDDEN_LABELS) {
      expect(screen.queryByText(label)).not.toBeInTheDocument();
    }
  });

  it('renders explicit no-overclaim footer assertions', () => {
    render(<DocumentDecreeCorrespondencePage routeKey="overview" userPermissions={[DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.overviewRead]} />);

    expect(screen.getByText('No sign document UI.')).toBeInTheDocument();
    expect(screen.getByText('No issue official decree UI.')).toBeInTheDocument();
    expect(screen.getByText('No production/sales/GCC/L5/L6 claim.')).toBeInTheDocument();
  });

  it('keeps route inventory fixed at 23 routes', () => {
    expect(DOCUMENT_DECREE_CORRESPONDENCE_ROUTES).toHaveLength(23);
  });

  it('does not expose forbidden API helper names', () => {
    expect('signDocument' in documentDecreeCorrespondenceApi).toBe(false);
    expect('issueOfficialDecree' in documentDecreeCorrespondenceApi).toBe(false);
    expect('approveDecreeAutomatically' in documentDecreeCorrespondenceApi).toBe(false);
    expect('submitToMinistry' in documentDecreeCorrespondenceApi).toBe(false);
    expect('confirmLegalArchive' in documentDecreeCorrespondenceApi).toBe(false);
  });

  it('does not render positive readiness overclaim labels', () => {
    render(<DocumentDecreeCorrespondencePage routeKey="limitations" userPermissions={[DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.limitationsRead]} />);

    expect(screen.queryByText('Production ready')).not.toBeInTheDocument();
    expect(screen.queryByText('Sales ready')).not.toBeInTheDocument();
    expect(screen.queryByText('GCC ready')).not.toBeInTheDocument();
    expect(screen.queryByText('L5/L6 ready')).not.toBeInTheDocument();
  });

  it('does not render fake execution labels', () => {
    render(<DocumentDecreeCorrespondencePage routeKey="limitations" userPermissions={[DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.limitationsRead]} />);

    expect(screen.queryByText('Fake signature')).not.toBeInTheDocument();
    expect(screen.queryByText('Fake decree')).not.toBeInTheDocument();
    expect(screen.queryByText('Fake document')).not.toBeInTheDocument();
  });

  it('does not render hidden-score labels', () => {
    render(<DocumentDecreeCorrespondencePage routeKey="limitations" userPermissions={[DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.limitationsRead]} />);

    expect(screen.queryByText('Hidden staff score')).not.toBeInTheDocument();
    expect(screen.queryByText('Hidden department score')).not.toBeInTheDocument();
  });
});
