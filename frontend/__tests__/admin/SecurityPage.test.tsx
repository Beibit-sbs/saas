import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import SecurityPage from "../../app/(admin)/console/security/page";

const toastMock = vi.fn();

vi.mock("../../app/components/LanguageProvider", () => ({
  useLanguage: () => ({
    t: (key: string) => {
      const dict: Record<string, string> = {
        "console.security.title": "Security",
        "console.security.description": "Manage security settings",
        "console.security.changePasswordTitle": "Change password",
        "console.security.changePasswordDescription": "Update account password",
        "console.security.currentPassword": "Current password",
        "console.security.newPassword": "New password",
        "console.security.confirmPassword": "Confirm password",
        "console.security.updating": "Updating",
        "console.security.updatePassword": "Update password",
        "console.security.accountSecurityTitle": "Account security",
        "console.security.accountSecurityDescription": "Security metadata",
        "console.security.userLabel": "User",
        "console.security.identifierLabel": "Identifier",
        "console.security.rotationRecommendation": "Rotate credentials regularly",
        "console.security.validation.required": "Required",
        "console.security.validation.length": "Too short",
        "console.security.validation.complexity": "Complexity",
        "console.security.validation.confirmation": "Mismatch",
        "console.security.validation.different": "Must be different",
        "console.security.passwordUpdateFailed": "Password update failed",
        "console.security.passwordUpdateSuccess": "Password updated",
        "console.security.passwordUpdatedTitle": "Updated",
        "console.security.passwordUpdatedDescription": "Password has been updated",
        "console.security.endpointUnavailable": "Endpoint unavailable",
      };
      return dict[key] ?? key;
    },
  }),
}));

vi.mock("../../shared/auth/hooks", () => ({
  useAdminAuth: () => ({
    user: {
      sub: "owner@example.com",
      displayName: "Owner",
      roles: ["admin"],
      permissions: ["platform.admin.read"],
      tenantId: 1,
    },
  }),
}));

vi.mock("../../shared/ui/use-toast", () => ({
  useToast: () => ({ toast: toastMock }),
}));

describe("SecurityPage MFA", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("starts MFA enrollment and shows secret/recovery codes", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/auth/csrf")) {
        return new Response(JSON.stringify({ csrf_token: "csrf-token" }), { status: 200 });
      }
      if (url.endsWith("/api/auth/mfa/enable")) {
        return new Response(
          JSON.stringify({
            secret: "ABCDEF123456",
            otpauth_uri: "otpauth://totp/ai-saas:owner@example.com?secret=ABCDEF123456&issuer=ai-saas",
            recovery_codes: ["rec-001", "rec-002"],
          }),
          { status: 200 },
        );
      }
      return new Response(JSON.stringify({}), { status: 200 });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<SecurityPage />);

    fireEvent.click(screen.getByRole("button", { name: "Start MFA enrollment" }));

    await waitFor(() => {
      expect(screen.getByText(/MFA enrollment started/i)).toBeInTheDocument();
    });

    expect(
      screen.getByText(/otpauth:\/\/totp\/ai-saas:owner@example.com\?secret=ABCDEF123456/i),
    ).toBeInTheDocument();
    expect(screen.getByText("rec-001")).toBeInTheDocument();
    expect(screen.getByText("rec-002")).toBeInTheDocument();
  });

  it("verifies MFA with one-time code", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/auth/csrf")) {
        return new Response(JSON.stringify({ csrf_token: "csrf-token" }), { status: 200 });
      }
      if (url.endsWith("/api/auth/mfa/verify")) {
        return new Response(JSON.stringify({ status: "enabled" }), { status: 200 });
      }
      return new Response(JSON.stringify({}), { status: 200 });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<SecurityPage />);

    fireEvent.change(screen.getByLabelText("One-time code"), { target: { value: "123456" } });
    fireEvent.click(screen.getByRole("button", { name: "Verify / Enable MFA" }));

    await waitFor(() => {
      expect(screen.getByText(/MFA enabled/i)).toBeInTheDocument();
    });

    expect(toastMock).toHaveBeenCalled();
  });
});
