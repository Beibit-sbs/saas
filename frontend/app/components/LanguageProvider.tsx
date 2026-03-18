"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { buildCsrfHeaders } from "./csrf";
import { commonTranslations, type CommonTranslationKey } from "../../i18n/common";

type BaseLanguage = "kk" | "ru" | "en";
export type AppLanguage = BaseLanguage | string;

export type SupportedLanguage = {
  code: string;
  name: string;
  native_name: string;
  enabled: boolean;
  system: boolean;
};

type LanguageContextValue = {
  language: AppLanguage;
  setLanguage: (lang: AppLanguage) => void;
  supportedLanguages: SupportedLanguage[];
  reloadLanguages: () => Promise<void>;
  t: (key: CommonTranslationKey) => string;
};

const LanguageContext = createContext<LanguageContextValue | null>(null);

const defaultSupportedLanguages: SupportedLanguage[] = [
  { code: "kk", name: "Kazakh", native_name: "Қазақша", enabled: true, system: true },
  { code: "ru", name: "Russian", native_name: "Русский", enabled: true, system: true },
  { code: "en", name: "English", native_name: "English", enabled: true, system: true },
];
const uiLanguageAllowlist = new Set<BaseLanguage>(["kk", "ru", "en"]);

function isBaseLanguage(lang: string): lang is BaseLanguage {
  return lang === "kk" || lang === "ru" || lang === "en";
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<AppLanguage>("ru");
  const [userId, setUserId] = useState<string | null>(null);
  const [supportedLanguages, setSupportedLanguages] = useState<SupportedLanguage[]>(
    defaultSupportedLanguages,
  );

  const reloadLanguages = useCallback(async () => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const res = await fetch(`${baseUrl}/i18n/languages`, { cache: "no-store" });
      if (!res.ok) {
        return;
      }

      const json = (await res.json()) as { languages?: SupportedLanguage[] };
      if (json.languages && json.languages.length > 0) {
        setSupportedLanguages(
          json.languages.filter((item) => uiLanguageAllowlist.has(item.code as BaseLanguage)),
        );
      }
    } catch {
      // Keep defaults when backend is unavailable.
    }
  }, []);

  useEffect(() => {
    const syncUserId = () => {
      const currentUserId = localStorage.getItem("app.userId");
      setUserId(currentUserId);
    };

    syncUserId();

    const saved = localStorage.getItem("app.language");
    if (saved) {
      setLanguage(saved);
      document.documentElement.lang = saved;
    }

    window.addEventListener("app-auth-changed", syncUserId);
    void reloadLanguages();

    return () => {
      window.removeEventListener("app-auth-changed", syncUserId);
    };
  }, [reloadLanguages]);

  useEffect(() => {
    const loadUserPreference = async () => {
      if (!userId) return;

      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
        const token = localStorage.getItem("app.token");
        const headers: Record<string, string> = {};
        if (token) {
          headers.Authorization = `Bearer ${token}`;
        }
        const res = await fetch(`${baseUrl}/auth/me/preferences`, {
          headers,
          credentials: "include",
          cache: "no-store",
        });

        if (!res.ok) return;
        const json = (await res.json()) as { language?: string | null };
        if (json.language) {
          setLanguage(json.language);
        }
      } catch {
        // Keep current language when preference endpoint is unavailable.
      }
    };

    void loadUserPreference();
  }, [userId]);

  useEffect(() => {
    localStorage.setItem("app.language", language);
    document.documentElement.lang = language;

    const saveUserPreference = async () => {
      if (!userId) return;

      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
        const token = localStorage.getItem("app.token");
        const csrfHeaders = await buildCsrfHeaders(baseUrl);
        const headers: Record<string, string> = {
          "Content-Type": "application/json",
          ...csrfHeaders,
        };
        if (token) {
          headers.Authorization = `Bearer ${token}`;
        }
        await fetch(`${baseUrl}/auth/me/preferences/language`, {
          method: "PUT",
          headers,
          credentials: "include",
          body: JSON.stringify({ language }),
        });
      } catch {
        // Keep local selection even if remote preference save fails.
      }
    };

    void saveUserPreference();
  }, [language, userId]);

  const value = useMemo<LanguageContextValue>(() => {
    const activeBaseLanguage = isBaseLanguage(language) ? language : "ru";

    return {
      language,
      setLanguage,
      supportedLanguages,
      reloadLanguages,
      t: (key: CommonTranslationKey) => commonTranslations[activeBaseLanguage]?.[key] ?? commonTranslations.ru[key],
    };
  }, [language, reloadLanguages, supportedLanguages]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    throw new Error("useLanguage must be used inside LanguageProvider");
  }
  return ctx;
}
