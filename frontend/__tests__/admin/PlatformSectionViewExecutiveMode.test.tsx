import { describe, expect, it, vi, beforeEach } from "vitest";
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { PlatformSectionView } from "../../app/(admin)/console/platform/platform-section-view";

const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}));

vi.mock("@/shared/ui/require-admin-role", () => ({
  RequireAdminRole: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("@tanstack/react-query", async () => {
  const actual = await vi.importActual<typeof import("@tanstack/react-query")>("@tanstack/react-query");
  return {
    ...actual,
    useQuery: () => ({ data: undefined }),
    useQueryClient: () => ({ invalidateQueries: vi.fn() }),
    useMutation: () => ({ mutate: vi.fn() }),
  };
});

describe("PlatformSectionView executive mode in canonical flow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
  });

  it("renders canonical executive toggle", () => {
    render(<PlatformSectionView section={"overview" as any} />);

    expect(screen.getByTestId("canonical-executive-mode-toggle")).toBeInTheDocument();
    expect(screen.getByTestId("platform-console-unified")).toBeInTheDocument();
  });

  it("loads persisted executive mode from localStorage", () => {
    window.localStorage.setItem("admin.executiveMode", "1");
    render(<PlatformSectionView section={"overview" as any} />);

    expect(screen.getByTestId("canonical-executive-mode-toggle")).toHaveAttribute("aria-pressed", "true");
  });

  it("toggles and persists executive mode", async () => {
    const user = userEvent.setup();
    render(<PlatformSectionView section={"overview" as any} />);

    const toggle = screen.getByTestId("canonical-executive-mode-toggle");
    await act(async () => { await user.click(toggle); });

    expect(window.localStorage.getItem("admin.executiveMode")).toBe("1");
    expect(toggle).toHaveAttribute("aria-pressed", "true");
  });
});
