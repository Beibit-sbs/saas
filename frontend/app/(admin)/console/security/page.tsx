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

export default function SecurityPage() {
  const { t } = useLanguage();
  const { user } = useAdminAuth();
  const { toast } = useToast();

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<PasswordFeedback | null>(null);

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
    </section>
  );
}
