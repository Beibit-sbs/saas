import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import {
  DOCUMENT_DECREE_CORRESPONDENCE_WORKFLOWS,
  DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES,
} from '@/modules/document-decree-correspondence/constants';
import {
  buildDdcPageModel,
  DocumentDecreeCorrespondencePage,
  getDdcRouteDefinition,
} from '@/modules/document-decree-correspondence/pages';

describe('Document Decree Correspondence workflows', () => {
  it('exports the expected workflow count', () => {
    expect(DOCUMENT_DECREE_CORRESPONDENCE_WORKFLOWS).toHaveLength(10);
  });

  it('keeps workflow keys unique', () => {
    const keys = DOCUMENT_DECREE_CORRESPONDENCE_WORKFLOWS.map((workflow) => workflow.key);
    expect(new Set(keys).size).toBe(keys.length);
  });

  it('builds page model for workflow route with matching route key', () => {
    const model = buildDdcPageModel('decrees');
    expect(model.route.key).toBe('decrees');
    expect(model.workflows.length).toBeGreaterThan(0);
  });

  it('retrieves route definitions by key', () => {
    expect(getDdcRouteDefinition('archive').path).toBe('/console/document-decree-correspondence/archive');
    expect(getDdcRouteDefinition('bridges').requiredPermission).toBe(DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.bridgesExecutiveRead);
  });

  it('renders workflow timeline content in page runtime', () => {
    render(<DocumentDecreeCorrespondencePage routeKey="routing" userPermissions={[DOCUMENT_DECREE_CORRESPONDENCE_PERMISSION_VALUES.documentRoutingRead]} />);
    expect(screen.getByTestId('ddc-audit-timeline')).toBeInTheDocument();
  });

  it('throws on unknown route definition request', () => {
    expect(() => getDdcRouteDefinition('unknown' as never)).toThrowError('Unknown DDC route key: unknown');
  });
});
