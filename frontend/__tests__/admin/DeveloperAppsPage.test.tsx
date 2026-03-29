import { describe, expect, it, vi, beforeEach } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import type { ReactNode } from "react";

import DeveloperAppsPage from "../../app/(admin)/console/developer/apps/page";

const useDeveloperAppsMock = vi.fn();
const useDeveloperAppInstallationsMock = vi.fn();
const useDeveloperAppLogsMock = vi.fn();
const useCreateDeveloperAppMock = vi.fn();

vi.mock("../../modules/platform/developer/use-developer", () => ({
  useDeveloperApps: (...args: unknown[]) => useDeveloperAppsMock(...args),
  useDeveloperAppInstallations: (...args: unknown[]) => useDeveloperAppInstallationsMock(...args),
  useDeveloperAppLogs: (...args: unknown[]) => useDeveloperAppLogsMock(...args),
  useCreateDeveloperApp: (...args: unknown[]) => useCreateDeveloperAppMock(...args),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  RequirePermission: ({ children }: { children: ReactNode }) => <>{children}</>,
  PermissionGate: ({ children }: { children: ReactNode }) => <>{children}</>,
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

describe("DeveloperAppsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useDeveloperAppInstallationsMock.mockReturnValue({ data: [], isLoading: false, isError: false });
    useDeveloperAppLogsMock.mockReturnValue({ data: [], isLoading: false, isError: false });
    useCreateDeveloperAppMock.mockReturnValue({ mutateAsync: vi.fn(), isPending: false });
  });

  it("renders page and empty state", () => {
    useDeveloperAppsMock.mockReturnValue({ data: [], isLoading: false, isError: false });

    render(<DeveloperAppsPage />);

    expect(screen.getByTestId("developer-apps-page")).toBeInTheDocument();
    expect(screen.getByText(/no developer apps yet/i)).toBeInTheDocument();
  });

  it("renders apps and selected detail", () => {
    useDeveloperAppsMock.mockReturnValue({
      data: [
        {
          id: 1,
          name: "Registrar Sync",
          app_key: "app_123",
          description: "sync",
          owner_email: "owner@example.com",
          status: "active",
          scopes: ["students.read", "analytics.read"],
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:00Z",
        },
      ],
      isLoading: false,
      isError: false,
    });
    useDeveloperAppInstallationsMock.mockReturnValue({
      data: [{ id: 1, app_id: 1, tenant_id: 7, status: "active", installed_by: "owner@example.com", created_at: "2026-01-01T00:00:00Z" }],
      isLoading: false,
      isError: false,
    });
    useDeveloperAppLogsMock.mockReturnValue({
      data: [{ id: 1, app_id: 1, tenant_id: 7, endpoint: "/api/dev/students", status_code: 200, latency_ms: 12.5, created_at: "2026-01-01T00:00:00Z" }],
      isLoading: false,
      isError: false,
    });

    render(<DeveloperAppsPage />);
    fireEvent.click(screen.getByTestId("developer-app-row-1"));

    expect(screen.getByTestId("developer-app-detail-1")).toBeInTheDocument();
    expect(screen.getByTestId("developer-app-installations")).toBeInTheDocument();
    expect(screen.getByTestId("developer-app-logs")).toBeInTheDocument();
  });
});