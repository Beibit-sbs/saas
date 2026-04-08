import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import HealthPage from "../../app/(admin)/console/health/page";

const hasPermissionMock = vi.fn();

vi.mock("../../shared/hooks/use-permissions", () => ({
  usePermissions: () => ({
    hasPermission: hasPermissionMock,
    hasAnyPermission: hasPermissionMock,
    roles: [],
  }),
}));

vi.mock("../../modules/platform/health/hooks", () => ({
  useHealthStatus: () => ({
    data: null,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  }),
  useMetrics: () => ({
    data: null,
    isLoading: false,
  }),
}));

vi.mock("../../shared/ui/permission-gate", () => ({
  AccessDenied: ({ message }: { message?: string }) => <div>{message ?? "Access Denied"}</div>,
}));

vi.mock("../../app/components/LanguageProvider", () => ({
  useLanguage: () => ({
    t: (key: string) => key,
  }),
}));

describe("HealthPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders AccessDenied when health read permission is missing", () => {
    hasPermissionMock.mockReturnValue(false);

    render(<HealthPage />);

    expect(hasPermissionMock).toHaveBeenCalled();
    expect(screen.getByText("Access Denied")).toBeInTheDocument();
  });
});
