import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import AutomationRuleNewPage from "../../app/(admin)/console/automation/new/page";

let allowAccess = true;

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: ReactNode; permission: string }) =>
    allowAccess ? <>{children}</> : <div>Access Denied</div>,
}));

vi.mock("../../shared/ui/use-toast", () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

vi.mock("../../shared/auth/context", () => ({
  useAdminAuth: () => ({
    user: { tenantId: 1 },
    hasPermission: vi.fn(),
    hasAnyPermission: vi.fn(),
  }),
}));

vi.mock("../../modules/platform/automation/create-rule", () => ({
  useCreateAutomationRule: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
}));

vi.mock("../../app/components/LanguageProvider", () => ({
  useLanguage: () => ({
    t: (key: string) => key,
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

describe("AutomationRuleNewPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    allowAccess = true;
  });

  it("renders AccessDenied when automation.write permission is missing", () => {
    allowAccess = false;

    render(<AutomationRuleNewPage />);

    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
