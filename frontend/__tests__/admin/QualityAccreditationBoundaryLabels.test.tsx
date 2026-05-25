import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  QUALITY_ACCREDITATION_BOUNDARY_COPY,
  QUALITY_ACCREDITATION_BOUNDARY_LABELS,
} from '@/modules/quality-accreditation/boundaryLabels';
import { getQualityAccreditationBoundaryLabels } from '@/modules/quality-accreditation/guards';
import { QualityAccreditationBoundaryBanner } from '@/modules/quality-accreditation/pages';

describe('Quality Accreditation boundary labels', () => {
  it('renders all global boundary labels in the shared banner', () => {
    render(<QualityAccreditationBoundaryBanner labels={[...QUALITY_ACCREDITATION_BOUNDARY_COPY]} />);

    expect(screen.getByText(/metadata\/evidence-only quality foundation/i)).toBeInTheDocument();
    expect(screen.getByText(/accreditation readiness, not accreditation approval/i)).toBeInTheDocument();
    expect(screen.getByText(/no official accreditation approval/i)).toBeInTheDocument();
    expect(screen.getByText(/no fake accreditation evidence/i)).toBeInTheDocument();
    expect(screen.getByText(/no hidden program score/i)).toBeInTheDocument();
    expect(screen.getByText(/read-only-first bridge/i)).toBeInTheDocument();
  });

  it('returns page-specific labels for dashboard and standards', () => {
    const dashboardLabels = getQualityAccreditationBoundaryLabels('dashboard');
    const standardsLabels = getQualityAccreditationBoundaryLabels('standards');

    expect(dashboardLabels).toEqual(expect.arrayContaining([
      QUALITY_ACCREDITATION_BOUNDARY_LABELS.fakeMetricsFalse,
      QUALITY_ACCREDITATION_BOUNDARY_LABELS.fakeEvidenceFalse,
    ]));
    expect(standardsLabels.some((label) => /official compliance/i.test(label))).toBe(true);
  });

  it('returns page-specific labels for evidence, readiness, and committee', () => {
    expect(getQualityAccreditationBoundaryLabels('evidence').some((label) => /reviewed by humans/i.test(label))).toBe(true);
    expect(getQualityAccreditationBoundaryLabels('programReadiness').some((label) => /hidden program score/i.test(label))).toBe(true);
    expect(getQualityAccreditationBoundaryLabels('committee').some((label) => /human decisions only/i.test(label))).toBe(true);
  });

  it('keeps provider sync, hidden score, fake outputs, and official claims explicitly absent', () => {
    expect(QUALITY_ACCREDITATION_BOUNDARY_LABELS.noProviderSync).toMatch(/no provider sync/i);
    expect(QUALITY_ACCREDITATION_BOUNDARY_LABELS.noExternalDatabaseSync).toMatch(/no external database sync/i);
    expect(QUALITY_ACCREDITATION_BOUNDARY_LABELS.noOfficialMinistrySubmission).toMatch(/no official ministry submission/i);
    expect(QUALITY_ACCREDITATION_BOUNDARY_LABELS.noOfficialRankingClaim).toMatch(/no official ranking claim/i);
    expect(QUALITY_ACCREDITATION_BOUNDARY_LABELS.noHiddenFacultyScore).toMatch(/no hidden faculty score/i);
    expect(QUALITY_ACCREDITATION_BOUNDARY_LABELS.noFakeSurveyResults).toMatch(/no fake survey results/i);
  });
});