"use client";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useLanguage } from "../components/LanguageProvider";
import { AdminControlPlaneContent } from "./components/AdminControlPlaneContent";
import { AdminShell, type AdminSection } from "./components/AdminShell";
import { adminTranslations } from "../../i18n/admin";
import type { AdminTab } from "./types";

const EXECUTIVE_MODE_STORAGE_KEY = "admin.executiveMode";

function toUiLang(value: string): "ru" | "en" | "kk" {
  const normalized = String(value || "").toLowerCase();
  const base = normalized.split(/[-_]/)[0];
  if (base === "ru" || base === "en" || base === "kk") {
    return base;
  }
  return "ru";
}

export default function AdminPage() {
  const { t, language } = useLanguage();

  const [activeTab, setActiveTab] = useState<AdminTab>("overview");
  const [executiveMode, setExecutiveMode] = useState(false);

  const l = useMemo(() => adminTranslations[toUiLang(language)], [language]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = window.localStorage.getItem(EXECUTIVE_MODE_STORAGE_KEY);
    if (stored === "1") {
      setExecutiveMode(true);
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(EXECUTIVE_MODE_STORAGE_KEY, executiveMode ? "1" : "0");
  }, [executiveMode]);

  const adminSections: AdminSection[] = [
    { id: "overview", label: "Overview", icon: "◧" },
    { id: "languages", label: "Languages", icon: "⟲" },
    { id: "local-users", label: "Local Users", icon: "◫" },
    { id: "rbac", label: "RBAC", icon: "◎" },
    { id: "integrations", label: "Integrations", icon: "◇" },
    { id: "backups", label: "Backups", icon: "▣" },
    { id: "jobs", label: "Jobs", icon: "◔" },
    { id: "audit", label: "Audit", icon: "◌" },
    { id: "feature-flags", label: "Feature Flags", icon: "✦" },
    { id: "system", label: "System", icon: "◍" },
    { id: "university", label: "University", icon: "◬" },
    { id: "tenants", label: "Tenants", icon: "⬡" },
  ];

  return (
    <AdminShell
      activeTab={activeTab}
      onTabChange={(tab) => setActiveTab(tab as AdminTab)}
      sections={adminSections}
      platformName={t("admin.title")}
      presentationMode={executiveMode}
      adminSubtitle={l.adminHeaderSubtitle}
      executiveSubtitle={l.executiveHeaderSubtitle}
      headerControls={
        <div className="shellHeaderMeta">
          <button
            type="button"
            className="admin-presentation-toggle"
            onClick={() => setExecutiveMode((prev) => !prev)}
            aria-pressed={executiveMode}
            data-testid="admin-executive-mode-toggle"
          >
            {executiveMode ? l.executiveModeDisable : l.executiveModeEnable}
          </button>
          <span>Legacy /admin</span>
          <small>
            Canonical route: <Link href="/console/platform">/console/platform</Link>
          </small>
        </div>
      }
    >
      <AdminControlPlaneContent activeTab={activeTab} onTabChange={setActiveTab} executiveMode={executiveMode} />
    </AdminShell>
  );
}
