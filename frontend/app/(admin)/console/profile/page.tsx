"use client";

import { useMemo } from "react";
import { useLanguage } from "@/app/components/LanguageProvider";
import { useAdminAuth } from "@/shared/auth/hooks";
import { Badge } from "@/shared/ui/badge";
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

export default function ProfilePage() {
  const { t } = useLanguage();
  const { user, refreshSession, isLoading } = useAdminAuth();

  const roleBadges = useMemo(() => user?.roles ?? [], [user?.roles]);

  const displayName = user?.displayName ?? "-";
  const userId = user?.sub ?? "-";
  const tenantId = typeof user?.tenantId === "number" ? String(user.tenantId) : "-";

  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">{t("console.profile.title")}</h1>
        <p className="text-sm text-muted-foreground">{t("console.profile.description")}</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg">{t("console.profile.accountInfoTitle")}</CardTitle>
            <CardDescription>{t("console.profile.accountInfoDescription")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="profile-display-name">{t("console.profile.displayName")}</Label>
                <Input id="profile-display-name" value={displayName} readOnly />
              </div>
              <div className="space-y-2">
                <Label htmlFor="profile-user-id">{t("console.profile.userId")}</Label>
                <Input id="profile-user-id" value={userId} readOnly />
              </div>
              <div className="space-y-2">
                <Label htmlFor="profile-tenant-id">{t("console.profile.tenant")}</Label>
                <Input id="profile-tenant-id" value={tenantId} readOnly />
              </div>
              <div className="space-y-2">
                <Label htmlFor="profile-auth-state">{t("console.profile.sessionStatus")}</Label>
                <Input
                  id="profile-auth-state"
                  value={
                    isLoading
                      ? t("console.profile.sessionChecking")
                      : user
                        ? t("console.profile.sessionAuthenticated")
                        : t("console.profile.sessionNotAuthenticated")
                  }
                  readOnly
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>{t("console.profile.roles")}</Label>
              <div className="flex flex-wrap gap-2">
                {roleBadges.length > 0 ? (
                  roleBadges.map((role) => (
                    <Badge key={role} variant="secondary">
                      {role}
                    </Badge>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">{t("console.profile.noRoleData")}</p>
                )}
              </div>
            </div>

            <div className="rounded-lg border bg-muted/40 p-4 text-sm text-muted-foreground">
              {t("console.profile.readOnlyNotice")}
              {" "}
              {t("console.profile.readOnlyNoticeDetail")}
            </div>

            <div className="flex justify-end">
              <Button type="button" variant="outline" onClick={() => void refreshSession()}>
                {t("console.profile.refreshSession")}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">{t("console.profile.actionsTitle")}</CardTitle>
            <CardDescription>{t("console.profile.actionsDescription")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-md border p-3 text-sm">
              <p className="font-medium">{t("console.profile.identitySourceTitle")}</p>
              <p className="mt-1 text-muted-foreground">
                {t("console.profile.identitySourceDescription")}
              </p>
            </div>
            <div className="rounded-md border p-3 text-sm">
              <p className="font-medium">{t("console.profile.updateAccountTitle")}</p>
              <p className="mt-1 text-muted-foreground">
                {t("console.profile.updateAccountDescription")}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
