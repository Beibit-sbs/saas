import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import BrainPolicyPage from "../../app/(admin)/console/ai/brain/policy/page";

const useAdminAuthMock = vi.fn();
const useBrainPolicyProfileMock = vi.fn();
const useUpdateBrainPolicyProfileMock = vi.fn();

let allowAccess = true;

vi.mock("../../shared/auth/context", () => ({
  useAdminAuth: (...args: unknown[]) => useAdminAuthMock(...args),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: ReactNode }) =>
    allowAccess ? <>{children}</> : <div>Access Denied</div>,
}));

vi.mock("../../shared/ui/confirm-action-dialog", () => ({
  ConfirmActionDialog: ({ title }: { title: string }) => <div data-testid="confirm-dialog">{title}</div>,
}));

vi.mock("../../shared/ui/use-toast", () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

vi.mock("../../modules/brain-core/hooks", () => ({
  useBrainPolicyProfile: (...args: unknown[]) => useBrainPolicyProfileMock(...args),
  useUpdateBrainPolicyProfile: (...args: unknown[]) => useUpdateBrainPolicyProfileMock(...args),
}));

describe("BrainPolicyPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;

    useAdminAuthMock.mockReturnValue({
      user: { tenantId: 101, sub: "admin@tenant" },
    });

    useBrainPolicyProfileMock.mockReturnValue({
      data: {
        tenant_id: 101,
        autonomy_level: 2,
        require_approval_for_critical: true,
        default_approval_role: "dean_office",
        enable_ai_reasoning: false,
      },
      isPending: false,
      isError: false,
    });

    useUpdateBrainPolicyProfileMock.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
  });

  it("renders policy settings form with current profile values", () => {
    render(<BrainPolicyPage />);

    expect(screen.getByText("Brain Core — Policy Settings")).toBeInTheDocument();
    expect(screen.getByText("Autonomy Level")).toBeInTheDocument();
    expect(screen.getByText("Require approval for critical decisions")).toBeInTheDocument();
    expect(screen.getByText("Default approval role")).toBeInTheDocument();
    expect(screen.getByText("Enable AI reasoning (beta)")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save Policy" })).toBeInTheDocument();
  });

  it("renders Access Denied when permission is missing", () => {
    allowAccess = false;
    render(<BrainPolicyPage />);

    expect(screen.getByText("Access Denied")).toBeInTheDocument();
    expect(screen.queryByText("Brain Core — Policy Settings")).not.toBeInTheDocument();
  });
});
