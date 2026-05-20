/**
 * Tests: AssignmentTemplateManager (TemplatesPage)
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('@/shared/auth/permission-gate', () => ({
  RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  PermissionGate: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({}),
}));

vi.mock('@/modules/rector-assignments/hooks', () => ({
  useRectorAssignmentTemplates: vi.fn(),
  useCreateTemplate: vi.fn(),
  useUpdateTemplate: vi.fn(),
}));

import * as hooks from '@/modules/rector-assignments/hooks';
import TemplatesPage from '@/app/(admin)/console/rector-assignments/templates/page';

function stubHooks(templates: unknown[] = []) {
  vi.mocked(hooks.useRectorAssignmentTemplates).mockReturnValue({
    data: templates,
    isLoading: false,
    isError: false,
  } as any);
  vi.mocked(hooks.useCreateTemplate).mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue({}),
    isPending: false,
  } as any);
  vi.mocked(hooks.useUpdateTemplate).mockReturnValue({
    mutateAsync: vi.fn().mockResolvedValue({}),
    isPending: false,
  } as any);
}

beforeEach(() => {
  vi.clearAllMocks();
  stubHooks();
});

describe('TemplatesPage', () => {
  it('shows empty state when no templates', () => {
    render(<TemplatesPage />);
    expect(screen.getByTestId('empty-templates')).toBeInTheDocument();
  });

  it('renders template rows', () => {
    stubHooks([
      {
        id: '1',
        name: 'Weekly Inspection',
        default_priority: 'HIGH',
        default_recurrence_type: 'WEEKLY',
        is_active: true,
        template_body: 'Inspect all facilities.',
      },
    ]);
    render(<TemplatesPage />);
    expect(screen.getByTestId('template-row-1')).toBeInTheDocument();
    expect(screen.getByText('Weekly Inspection')).toBeInTheDocument();
  });

  it('clicking New Template button shows form panel', async () => {
    const user = userEvent.setup();
    render(<TemplatesPage />);
    await user.click(screen.getByTestId('new-template-btn'));
    expect(screen.getByTestId('template-form-panel')).toBeInTheDocument();
  });

  it('shows validation error when template name is empty', async () => {
    const user = userEvent.setup();
    render(<TemplatesPage />);
    await user.click(screen.getByTestId('new-template-btn'));
    await user.click(screen.getByTestId('save-template-btn'));
    expect(screen.getByTestId('template-form-error')).toBeInTheDocument();
    expect(screen.getByText(/name is required/i)).toBeInTheDocument();
  });

  it('cancel button hides form panel', async () => {
    const user = userEvent.setup();
    render(<TemplatesPage />);
    await user.click(screen.getByTestId('new-template-btn'));
    expect(screen.getByTestId('template-form-panel')).toBeInTheDocument();
    await user.click(screen.getByTestId('cancel-template-btn'));
    expect(screen.queryByTestId('template-form-panel')).not.toBeInTheDocument();
  });

  it('clicking Edit shows form panel with existing data', async () => {
    stubHooks([
      {
        id: '2',
        name: 'Monthly Review',
        default_priority: 'NORMAL',
        default_recurrence_type: 'MONTHLY',
        is_active: true,
        template_body: null,
        description: null,
      },
    ]);
    const user = userEvent.setup();
    render(<TemplatesPage />);
    await user.click(screen.getByTestId('edit-template-2'));
    expect(screen.getByTestId('template-form-panel')).toBeInTheDocument();
    expect(screen.getByTestId('tmpl-name-input')).toHaveValue('Monthly Review');
  });
});
