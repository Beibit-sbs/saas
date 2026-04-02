import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { PlatformSectionView } from "../../app/(admin)/console/platform/platform-section-view";

const pushMock = vi.fn();
const contentMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}));

vi.mock("@/app/components/LanguageProvider", () => ({
  useLanguage: () => ({ language: "en" }),
}));

vi.mock("@/shared/ui/require-admin-role", () => ({
  RequireAdminRole: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock("@/app/admin/components/AdminControlPlaneContent", () => ({
  AdminControlPlaneContent: (props: {
    activeTab: string;
    compact?: boolean;
    executiveMode?: boolean;
    onTabChange?: (tab: string) => void;
  }) => {
    contentMock(props);
    return (
      <div data-testid="platform-content">
        tab:{props.activeTab}|executive:{props.executiveMode ? "1" : "0"}
      </div>
    );
  },
}));

describe("PlatformSectionView executive mode in canonical flow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
  });

  it("renders canonical executive toggle", () => {
    render(<PlatformSectionView tab={"overview" as any} />);

    expect(screen.getByTestId("canonical-executive-mode-toggle")).toBeInTheDocument();
    expect(screen.getByTestId("platform-content")).toHaveTextContent("executive:0");
  });

  it("loads persisted executive mode from localStorage", () => {
    window.localStorage.setItem("admin.executiveMode", "1");
    render(<PlatformSectionView tab={"overview" as any} />);

    expect(screen.getByTestId("platform-content")).toHaveTextContent("executive:1");
  });

  it("toggles and persists executive mode", async () => {
    const user = userEvent.setup();
    render(<PlatformSectionView tab={"overview" as any} />);

    const toggle = screen.getByTestId("canonical-executive-mode-toggle");
    await user.click(toggle);

    expect(window.localStorage.getItem("admin.executiveMode")).toBe("1");
    expect(screen.getByTestId("platform-content")).toHaveTextContent("executive:1");
  });
});
