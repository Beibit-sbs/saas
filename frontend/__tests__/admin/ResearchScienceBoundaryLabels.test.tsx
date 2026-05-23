import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  RESEARCH_SCIENCE_BOUNDARY_COPY,
  RESEARCH_SCIENCE_BOUNDARY_LABELS,
} from '@/modules/research-science/boundaryLabels';
import { ResearchScienceBoundaryBanner } from '@/modules/research-science/pages';
import { getResearchScienceBoundaryLabels } from '@/modules/research-science/guards';

describe('Research Science boundary labels', () => {
  it('renders all global boundary labels in the shared banner', () => {
    render(<ResearchScienceBoundaryBanner labels={[...RESEARCH_SCIENCE_BOUNDARY_COPY]} />);

    expect(screen.getByText(/metadata-only research foundation/i)).toBeInTheDocument();
    expect(screen.getByText(/evidence metadata only/i)).toBeInTheDocument();
    expect(screen.getByText(/no fake publications/i)).toBeInTheDocument();
    expect(screen.getByText(/no fake conference certificates/i)).toBeInTheDocument();
    expect(screen.getByText(/no fake grant evidence/i)).toBeInTheDocument();
    expect(screen.getByText(/no hidden researcher score/i)).toBeInTheDocument();
    expect(screen.getByText(/no official verification/i)).toBeInTheDocument();
    expect(screen.getByText(/read-only-first bridge/i)).toBeInTheDocument();
  });

  it('returns page-specific labels for publications and conferences', () => {
    const publicationLabels = getResearchScienceBoundaryLabels('publications');
    const conferenceLabels = getResearchScienceBoundaryLabels('conferences');

    expect(publicationLabels).toEqual(expect.arrayContaining([
      RESEARCH_SCIENCE_BOUNDARY_LABELS.noFakePublications,
      RESEARCH_SCIENCE_BOUNDARY_LABELS.noCitationScore,
    ]));
    expect(conferenceLabels.some((label) => /official certificates/i.test(label))).toBe(true);
  });

  it('returns page-specific labels for grants, ethics, and evidence', () => {
    expect(getResearchScienceBoundaryLabels('grants').some((label) => /does not submit grant applications/i.test(label))).toBe(true);
    expect(getResearchScienceBoundaryLabels('ethics').some((label) => /human committee review/i.test(label))).toBe(true);
    expect(getResearchScienceBoundaryLabels('evidence').some((label) => /metadata-only unless reviewed by humans/i.test(label))).toBe(true);
  });

  it('keeps provider sync, hidden score, and official verification explicitly absent', () => {
    expect(RESEARCH_SCIENCE_BOUNDARY_LABELS.noProviderSync).toMatch(/no provider sync/i);
    expect(RESEARCH_SCIENCE_BOUNDARY_LABELS.noExternalDatabaseSync).toMatch(/no external database sync/i);
    expect(RESEARCH_SCIENCE_BOUNDARY_LABELS.noOfficialVerification).toMatch(/no official verification/i);
    expect(RESEARCH_SCIENCE_BOUNDARY_LABELS.noHiddenFacultyScore).toMatch(/no hidden faculty score/i);
    expect(RESEARCH_SCIENCE_BOUNDARY_LABELS.noHiddenStudentResearchScore).toMatch(/no hidden student research score/i);
  });
});