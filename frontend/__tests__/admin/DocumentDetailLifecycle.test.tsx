import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  DocumentDetailHeader,
  DocumentLifecycleTimeline,
  DocumentReviewPanel,
  DocumentVersionTimeline,
} from '@/modules/document-workflow/components/pages';
import type { DocumentDetail, DocumentStatusHistory } from '@/modules/document-workflow/types';

const DOCUMENT: DocumentDetail = {
  id: 5,
  tenant_id: 1,
  title: 'Annual Senate Report',
  document_type: 'REPORT',
  status: 'UNDER_REVIEW',
  registry_number: 'DOC-2026-005',
  registry_date: '2026-05-21T00:00:00Z',
  source_department_id: 11,
  owner_user_id: 7,
  created_by_user_id: 1,
  linked_assignment_id: 91,
  linked_decree_id: null,
  version: 3,
  created_at: '2026-05-20T00:00:00Z',
  updated_at: '2026-05-21T00:00:00Z',
  archived_at: null,
  versions: [
    {
      id: 1,
      document_id: 5,
      version_number: 1,
      title: 'Draft version',
      body_text: 'Initial body',
      metadata_json: {},
      created_by_user_id: 1,
      created_at: '2026-05-20T00:00:00Z',
    },
  ],
  reviews: [
    {
      id: 1,
      document_id: 5,
      reviewer_user_id: 8,
      decision: 'APPROVED',
      comment: 'Looks good',
      created_at: '2026-05-21T00:00:00Z',
    },
  ],
  assignment_links: [],
};

const HISTORY: DocumentStatusHistory[] = [
  {
    id: 1,
    document_id: 5,
    from_status: 'REGISTERED',
    to_status: 'UNDER_REVIEW',
    actor_user_id: 8,
    reason: 'Sent for review',
    created_at: '2026-05-21T00:00:00Z',
  },
];

describe('document lifecycle components', () => {
  it('renders required document detail labels', () => {
    render(<DocumentDetailHeader document={DOCUMENT} />);
    expect(screen.getByTestId('signature-metadata-notice').textContent).toMatch(/signature metadata only/i);
    expect(screen.getByTestId('no-automatic-signing-notice').textContent).toMatch(/no automatic signing/i);
    expect(screen.getByTestId('registry-official-notice').textContent).toMatch(/registration workflow/i);
  });

  it('renders history, versions, and review records from backend data', () => {
    render(
      <div>
        <DocumentLifecycleTimeline history={HISTORY} />
        <DocumentVersionTimeline versions={DOCUMENT.versions} />
        <DocumentReviewPanel reviews={DOCUMENT.reviews} />
      </div>,
    );
    expect(screen.getByText(/sent for review/i)).toBeTruthy();
    expect(screen.getByTestId('document-version-1').textContent).toMatch(/draft version/i);
    expect(screen.getByText(/looks good/i)).toBeTruthy();
  });
});