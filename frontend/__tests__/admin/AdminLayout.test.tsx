import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import AdminLayout from "../../app/(admin)/layout";

const usePermissionsMock = vi.fn();

vi.mock("../../shared/hooks/use-permissions", () => ({
  usePermissions: () => usePermissionsMock(),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

vi.mock("../../shared/ui/providers", () => ({
  Providers: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("../../shared/ui/app-sidebar", () => ({
  AppSidebar: () => <div>Sidebar</div>,
}));

vi.mock("../../shared/ui/app-topbar", () => ({
  AppTopbar: () => <div>Topbar</div>,
}));

describe("AdminLayout", () => {
  it("renders admin shell for admin role", () => {
    usePermissionsMock.mockReturnValue({ roles: ["admin"] });

    render(
      <AdminLayout>
        <div>Admin Content</div>
      </AdminLayout>,
    );

    expect(screen.getByText("Sidebar")).toBeInTheDocument();
    expect(screen.getByText("Topbar")).toBeInTheDocument();
    expect(screen.getByText("Admin Content")).toBeInTheDocument();
  });

  it("renders access denied for non-admin role", () => {
    usePermissionsMock.mockReturnValue({ roles: ["teacher"] });

    render(
      <AdminLayout>
        <div>Admin Content</div>
      </AdminLayout>,
    );

    expect(screen.getByText(/only to platform superadmins/i)).toBeInTheDocument();
    expect(screen.queryByText("Admin Content")).not.toBeInTheDocument();
  });
});
