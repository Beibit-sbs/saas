import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  HumanReviewRequiredBadge,
  NoAutomatedDecisionBadge,
  NoHiddenScoreBadge,
  ProviderNotEnabledBadge,
  StudentLifecycleBoundaryBanner,
  StudentLifecycleLimitationsPanel,
  SupportVisibilityOnlyBadge,
  UnofficialPreviewBadge,
} from '@/modules/student-lifecycle/components';

describe('Student Lifecycle boundary labels', () => {
  it('renders the boundary banner labels', () => {
    render(
      <StudentLifecycleBoundaryBanner
        labels={['Human review required', 'No automated decision is made', 'Provider integration not enabled']}
      />,
    );

    expect(screen.getByText(/human review required/i)).toBeInTheDocument();
    expect(screen.getByText(/no automated decision is made/i)).toBeInTheDocument();
    expect(screen.getByText(/provider integration not enabled/i)).toBeInTheDocument();
  });

  it('renders the focused runtime badges', () => {
    render(
      <div>
        <HumanReviewRequiredBadge />
        <NoAutomatedDecisionBadge />
        <UnofficialPreviewBadge />
        <ProviderNotEnabledBadge />
        <NoHiddenScoreBadge />
        <SupportVisibilityOnlyBadge />
      </div>,
    );

    expect(screen.getByText(/human review required/i)).toBeInTheDocument();
    expect(screen.getByText(/no automated decision is made/i)).toBeInTheDocument();
    expect(screen.getByText(/unofficial preview/i)).toBeInTheDocument();
    expect(screen.getByText(/provider integration not enabled/i)).toBeInTheDocument();
    expect(screen.getByText(/no hidden risk score/i)).toBeInTheDocument();
    expect(screen.getByText(/support visibility only/i)).toBeInTheDocument();
  });

  it('renders known limitations when present', () => {
    render(<StudentLifecycleLimitationsPanel limitations={['Metadata only', 'Incomplete data']} />);
    expect(screen.getByText(/metadata only/i)).toBeInTheDocument();
    expect(screen.getByText(/incomplete data/i)).toBeInTheDocument();
  });
});