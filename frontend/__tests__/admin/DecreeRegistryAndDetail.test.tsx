import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DecreeRegistryTable, SignedMetadataNotice } from '@/modules/document-workflow/components/pages';
import type { OrderDecree } from '@/modules/document-workflow/types';

describe('decree workflow components', () => {
  it('renders required anti-fake signing labels', () => {
    render(<SignedMetadataNotice />);
    expect(screen.getByTestId('signed-metadata-only-notice').textContent).toMatch(/signed metadata only/i);
    expect(screen.getByTestId('no-auto-signature-notice').textContent).toMatch(/no auto-signature/i);
    expect(screen.getByTestId('no-auto-approval-notice').textContent).toMatch(/no auto-approval/i);
  });

  it('renders decree registry rows from backend data', () => {
    const decrees: OrderDecree[] = [
      {
        id: 3,
        tenant_id: 1,
        title: 'Appointment Order',
        decree_type: 'ORDER',
        status: 'APPROVED_FOR_SIGNING',
        registry_number: null,
        registry_date: null,
        effective_date: '2026-05-21',
        signed_by_user_id: null,
        signed_at: null,
        linked_document_id: 5,
        linked_assignment_id: 8,
        created_by_user_id: 1,
        version: 2,
        created_at: '2026-05-21T00:00:00Z',
        updated_at: '2026-05-21T00:00:00Z',
        archived_at: null,
      },
    ];
    render(<DecreeRegistryTable decrees={decrees} />);
    expect(screen.getByTestId('decree-row-3').textContent).toMatch(/appointment order/i);
    expect(screen.getByTestId('decree-row-3').textContent).toMatch(/approved for signing/i);
  });
});