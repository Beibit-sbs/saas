import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AppTopbar } from "../../shared/ui/app-topbar";

const useAdminAuthMock = vi.fn();
const useLanguageMock = vi.fn();
const loadLoginTenantDirectoryMock = vi.fn();
const findTenantByIdMock = vi.fn();

vi.mock("../../shared/auth/hooks", () => ({
  useAdminAuth: (...args: unknown[]) => useAdminAuthMock(...args),
}));

vi.mock("../../app/components/LanguageProvider", () => ({
  useLanguage: (...args: unknown[]) => useLanguageMock(...args),
}));

vi.mock("../../app/components/LanguageSwitcher", () => ({
  default: () => <div data-testid="language-switcher" />,
}));

vi.mock("../../app/login/tenant-directory", () => ({
  loadLoginTenantDirectory: (...args: unknown[]) => loadLoginTenantDirectoryMock(...args),
  findTenantById: (...args: unknown[]) => findTenantByIdMock(...args),
}));

describe("AppTopbar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useLanguageMock.mockReturnValue({
      t: (key: string) => {
        const dict: Record<string, string> = {
          "ui.profile": "Profile",
          "ui.preferences": "Preferences",
          "ui.security": "Security",
          "ui.signOut": "Sign out",
          "ui.platformContext": "Platform Scope",
          "ui.universityIdFallback": "University ID {id}",
        };
        return dict[key] ?? key;
      },
    });
    loadLoginTenantDirectoryMock.mockResolvedValue({ state: "ready", tenants: [] });
    findTenantByIdMock.mockReturnValue(null);
  });

  it("renders user identity trigger", async () => {
    useAdminAuthMock.mockReturnValue({
      user: {
        displayName: "Alice Admin",
        sub: "alice",
        tenantId: 7,
        roles: ["admin"],
      },
      logout: vi.fn(),
    });

    findTenantByIdMock.mockReturnValue({ tenantId: "7", name: "Northwind University" });

    render(<AppTopbar />);

    expect(screen.getByTestId("language-switcher")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /alice admin/i })).toBeInTheDocument();
    expect(screen.getByText("AA")).toBeInTheDocument();
    expect(await screen.findByText("Northwind University")).toBeInTheDocument();
  });

  it("shows safe university ID fallback when name is unavailable", async () => {
    useAdminAuthMock.mockReturnValue({
      user: {
        displayName: "Alice Admin",
        sub: "alice",
        tenantId: 12,
        roles: ["admin"],
      },
      logout: vi.fn(),
    });

    render(<AppTopbar />);

    expect(await screen.findByText("University ID 12")).toBeInTheDocument();
  });

  it("shows platform context for superadmin without tenant scope", () => {
    useAdminAuthMock.mockReturnValue({
      user: {
        displayName: "Platform Admin",
        sub: "root",
        roles: ["superadmin"],
      },
      logout: vi.fn(),
    });

    render(<AppTopbar />);

    expect(screen.getByText("Platform Scope")).toBeInTheDocument();
  });

  it("shows profile, preferences and security links in dropdown", async () => {
    const user = userEvent.setup();

    useAdminAuthMock.mockReturnValue({
      user: {
        displayName: "Alice Admin",
        sub: "alice",
      },
      logout: vi.fn(),
    });

    render(<AppTopbar />);

    await user.click(screen.getByRole("button", { name: /alice admin/i }));

    expect(screen.getByRole("menuitem", { name: "Profile" })).toHaveAttribute("href", "/console/profile");
    expect(screen.getByRole("menuitem", { name: "Preferences" })).toHaveAttribute("href", "/console/preferences");
    expect(screen.getByRole("menuitem", { name: "Security" })).toHaveAttribute("href", "/console/security");
  });

  it("calls logout from dropdown action", async () => {
    const user = userEvent.setup();
    const logout = vi.fn();

    useAdminAuthMock.mockReturnValue({
      user: {
        displayName: "Alice Admin",
        sub: "alice",
      },
      logout,
    });

    render(<AppTopbar />);

    await user.click(screen.getByRole("button", { name: /alice admin/i }));
    await user.click(screen.getByRole("menuitem", { name: "Sign out" }));

    expect(logout).toHaveBeenCalledTimes(1);
  });
});
