"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { AdminControlPlaneContent } from "@/app/admin/components/AdminControlPlaneContent";
import type { AdminTab } from "@/app/admin/types";
import { adminTranslations } from "@/i18n/admin";
import { useLanguage } from "@/app/components/LanguageProvider";
import { TAB_TO_PLATFORM_SECTION } from "./platform-sections";
import { RequireAdminRole } from "@/shared/ui/require-admin-role";

interface PlatformSectionViewProps {
  tab: AdminTab;
}

const EXECUTIVE_MODE_STORAGE_KEY = "admin.executiveMode";

function toUiLang(value: string): "ru" | "en" | "kk" {
  const normalized = String(value || "").toLowerCase();
  const base = normalized.split(/[-_]/)[0];
  if (base === "ru" || base === "en" || base === "kk") {
    return base;
  }
  return "ru";
}

export function PlatformSectionView({ tab }: PlatformSectionViewProps) {
  const router = useRouter();
  const { language } = useLanguage();
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

  const handleTabChange = useCallback((nextTab: AdminTab) => {
    router.push(`/console/platform/${TAB_TO_PLATFORM_SECTION[nextTab]}`);
  }, [router]);

  return (
    <RequireAdminRole>
      <div className="space-y-3">
        <div className="flex justify-end">
          <button
            type="button"
            className="admin-presentation-toggle"
            onClick={() => setExecutiveMode((prev) => !prev)}
            aria-pressed={executiveMode}
            data-testid="canonical-executive-mode-toggle"
          >
            {executiveMode ? l.executiveModeDisable : l.executiveModeEnable}
          </button>
        </div>
        <AdminControlPlaneContent
          activeTab={tab}
          compact
          onTabChange={handleTabChange}
          executiveMode={executiveMode}
        />
      </div>
    </RequireAdminRole>
  );
}
