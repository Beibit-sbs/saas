import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { RequireAdminRole } from "../../shared/ui/require-admin-role";

const usePermissionsMock = vi.fn();

vi.mock("../../shared/hooks/use-permissions", () => ({
  usePermissions: () => usePermissionsMock(),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

describe("RequireAdminRole", () => {
  it("renders children for superadmin", () => {
    usePermissionsMock.mockReturnValue({ roles: ["superadmin"] });

    render(
      <RequireAdminRole>
        <div>Platform Content</div>
      </RequireAdminRole>,
    );

    expect(screen.getByText("Platform Content")).toBeInTheDocument();
  });

  it("renders children for admin", () => {
    usePermissionsMock.mockReturnValue({ roles: ["admin"] });

    render(
      <RequireAdminRole>
        <div>Platform Content</div>
      </RequireAdminRole>,
    );

    expect(screen.getByText("Platform Content")).toBeInTheDocument();
  });

  it("renders access denied for non-admin role", () => {
    usePermissionsMock.mockReturnValue({ roles: ["teacher"] });

    render(
      <RequireAdminRole>
        <div>Platform Content</div>
      </RequireAdminRole>,
    );

    expect(screen.getByText(/only to platform administrators/i)).toBeInTheDocument();
  });
});
