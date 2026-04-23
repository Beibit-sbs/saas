/**
 * Contracts & Legal Repository Page — Unit Tests
 * Validates contract registry dashboard and workflow list rendering
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ContractsLegalRepositoryPage from '@/app/(admin)/console/contracts-legal-repository/page';

vi.mock('@/shared/auth/permission-gate', () => ({
  RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('@/shared/ui/page-header', () => ({
  PageHeader: ({ title }: { title: string }) => <h1>{title}</h1>,
}));

vi.mock('@/shared/ui/page-states', () => ({
  LoadingState: ({ message }: { message: string }) => <div>{message}</div>,
  ErrorState: ({ message }: { message: string }) => <div>{message}</div>,
}));

vi.mock('@/shared/ui/badge', () => ({
  Badge: ({ children, variant }: { children: React.ReactNode; variant?: string }) => (
    <span data-variant={variant}>{children}</span>
  ),
}));

vi.mock('@/modules/contracts-legal-repository/hooks', () => ({
  useContractDashboardSummary: vi.fn(),
  useContractsList: vi.fn(),
}));

import * as hooks from '@/modules/contracts-legal-repository/hooks';

const DEFAULT_DASHBOARD = {
  total_contracts: 42,
  status_breakdown: {
    draft: 4,
    in_review: 6,
    approved: 8,
    active: 18,
    expiring: 3,
    expired: 2,
    terminated: 1,
  },
  expiring_30_days: 3,
  high_risk_count: 5,
  total_active_value: 12800000,
  last_updated: '2026-04-22T10:00:00Z',
};

const DEFAULT_CONTRACTS = [
  {
    contract_id: 'c-001',
    contract_number: 'CTR-2026-001',
    title: 'Cloud Infrastructure Agreement',
    type: 'service' as const,
    status: 'active' as const,
    owner_name: 'Jane Doe',
    counterparty: 'SkyCompute LLC',
    end_date: '2027-03-31',
    risk_level: 'medium' as const,
    updated_at: '2026-04-20T12:30:00Z',
  },
  {
    contract_id: 'c-002',
    contract_number: 'CTR-2026-002',
    title: 'Laboratory Equipment Supply',
    type: 'vendor' as const,
    status: 'in_review' as const,
    owner_name: 'John Smith',
    counterparty: 'LabTech Corp',
    end_date: '2026-12-15',
    risk_level: 'high' as const,
    updated_at: '2026-04-21T16:10:00Z',
  },
];

describe('ContractsLegalRepositoryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    stubDefaults();
  });

  function stubDefaults() {
    vi.mocked(hooks.useContractDashboardSummary).mockReturnValue({
      data: DEFAULT_DASHBOARD,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    vi.mocked(hooks.useContractsList).mockReturnValue({
      data: DEFAULT_CONTRACTS,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);
  }

  it('renders page heading', () => {
    render(<ContractsLegalRepositoryPage />);
    expect(screen.getByText('Contracts & Legal Repository')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    vi.mocked(hooks.useContractDashboardSummary).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<ContractsLegalRepositoryPage />);
    expect(screen.getByText('Loading contracts dashboard...')).toBeInTheDocument();
  });

  it('shows error state', () => {
    vi.mocked(hooks.useContractDashboardSummary).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      refetch: vi.fn(),
    } as any);

    render(<ContractsLegalRepositoryPage />);
    expect(screen.getByText('Failed to load contracts data')).toBeInTheDocument();
  });

  it('renders dashboard metrics', () => {
    render(<ContractsLegalRepositoryPage />);

    expect(screen.getByTestId('total-contracts')).toHaveTextContent('42');
    expect(screen.getByTestId('expiring-30-days')).toHaveTextContent('3');
    expect(screen.getByTestId('high-risk-count')).toHaveTextContent('5');
    expect(screen.getByTestId('total-active-value')).toHaveTextContent('12,800,000');
    expect(screen.getByTestId('active-count')).toHaveTextContent('18');
  });

  it('shows expiry alert when expiring contracts exist', () => {
    render(<ContractsLegalRepositoryPage />);
    expect(screen.getByTestId('expiry-alert-section')).toBeInTheDocument();
  });

  it('hides expiry alert when no expiring contracts', () => {
    vi.mocked(hooks.useContractDashboardSummary).mockReturnValue({
      data: { ...DEFAULT_DASHBOARD, expiring_30_days: 0 },
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<ContractsLegalRepositoryPage />);
    expect(screen.queryByTestId('expiry-alert-section')).not.toBeInTheDocument();
  });

  it('renders status distribution section', () => {
    render(<ContractsLegalRepositoryPage />);
    const statusSection = screen.getByTestId('status-distribution-section');
    expect(statusSection).toBeInTheDocument();
    expect(within(statusSection).getByText('In Review')).toBeInTheDocument();
    expect(within(statusSection).getByText('Expired')).toBeInTheDocument();
  });

  it('updates status filter', async () => {
    const user = userEvent.setup();
    render(<ContractsLegalRepositoryPage />);

    const statusFilter = screen.getByTestId('status-filter');
    await user.selectOptions(statusFilter, 'active');
    expect(statusFilter).toHaveValue('active');
  });

  it('updates type filter', async () => {
    const user = userEvent.setup();
    render(<ContractsLegalRepositoryPage />);

    const typeFilter = screen.getByTestId('type-filter');
    await user.selectOptions(typeFilter, 'service');
    expect(typeFilter).toHaveValue('service');
  });

  it('renders contract table rows', () => {
    render(<ContractsLegalRepositoryPage />);

    expect(screen.getByTestId('contract-row-c-001')).toBeInTheDocument();
    expect(screen.getByTestId('contract-row-c-002')).toBeInTheDocument();
    expect(screen.getByText('CTR-2026-001')).toBeInTheDocument();
    expect(screen.getByText('CTR-2026-002')).toBeInTheDocument();
  });

  it('renders status badge variants', () => {
    render(<ContractsLegalRepositoryPage />);

    const activeBadge = screen.getByTestId('contract-row-c-001').querySelector('span[data-variant]');
    expect(activeBadge).toHaveAttribute('data-variant', 'success');

    const reviewBadge = screen.getByTestId('contract-row-c-002').querySelector('span[data-variant]');
    expect(reviewBadge).toHaveAttribute('data-variant', 'warning');
  });

  it('renders risk style marker', () => {
    render(<ContractsLegalRepositoryPage />);

    const highRisk = screen.getByTestId('risk-c-002');
    expect(highRisk).toHaveClass('text-orange-700');
  });

  it('shows list loading state', () => {
    vi.mocked(hooks.useContractsList).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<ContractsLegalRepositoryPage />);
    expect(screen.getByText('Loading contracts...')).toBeInTheDocument();
  });

  it('shows empty state when list is empty', () => {
    vi.mocked(hooks.useContractsList).mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<ContractsLegalRepositoryPage />);
    expect(screen.getByText('No contracts found')).toBeInTheDocument();
  });

  it('renders last updated footer', () => {
    render(<ContractsLegalRepositoryPage />);
    expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
  });
});
