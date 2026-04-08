import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import WorkflowsPage from "../../app/(admin)/console/workflows/page";

let allowAccess = true;
const useWorkflowInstancesMock = vi.fn();
const useWorkflowTasksMock = vi.fn();

vi.mock("../../modules/workflows-admin/hooks", () => ({
  useWorkflowInstances: (...args: unknown[]) => useWorkflowInstancesMock(...args),
  useWorkflowTasks: (...args: unknown[]) => useWorkflowTasksMock(...args),
  useStartWorkflow: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  PermissionGate: ({ children }: { children: React.ReactNode }) =>
    allowAccess ? <>{children}</> : null,
  RequirePermission: ({ children }: { children: React.ReactNode; permission: string }) =>
    allowAccess ? <>{children}</> : <div>Access Denied</div>,
  AccessDenied: ({ message }: { message?: string }) => (
    <div>{message ?? "Access Denied"}</div>
  ),
}));

vi.mock("../../shared/hooks/use-permissions", () => ({
  usePermissions: () => ({
    hasPermission: () => allowAccess,
    hasAnyPermission: () => allowAccess,
    roles: allowAccess ? ["admin"] : [],
  }),
}));

vi.mock("../../shared/hooks/use-mutation-feedback", () => ({
  useMutationFeedback: () => ({
    getHandlers: () => ({ onSuccess: vi.fn(), onError: vi.fn() }),
  }),
}));

vi.mock("../../app/components/LanguageProvider", async () => {
  const { en: commonEn } = await import("../../i18n/common/en");
  const { en: adminEn } = await import("../../i18n/admin/en");
  const dict = { ...commonEn, ...adminEn } as Record<string, string>;

  return {
    useLanguage: () => ({
      t: (key: string) => dict[key] ?? key,
    }),
  };
});

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
  usePathname: () => "/console/workflows",
  useSearchParams: () => new URLSearchParams(),
}));

describe("WorkflowsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
    useWorkflowInstancesMock.mockReturnValue({
      data: {
        total: 1,
        items: [
          {
            id: 1,
            entity_type: "application",
            entity_id: 42,
            status: "running",
            initiated_by: "admin",
            started_at: "2026-01-01T00:00:00Z",
          },
        ],
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    useWorkflowTasksMock.mockReturnValue({
      data: {
        total: 1,
        items: [
          {
            id: 10,
            workflow_instance_id: 1,
            title: "Review application",
            assignee_ref: "registrar",
            status: "open",
          },
        ],
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders workflows page with instances and tasks", () => {
    render(<WorkflowsPage />);
    expect(screen.getByTestId("workflows-page")).toBeInTheDocument();
    expect(screen.getByText("application")).toBeInTheDocument();
    expect(screen.getByText("Review application")).toBeInTheDocument();
  });

  it("shows start workflow form", () => {
    render(<WorkflowsPage />);
    expect(screen.getAllByText("Start workflow").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByLabelText("Workflow key")).toBeInTheDocument();
  });

  it("shows empty states when data absent", () => {
    useWorkflowInstancesMock.mockReturnValue({
      data: { total: 0, items: [] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    useWorkflowTasksMock.mockReturnValue({
      data: { total: 0, items: [] },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<WorkflowsPage />);
    expect(screen.getByText(/No workflow instances found\./i)).toBeInTheDocument();
  });
  it("shows access denied when read permission is missing", () => {
    allowAccess = false;
    render(<WorkflowsPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });

});
