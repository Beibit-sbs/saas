import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import FeatureFlagsPage from "../../app/(admin)/console/feature-flags/page";

const useFeatureFlagsMock = vi.fn();
const hasPermissionMock = vi.fn();

vi.mock("../../modules/platform/feature-flags/hooks", () => ({
  useFeatureFlags: (...args: unknown[]) => useFeatureFlagsMock(...args),
  useUpsertFeatureFlag: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock("../../shared/hooks/use-permissions", () => ({
  usePermissions: () => ({
    hasPermission: hasPermissionMock,
    hasAnyPermission: hasPermissionMock,
    roles: [],
  }),
}));

vi.mock("../../shared/hooks/use-mutation-feedback", () => ({
  useMutationFeedback: () => ({
    getHandlers: () => ({ onSuccess: vi.fn(), onError: vi.fn() }),
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

describe("FeatureFlagsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useFeatureFlagsMock.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders AccessDenied when feature-flags read permission is missing", () => {
    hasPermissionMock.mockReturnValue(false);

    render(<FeatureFlagsPage />);

    expect(hasPermissionMock).toHaveBeenCalled();
    expect(screen.getByText("Access Denied")).toBeInTheDocument();
  });
});
