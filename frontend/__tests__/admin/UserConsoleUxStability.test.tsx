import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const useLanguageMock = vi.fn();
const useAdminAuthMock = vi.fn();
const useToastMock = vi.fn();

vi.mock("../../app/components/LanguageProvider", () => ({
  useLanguage: (...args: unknown[]) => useLanguageMock(...args),
}));

vi.mock("../../shared/auth/hooks", () => ({
  useAdminAuth: (...args: unknown[]) => useAdminAuthMock(...args),
}));

vi.mock("../../shared/ui/use-toast", () => ({
  useToast: (...args: unknown[]) => useToastMock(...args),
}));

import ProfilePage from "../../app/(admin)/console/profile/page";
import PreferencesPage from "../../app/(admin)/console/preferences/page";
import SecurityPage from "../../app/(admin)/console/security/page";

const defaultLanguageDict: Record<string, string> = {
  "console.profile.title": "Profile",
  "console.profile.description": "Manage profile",
  "console.profile.accountInfoTitle": "Account Information",
  "console.profile.accountInfoDescription": "Profile identity from session",
  "console.profile.displayName": "Display name",
  "console.profile.userId": "User ID",
  "console.profile.tenant": "University",
  "console.profile.sessionStatus": "Session status",
  "console.profile.sessionChecking": "Checking session",
  "console.profile.sessionAuthenticated": "Authenticated",
  "console.profile.sessionNotAuthenticated": "Not authenticated",
  "console.profile.roles": "Roles",
  "console.profile.noRoleData": "No role data",
  "console.profile.readOnlyNotice": "Read only",
  "console.profile.readOnlyNoticeDetail": "Session refresh",
  "console.profile.refreshSession": "Refresh session data",
  "console.profile.actionsTitle": "Profile Actions",
  "console.profile.actionsDescription": "Quick actions",
  "console.profile.identitySourceTitle": "Identity source",
  "console.profile.identitySourceDescription": "Uses /api/auth/me",
  "console.profile.updateAccountTitle": "Need to update account details?",
  "console.profile.updateAccountDescription": "Contact admin",
  "console.preferences.title": "Preferences",
  "console.preferences.description": "Configure defaults",
  "console.preferences.workspaceTitle": "Console Preferences",
  "console.preferences.workspaceDescription": "Configure console experience",
  "console.preferences.languageLabel": "Language",
  "console.preferences.currentLanguageLabel": "Current",
  "console.preferences.selectLanguagePlaceholder": "Select language",
  "console.preferences.saveLanguage": "Save language",
  "console.preferences.themeModeLabel": "Theme mode",
  "console.preferences.themeModeDescription": "Toggle theme",
  "console.preferences.themeToggleAria": "Toggle dark mode",
  "console.preferences.scopeTitle": "Preference Scope",
  "console.preferences.scopeDescription": "How applied",
  "console.preferences.scopeLanguagePrefix": "Language preference is persisted for user",
  "console.preferences.scopeLanguageSuffix": "and applied after next sign-in.",
  "console.preferences.scopeThemeDescription": "Theme mode is stored in browser local storage.",
  "console.preferences.languageUpdatedTitle": "Language updated",
  "console.preferences.languageUpdatedDescription": "Language saved",
  "console.preferences.themeUpdatedTitle": "Theme updated",
  "console.preferences.themeUpdatedDescriptionDark": "Console theme switched to dark.",
  "console.preferences.themeUpdatedDescriptionLight": "Console theme switched to light.",
  "console.security.title": "Security",
  "console.security.description": "Security settings",
  "console.security.changePasswordTitle": "Change Password",
  "console.security.changePasswordDescription": "Update credentials",
  "console.security.currentPassword": "Current password",
  "console.security.newPassword": "New password",
  "console.security.confirmPassword": "Confirm new password",
  "console.security.updating": "Updating...",
  "console.security.updatePassword": "Update password",
  "console.security.accountSecurityTitle": "Account Security",
  "console.security.accountSecurityDescription": "Identity context",
  "console.security.userLabel": "User",
  "console.security.identifierLabel": "Identifier",
  "console.security.rotationRecommendation": "Rotate passwords",
  "console.security.validation.required": "All password fields are required.",
  "console.security.validation.length": "New password must be at least 8 characters.",
  "console.security.validation.complexity": "New password must include uppercase, lowercase and digits.",
  "console.security.validation.confirmation": "Password confirmation does not match.",
  "console.security.validation.different": "New password must differ from current password.",
  "console.security.passwordUpdateFailed": "Password update failed. Please try again.",
  "console.security.passwordUpdateSuccess": "Password has been updated successfully.",
  "console.security.passwordUpdatedTitle": "Password updated",
  "console.security.passwordUpdatedDescription": "Your account credentials were changed.",
  "console.security.endpointUnavailable": "Security endpoint is currently unavailable. Please retry later.",
};

function t(key: string) {
  return defaultLanguageDict[key] ?? key;
}

describe("User console UX stability", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    document.documentElement.classList.remove("dark");

    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: vi.fn().mockImplementation(() => ({
        matches: false,
        media: "(prefers-color-scheme: dark)",
        onchange: null,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        addListener: vi.fn(),
        removeListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });

    useLanguageMock.mockReturnValue({
      t,
      language: "en",
      setLanguage: vi.fn(),
      supportedLanguages: [
        { code: "kk", name: "Kazakh", native_name: "Kazakh", enabled: true, system: true },
        { code: "ru", name: "Russian", native_name: "Russian", enabled: true, system: true },
        { code: "en", name: "English", native_name: "English", enabled: true, system: true },
      ],
    });

    useAdminAuthMock.mockReturnValue({
      user: {
        sub: "user-123",
        displayName: "Test User",
        roles: ["admin"],
        permissions: [],
        tenantId: 12,
      },
      isLoading: false,
      refreshSession: vi.fn(),
    });

    useToastMock.mockReturnValue({ toast: vi.fn() });
  });

  it("shows validation message when security form is submitted empty", async () => {
    const user = userEvent.setup();
    render(<SecurityPage />);

    await user.click(screen.getByRole("button", { name: "Update password" }));

    expect(screen.getByText("All password fields are required.")).toBeInTheDocument();
  });

  it("shows mismatch validation in security form", async () => {
    const user = userEvent.setup();
    render(<SecurityPage />);

    fireEvent.change(screen.getByLabelText("Current password"), { target: { value: "Current12" } });
    fireEvent.change(screen.getByLabelText("New password"), { target: { value: "NewPassword9" } });
    fireEvent.change(screen.getByLabelText("Confirm new password"), { target: { value: "NewPassword8" } });

    await user.click(screen.getByRole("button", { name: "Update password" }));

    expect(screen.getByText("Password confirmation does not match.")).toBeInTheDocument();
  });

  it("applies and persists dark theme from preferences", async () => {
    const user = userEvent.setup();
    window.localStorage.setItem("console.theme", "dark");

    render(<PreferencesPage />);

    expect(document.documentElement.classList.contains("dark")).toBe(true);

    await user.click(screen.getByRole("switch", { name: "Toggle dark mode" }));

    expect(window.localStorage.getItem("console.theme")).toBe("light");
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });

  it("renders profile with session-backed values safely", () => {
    render(<ProfilePage />);

    expect(screen.getByDisplayValue("Test User")).toBeInTheDocument();
    expect(screen.getByDisplayValue("user-123")).toBeInTheDocument();
    expect(screen.getByDisplayValue("12")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Authenticated")).toBeInTheDocument();
    expect(screen.getByText("admin")).toBeInTheDocument();
  });
});
