import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import PromptManagementPage from "../../app/(admin)/console/prompt-management/page";

let allowAccess = true;

vi.mock("../../modules/prompt-management/hooks", () => ({
  useCreateTemplate: () => ({ mutate: vi.fn(), isPending: false }),
  useListTemplates: () => ({
    data: [
      {
        template_id: "tpl-1",
        name: "advisor-v1",
        category: "academic",
        version: 1,
        is_active: true,
      },
    ],
  }),
  useABRoute: () => ({ mutate: vi.fn(), isPending: false, data: null }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: React.ReactNode; permission: string }) =>
    allowAccess ? <>{children}</> : <div>Access Denied</div>,
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

vi.mock("../../shared/hooks/use-permissions", () => ({
  usePermissions: () => ({
    hasPermission: () => allowAccess,
    hasAnyPermission: () => allowAccess,
    roles: allowAccess ? ["admin"] : [],
  }),
}));

describe("PromptManagementPage", () => {
  beforeEach(() => {
    allowAccess = true;
  });

  it("renders page title", () => {
    render(<PromptManagementPage />);
    expect(screen.getByText(/Prompt Management/i)).toBeInTheDocument();
  });

  it("renders template rows", () => {
    render(<PromptManagementPage />);
    expect(screen.getByText("advisor-v1")).toBeInTheDocument();
    expect(screen.getByText("v1")).toBeInTheDocument();
  });

  it("renders create form", () => {
    render(<PromptManagementPage />);
    expect(screen.getByLabelText(/Name/i)).toBeInTheDocument();
  });

  it("shows access denied without permission", () => {
    allowAccess = false;
    render(<PromptManagementPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
