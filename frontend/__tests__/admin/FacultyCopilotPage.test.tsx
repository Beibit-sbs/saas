import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import FacultyCopilotPage from "../../app/(admin)/console/faculty-copilot/page";

let allowAccess = true;

vi.mock("../../modules/faculty-copilot/hooks", () => ({
  useGenerateLessonPlan: () => ({ mutate: vi.fn(), isPending: false, data: null }),
  useGenerateMaterialPack: () => ({ mutate: vi.fn(), isPending: false, data: null }),
  useFacultyQnA: () => ({ mutate: vi.fn(), isPending: false, data: null }),
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

describe("FacultyCopilotPage", () => {
  beforeEach(() => {
    allowAccess = true;
  });

  it("renders page title", () => {
    render(<FacultyCopilotPage />);
    expect(screen.getByText(/Faculty Copilot/i)).toBeInTheDocument();
  });

  it("renders action buttons", () => {
    render(<FacultyCopilotPage />);
    expect(screen.getByRole("button", { name: /Generate Lesson Plan/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Generate Materials/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Ask Q&A/i })).toBeInTheDocument();
  });

  it("shows placeholder without answer", () => {
    render(<FacultyCopilotPage />);
    expect(screen.getByText(/No answer yet/i)).toBeInTheDocument();
  });

  it("shows access denied without permission", () => {
    allowAccess = false;
    render(<FacultyCopilotPage />);
    expect(screen.getByText(/Access Denied/i)).toBeInTheDocument();
  });
});
