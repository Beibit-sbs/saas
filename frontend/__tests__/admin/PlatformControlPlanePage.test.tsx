import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import PlatformControlPlanePage from "../../app/(admin)/console/platform/page";
import { PERMISSIONS } from "../../shared/config/permissions";

const hasPermissionMock = vi.fn();

vi.mock("../../shared/hooks/use-permissions", () => ({
  usePermissions: () => ({
    hasPermission: hasPermissionMock,
  }),
}));

vi.mock("../../app/(admin)/console/platform/platform-section-view", () => ({
  PlatformSectionView: ({ section }: { section: string }) => <div>section:{section}</div>,
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  PermissionGate: ({ children }: { children: ReactNode }) => <>{children}</>,
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

describe("PlatformControlPlanePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("checks platform admin read permission", () => {
    hasPermissionMock.mockReturnValue(true);

    render(<PlatformControlPlanePage />);

    expect(hasPermissionMock).toHaveBeenCalledWith(PERMISSIONS.DEVELOPER_PLATFORM_READ);
    expect(screen.getByText("section:overview")).toBeInTheDocument();
  });

  it("renders AccessDenied when user lacks platform admin read permission", () => {
    hasPermissionMock.mockReturnValue(false);

    render(<PlatformControlPlanePage />);

    expect(screen.getByText("Access Denied")).toBeInTheDocument();
  });
});
