import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DocumentAuditTrailPanel } from '@/modules/document-workflow/components/pages';
import type { DocumentAuditEvent } from '@/modules/document-workflow/types';

describe('DocumentAuditTrailPanel', () => {
  it('renders empty-state copy when there are no events', () => {
    render(<DocumentAuditTrailPanel events={[]} />);
    expect(screen.getByText(/no audit events/i)).toBeTruthy();
  });

  it('renders backend audit events without synthesizing extra actions', () => {
    const events: DocumentAuditEvent[] = [
      {
        id: 7,
        entity_type: 'document',
        entity_id: 5,
        event_type: 'DOCUMENT_REGISTERED',
        actor_user_id: 9,
        actor_role: 'chancellery_clerk',
        action: 'register',
        payload_json: {},
        created_at: '2026-05-21T00:00:00Z',
      },
    ];
    render(<DocumentAuditTrailPanel events={events} />);
    expect(screen.getByTestId('audit-event-7').textContent).toMatch(/document registered/i);
    expect(screen.getByTestId('audit-event-7').textContent).toMatch(/actor #9/i);
  });
});