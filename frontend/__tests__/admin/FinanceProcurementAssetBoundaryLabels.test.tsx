import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import {
  FINANCE_PROCUREMENT_ASSET_BOUNDARY_COPY,
  FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS,
  FINANCE_PROCUREMENT_ASSET_FORBIDDEN_LABELS,
  FINANCE_PROCUREMENT_ASSET_PAGE_BOUNDARY_LABELS,
} from '@/modules/finance-procurement-asset/boundaryLabels';
import { FpaBoundaryBanner } from '@/modules/finance-procurement-asset/pages';

describe('Finance Procurement Asset boundary labels', () => {
  it('keeps the expected boundary copy inventory explicit', () => {
    expect(FINANCE_PROCUREMENT_ASSET_BOUNDARY_COPY).toContain(FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.metadataEvidenceOnlyFinanceFoundation);
    expect(FINANCE_PROCUREMENT_ASSET_BOUNDARY_COPY).toContain(FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noLiveBankIntegration);
    expect(FINANCE_PROCUREMENT_ASSET_BOUNDARY_COPY).toContain(FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noProductionReadyClaim);
  });

  it('covers all 23 routes with boundary labels', () => {
    expect(Object.keys(FINANCE_PROCUREMENT_ASSET_PAGE_BOUNDARY_LABELS)).toHaveLength(23);
    expect(FINANCE_PROCUREMENT_ASSET_PAGE_BOUNDARY_LABELS.overview).toContain('Metadata/evidence-only finance foundation');
    expect(FINANCE_PROCUREMENT_ASSET_PAGE_BOUNDARY_LABELS['payment-readiness']).toContain('Payment readiness only');
    expect(FINANCE_PROCUREMENT_ASSET_PAGE_BOUNDARY_LABELS['student-finance']).toContain('paymentExecutionEnabled=false');
  });

  it('renders boundary labels in the banner', () => {
    render(<FpaBoundaryBanner labels={FINANCE_PROCUREMENT_ASSET_PAGE_BOUNDARY_LABELS.overview} />);

    expect(screen.getByText('Metadata/evidence-only finance foundation')).toBeInTheDocument();
    expect(screen.getByText('Human review required')).toBeInTheDocument();
  });

  it('keeps forbidden visible action labels explicit for negative tests', () => {
    expect(FINANCE_PROCUREMENT_ASSET_FORBIDDEN_LABELS).toContain('Execute payment');
    expect(FINANCE_PROCUREMENT_ASSET_FORBIDDEN_LABELS).toContain('Connect bank live');
    expect(FINANCE_PROCUREMENT_ASSET_FORBIDDEN_LABELS).toContain('L5/L6 ready');
  });

  it('does not include forbidden positive labels in rendered approved boundary copy', () => {
    render(<FpaBoundaryBanner labels={FINANCE_PROCUREMENT_ASSET_BOUNDARY_COPY as unknown as string[]} />);

    for (const label of FINANCE_PROCUREMENT_ASSET_FORBIDDEN_LABELS) {
      expect(screen.queryByText(label)).not.toBeInTheDocument();
    }
  });

  it('keeps explicit false and incomplete-data labels available', () => {
    expect(FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.fakeMetricsFalse).toBe('fakeMetrics=false');
    expect(FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.liveBankSyncFalse).toBe('liveBankSync=false');
    expect(FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.incompleteDataSupported).toBe('Incomplete data supported');
  });
});
