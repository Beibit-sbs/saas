import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BoundaryBanner } from '@/modules/academic-operations/components';
import { ACADEMIC_OPERATIONS_BOUNDARY_LABELS } from '@/modules/academic-operations/boundaryLabels';
import { getAcademicOperationsBoundaryLabels } from '@/modules/academic-operations/guards';

describe('Academic Operations boundary labels', () => {
  it('renders the gradebook and no-overclaim labels', () => {
    render(<BoundaryBanner labels={getAcademicOperationsBoundaryLabels('gradebook')} />);

    expect(screen.getByText(/no official grade publication/i)).toBeInTheDocument();
    expect(screen.getByText(/no automated grading/i)).toBeInTheDocument();
    expect(screen.getByText(/official grades/i)).toBeInTheDocument();
  });

  it('renders no hidden score, no provider sync, and matrix labels', () => {
    render(<BoundaryBanner labels={getAcademicOperationsBoundaryLabels('overview')} />);

    expect(screen.getByText(/matrix-guided: 467 planning rows/i)).toBeInTheDocument();
    expect(screen.getByText(/no provider sync/i)).toBeInTheDocument();
    expect(screen.getByText(/fake_metrics=false/i)).toBeInTheDocument();
  });

  it('keeps the shared boundary label constants explicit', () => {
    expect(ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noHiddenScore).toMatch(/no hidden score/i);
    expect(ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noOfficialTranscriptUpdate).toMatch(/no official transcript update/i);
  });
});