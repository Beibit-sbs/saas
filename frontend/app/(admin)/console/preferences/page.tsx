"use client";

import { useEffect, useMemo, useState } from "react";
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
import { Label } from "@/shared/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import { Switch } from "@/shared/ui/switch";
import { useToast } from "@/shared/ui/use-toast";

const CONSOLE_THEME_STORAGE_KEY = "console.theme";

type ThemeMode = "light" | "dark";

export default function PreferencesPage() {
  const { t, language, setLanguage, supportedLanguages } = useLanguage();
  const { user } = useAdminAuth();
  const { toast } = useToast();

  const [pendingLanguage, setPendingLanguage] = useState(language);
  const [themeMode, setThemeMode] = useState<ThemeMode>("light");

  useEffect(() => {
    setPendingLanguage(language);
  }, [language]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const storedTheme = window.localStorage.getItem(CONSOLE_THEME_STORAGE_KEY);
    if (storedTheme === "dark" || storedTheme === "light") {
      setThemeMode(storedTheme);
      document.documentElement.classList.toggle("dark", storedTheme === "dark");
      return;
    }

    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const nextTheme: ThemeMode = prefersDark ? "dark" : "light";
    setThemeMode(nextTheme);
    document.documentElement.classList.toggle("dark", prefersDark);
  }, []);

  const hasLanguageChanges = pendingLanguage !== language;

  const languageDescription = useMemo(() => {
    const active = supportedLanguages.find((item) => item.code === language);
    return active ? `${active.native_name} (${active.code})` : language;
  }, [language, supportedLanguages]);

  const applyLanguage = () => {
    setLanguage(pendingLanguage);
    toast({
      title: t("console.preferences.languageUpdatedTitle"),
      description: t("console.preferences.languageUpdatedDescription"),
    });
  };

  const toggleTheme = (checked: boolean) => {
    const nextTheme: ThemeMode = checked ? "dark" : "light";
    setThemeMode(nextTheme);
    if (typeof document !== "undefined") {
      document.documentElement.classList.toggle("dark", checked);
    }
    if (typeof window !== "undefined") {
      window.localStorage.setItem(CONSOLE_THEME_STORAGE_KEY, nextTheme);
    }
    toast({
      title: t("console.preferences.themeUpdatedTitle"),
      description:
        nextTheme === "dark"
          ? t("console.preferences.themeUpdatedDescriptionDark")
          : t("console.preferences.themeUpdatedDescriptionLight"),
    });
  };

  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">{t("console.preferences.title")}</h1>
        <p className="text-sm text-muted-foreground">{t("console.preferences.description")}</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg">{t("console.preferences.workspaceTitle")}</CardTitle>
            <CardDescription>{t("console.preferences.workspaceDescription")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-3 rounded-lg border p-4">
              <div className="space-y-1">
                <Label htmlFor="language-select">{t("console.preferences.languageLabel")}</Label>
                <p className="text-sm text-muted-foreground">
                  {t("console.preferences.currentLanguageLabel")}: {languageDescription}
                </p>
              </div>
              <Select value={pendingLanguage} onValueChange={setPendingLanguage}>
                <SelectTrigger id="language-select" className="max-w-sm">
                  <SelectValue placeholder={t("console.preferences.selectLanguagePlaceholder")} />
                </SelectTrigger>
                <SelectContent>
                  {supportedLanguages.map((item) => (
                    <SelectItem key={item.code} value={item.code}>
                      {item.native_name} ({item.code})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="flex justify-end">
                <Button type="button" onClick={applyLanguage} disabled={!hasLanguageChanges}>
                  {t("console.preferences.saveLanguage")}
                </Button>
              </div>
            </div>

            <div className="space-y-3 rounded-lg border p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <Label htmlFor="theme-switch">{t("console.preferences.themeModeLabel")}</Label>
                  <p className="text-sm text-muted-foreground">
                    {t("console.preferences.themeModeDescription")}
                  </p>
                </div>
                <Switch
                  id="theme-switch"
                  checked={themeMode === "dark"}
                  onCheckedChange={toggleTheme}
                  aria-label={t("console.preferences.themeToggleAria")}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">{t("console.preferences.scopeTitle")}</CardTitle>
            <CardDescription>{t("console.preferences.scopeDescription")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p>
              {t("console.preferences.scopeLanguagePrefix")} {user?.sub ?? "-"} {t("console.preferences.scopeLanguageSuffix")}
            </p>
            <p>
              {t("console.preferences.scopeThemeDescription")}
            </p>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
