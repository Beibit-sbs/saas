"use client";

import { useMemo, useState } from "react";
import { useLanguage } from "@/app/components/LanguageProvider";
import { useAdminAuth } from "@/shared/auth/hooks";
import { Button } from "@/shared/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { useToast } from "@/shared/ui/use-toast";

type PasswordFeedback = {
  tone: "success" | "error";
  message: string;
};

type MfaEnrollmentPayload = {
  secret?: string;
  otpauth_uri?: string;
  recovery_codes?: string[];
};

export default function SecurityPage() {
  const { t } = useLanguage();
  const { user } = useAdminAuth();
  const { toast } = useToast();

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<PasswordFeedback | null>(null);
  const [mfaCode, setMfaCode] = useState("");
  const [mfaRecoveryCode, setMfaRecoveryCode] = useState("");
  const [mfaEnrollment, setMfaEnrollment] = useState<MfaEnrollmentPayload | null>(null);
  const [mfaBusy, setMfaBusy] = useState(false);
  const [mfaMessage, setMfaMessage] = useState<{ tone: "success" | "error"; message: string } | null>(null);

  const validationError = useMemo(() => {
    if (!currentPassword || !newPassword || !confirmPassword) {
      return t("console.security.validation.required");
    }
    if (newPassword.length < 8) {
      return t("console.security.validation.length");
    }
    if (!/[A-Z]/.test(newPassword) || !/[a-z]/.test(newPassword) || !/[0-9]/.test(newPassword)) {
      return t("console.security.validation.complexity");
    }
    if (newPassword !== confirmPassword) {
      return t("console.security.validation.confirmation");
    }
    if (currentPassword === newPassword) {
      return t("console.security.validation.different");
    }
    return null;
  }, [confirmPassword, currentPassword, newPassword, t]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (validationError) {
      setFeedback({ tone: "error", message: validationError });
      return;
    }

    setIsSubmitting(true);
    setFeedback(null);
    try {
      const res = await fetch("/api/auth/me/password", {
        method: "PUT",
        credentials: "include",
        headers: {
          "content-type": "application/json",
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      if (!res.ok) {
        const payload = (await res.json().catch(() => null)) as { detail?: string } | null;
        const detail = payload?.detail;
        const message = detail || t("console.security.passwordUpdateFailed");
        setFeedback({ tone: "error", message });
        return;
      }

      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setFeedback({ tone: "success", message: t("console.security.passwordUpdateSuccess") });
      toast({
        title: t("console.security.passwordUpdatedTitle"),
        description: t("console.security.passwordUpdatedDescription"),
      });
    } catch {
      setFeedback({
        tone: "error",
        message: t("console.security.endpointUnavailable"),
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const fetchCsrfToken = async (): Promise<string> => {
    const res = await fetch("/api/auth/csrf", {
      method: "GET",
      cache: "no-store",
      credentials: "include",
    });
    if (!res.ok) {
      throw new Error("Failed to fetch CSRF token");
    }
    const payload = (await res.json().catch(() => ({}))) as { csrf_token?: unknown };
    const token = String(payload.csrf_token ?? "").trim();
    if (!token) {
      throw new Error("CSRF token is empty");
    }
    return token;
  };

  const handleMfaEnableStart = async () => {
    setMfaBusy(true);
    setMfaMessage(null);
    try {
      const csrfToken = await fetchCsrfToken();
      const res = await fetch("/api/auth/mfa/enable", {
        method: "POST",
        credentials: "include",
        headers: {
          "X-CSRF-Token": csrfToken,
        },
      });
      const payload = (await res.json().catch(() => ({}))) as MfaEnrollmentPayload & { detail?: string };
      if (!res.ok) {
        throw new Error(payload.detail || "Failed to start MFA enrollment");
      }
      setMfaEnrollment(payload);
      setMfaMessage({ tone: "success", message: "MFA enrollment started. Confirm with a one-time code." });
    } catch (error) {
      setMfaMessage({
        tone: "error",
        message: error instanceof Error ? error.message : "Failed to start MFA enrollment",
      });
    } finally {
      setMfaBusy(false);
    }
  };

  const handleMfaVerify = async () => {
    setMfaBusy(true);
    setMfaMessage(null);
    try {
      const csrfToken = await fetchCsrfToken();
      const res = await fetch("/api/auth/mfa/verify", {
        method: "POST",
        credentials: "include",
        headers: {
          "content-type": "application/json",
          "X-CSRF-Token": csrfToken,
        },
        body: JSON.stringify({
          code: mfaCode.trim() || undefined,
          recovery_code: mfaRecoveryCode.trim() || undefined,
        }),
      });
      const payload = (await res.json().catch(() => ({}))) as { status?: string; detail?: string };
      if (!res.ok) {
        throw new Error(payload.detail || "MFA verification failed");
      }
      setMfaCode("");
      setMfaRecoveryCode("");
      setMfaMessage({ tone: "success", message: `MFA ${payload.status ?? "verified"}.` });
      toast({
        title: "MFA updated",
        description: `Current status: ${payload.status ?? "verified"}`,
      });
    } catch (error) {
      setMfaMessage({
        tone: "error",
        message: error instanceof Error ? error.message : "MFA verification failed",
      });
    } finally {
      setMfaBusy(false);
    }
  };

  const handleMfaDisable = async () => {
    setMfaBusy(true);
    setMfaMessage(null);
    try {
      const csrfToken = await fetchCsrfToken();
      const res = await fetch("/api/auth/mfa/disable", {
        method: "POST",
        credentials: "include",
        headers: {
          "content-type": "application/json",
          "X-CSRF-Token": csrfToken,
        },
        body: JSON.stringify({
          code: mfaCode.trim() || undefined,
          recovery_code: mfaRecoveryCode.trim() || undefined,
        }),
      });
      const payload = (await res.json().catch(() => ({}))) as { status?: string; detail?: string };
      if (!res.ok) {
        throw new Error(payload.detail || "MFA disable failed");
      }
      setMfaEnrollment(null);
      setMfaCode("");
      setMfaRecoveryCode("");
      setMfaMessage({ tone: "success", message: "MFA disabled." });
      toast({
        title: "MFA disabled",
        description: "Two-factor authentication was disabled for this account.",
      });
    } catch (error) {
      setMfaMessage({
        tone: "error",
        message: error instanceof Error ? error.message : "MFA disable failed",
      });
    } finally {
      setMfaBusy(false);
    }
  };

  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">{t("console.security.title")}</h1>
        <p className="text-sm text-muted-foreground">{t("console.security.description")}</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg">{t("console.security.changePasswordTitle")}</CardTitle>
            <CardDescription>
              {t("console.security.changePasswordDescription")}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <Label htmlFor="current-password">{t("console.security.currentPassword")}</Label>
                <Input
                  id="current-password"
                  type="password"
                  autoComplete="current-password"
                  value={currentPassword}
                  onChange={(event) => setCurrentPassword(event.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="new-password">{t("console.security.newPassword")}</Label>
                <Input
                  id="new-password"
                  type="password"
                  autoComplete="new-password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirm-password">{t("console.security.confirmPassword")}</Label>
                <Input
                  id="confirm-password"
                  type="password"
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                />
              </div>

              {feedback ? (
                <div
                  className={
                    feedback.tone === "success"
                      ? "rounded-md border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-700"
                      : "rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
                  }
                >
                  {feedback.message}
                </div>
              ) : null}

              <div className="flex justify-end">
                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting ? t("console.security.updating") : t("console.security.updatePassword")}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">{t("console.security.accountSecurityTitle")}</CardTitle>
            <CardDescription>{t("console.security.accountSecurityDescription")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p>
              {t("console.security.userLabel")}: <span className="font-medium text-foreground">{user?.displayName ?? "-"}</span>
            </p>
            <p>
              {t("console.security.identifierLabel")}: <span className="font-medium text-foreground">{user?.sub ?? "-"}</span>
            </p>
            <p>
              {t("console.security.rotationRecommendation")}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Multi-factor authentication (MFA)</CardTitle>
          <CardDescription>
            Enable TOTP-based second factor, verify codes, and disable MFA with a valid code.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="secondary" onClick={handleMfaEnableStart} disabled={mfaBusy}>
              {mfaBusy ? "Please wait..." : "Start MFA enrollment"}
            </Button>
            <Button type="button" variant="outline" onClick={handleMfaVerify} disabled={mfaBusy}>
              {mfaBusy ? "Please wait..." : "Verify / Enable MFA"}
            </Button>
            <Button type="button" variant="destructive" onClick={handleMfaDisable} disabled={mfaBusy}>
              {mfaBusy ? "Please wait..." : "Disable MFA"}
            </Button>
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="mfa-code">One-time code</Label>
              <Input
                id="mfa-code"
                inputMode="numeric"
                autoComplete="one-time-code"
                value={mfaCode}
                onChange={(event) => setMfaCode(event.target.value)}
                placeholder="123456"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="mfa-recovery">Recovery code (optional)</Label>
              <Input
                id="mfa-recovery"
                value={mfaRecoveryCode}
                onChange={(event) => setMfaRecoveryCode(event.target.value)}
                placeholder="abcd1234"
              />
            </div>
          </div>

          {mfaEnrollment?.secret ? (
            <div className="rounded-md border border-muted px-3 py-2 text-sm">
              <p><span className="font-medium">Secret:</span> {mfaEnrollment.secret}</p>
              {mfaEnrollment.otpauth_uri ? (
                <p className="mt-1 break-all text-xs text-muted-foreground">
                  otpauth URI: {mfaEnrollment.otpauth_uri}
                </p>
              ) : null}
            </div>
          ) : null}

          {mfaEnrollment?.recovery_codes && mfaEnrollment.recovery_codes.length > 0 ? (
            <div className="rounded-md border border-muted px-3 py-2 text-sm">
              <p className="font-medium">Recovery codes</p>
              <ul className="mt-2 grid gap-1 text-xs text-muted-foreground">
                {mfaEnrollment.recovery_codes.map((code) => (
                  <li key={code}>{code}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {mfaMessage ? (
            <div
              className={
                mfaMessage.tone === "success"
                  ? "rounded-md border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-700"
                  : "rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive"
              }
            >
              {mfaMessage.message}
            </div>
          ) : null}
        </CardContent>
      </Card>
    </section>
  );
}
