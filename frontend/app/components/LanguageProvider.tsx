"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import { buildCsrfHeaders } from "./csrf";
import { useAuth } from "./AuthProvider";
import { commonTranslations, type CommonTranslationKey } from "../../i18n/common";
import {
  LOCALE_COOKIE_KEY,
  LOCALE_STORAGE_KEY,
  normalizeLocale,
  type AppLocale,
} from "@/shared/i18n/locale";

export type AppLanguage = AppLocale;

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

const SAFE_FALLBACK_ORDER = ["ru", "en", "kk"] as const;

function pickAvailableLanguage(preferred: unknown, availableCodes: Set<string>, runtimeDefault: AppLanguage): AppLanguage {
  const normalizedPreferred = normalizeLocale(preferred, "ru");
  if (availableCodes.has(normalizedPreferred)) {
    return normalizedPreferred;
  }

  const normalizedDefault = normalizeLocale(runtimeDefault, "ru");
  if (availableCodes.has(normalizedDefault)) {
    return normalizedDefault;
  }

  for (const candidate of SAFE_FALLBACK_ORDER) {
    if (availableCodes.has(candidate)) {
      return candidate;
    }
  }

  const firstAvailable = Array.from(availableCodes)[0];
  return firstAvailable || "ru";
}

function getRuntimeDictionary(locale: unknown) {
  const normalized = normalizeLocale(locale, "ru");
  const dictionaries = commonTranslations as Record<string, Record<CommonTranslationKey, string>>;
  return dictionaries[normalized];
}
function readLocaleCookie(): string | null {
  if (typeof document === "undefined") return null;
  const parts = document.cookie.split(";").map((item) => item.trim());
  for (const part of parts) {
    if (!part) continue;
    const [key, ...valueParts] = part.split("=");
    if (key === LOCALE_COOKIE_KEY) {
      return decodeURIComponent(valueParts.join("=") || "");
    }
  }
  return null;
}

function persistLocale(locale: string) {
  if (typeof document !== "undefined") {
    document.documentElement.lang = locale;
    document.cookie = `${LOCALE_COOKIE_KEY}=${encodeURIComponent(locale)}; Path=/; Max-Age=31536000; SameSite=Lax`;
  }
  if (typeof localStorage !== "undefined") {
    localStorage.setItem(LOCALE_STORAGE_KEY, locale);
  }
}

export function LanguageProvider({
  children,
  initialLanguage,
}: {
  children: ReactNode;
  initialLanguage?: AppLanguage;
}) {
  const { user } = useAuth();
  const [language, setLanguageState] = useState<AppLanguage>(() =>
    normalizeLocale(initialLanguage, "ru"),
  );
  const didHydrateLocaleRef = useRef(false);
  const pendingHydratedLocaleRef = useRef<AppLanguage | null>(null);
  const hasPersistedPreferenceRef = useRef(false);
  const didApplySessionFallbackRef = useRef(false);
  const [supportedLanguages, setSupportedLanguages] = useState<SupportedLanguage[]>(
    defaultSupportedLanguages,
  );
  const [runtimeDefaultLanguage, setRuntimeDefaultLanguage] = useState<AppLanguage>("ru");

  const setLanguage = useCallback((next: AppLanguage) => {
    const normalized = normalizeLocale(next, "ru");
    hasPersistedPreferenceRef.current = true;
    setLanguageState(normalized);
  }, []);

  const reloadLanguages = useCallback(async () => {
    try {
      const res = await fetch("/api/i18n/languages", { cache: "no-store" });
      if (!res.ok) {
        return;
      }

      const json = (await res.json()) as { languages?: SupportedLanguage[]; default_language?: string };
      const normalizedLanguages = (json.languages || [])
        .map((item) => ({ ...item, code: normalizeLocale(item.code) }))
        .filter((item) => item.enabled);

      const nextSupportedLanguages = normalizedLanguages.length > 0
        ? normalizedLanguages
        : defaultSupportedLanguages;

      const availableCodes = new Set(nextSupportedLanguages.map((item) => item.code));
      const nextDefaultLanguage = pickAvailableLanguage(json.default_language || "ru", availableCodes, "ru");

      setSupportedLanguages(nextSupportedLanguages);
      setRuntimeDefaultLanguage(nextDefaultLanguage);

      setLanguageState((current) => {
        const preferred = hasPersistedPreferenceRef.current
          ? (pendingHydratedLocaleRef.current ?? current)
          : current;
        return pickAvailableLanguage(preferred, availableCodes, nextDefaultLanguage);
      });

      if (!hasPersistedPreferenceRef.current) {
        pendingHydratedLocaleRef.current = nextDefaultLanguage;
        setLanguageState(nextDefaultLanguage);
      }
    } catch {
      // Keep defaults when backend is unavailable.
    }
  }, []);

  useEffect(() => {
    const fromCookie = readLocaleCookie();
    const fromStorage = typeof localStorage !== "undefined" ? localStorage.getItem(LOCALE_STORAGE_KEY) : null;
    const persistedLocale = fromCookie || fromStorage;

    hasPersistedPreferenceRef.current = Boolean(persistedLocale);
    const initial = normalizeLocale(persistedLocale || "ru", "ru");

    pendingHydratedLocaleRef.current = initial;
    setLanguageState(initial);
    persistLocale(initial);
    didHydrateLocaleRef.current = true;

    void reloadLanguages();
  }, [reloadLanguages]);

  useEffect(() => {
    const availableCodes = new Set(
      supportedLanguages
        .filter((item) => item.enabled)
        .map((item) => normalizeLocale(item.code)),
    );
    if (availableCodes.size === 0) {
      return;
    }

    setLanguageState((current) => pickAvailableLanguage(current, availableCodes, runtimeDefaultLanguage));
  }, [runtimeDefaultLanguage, supportedLanguages]);

  useEffect(() => {
    const loadUserPreference = async () => {
      const userId = user?.user_id;
      if (!userId) return;

      // Respect explicit/persisted locale selection and avoid re-applying session fallback.
      if (hasPersistedPreferenceRef.current || didApplySessionFallbackRef.current) {
        return;
      }

      if (user.language) {
        const fromSession = normalizeLocale(user.language, "ru");
        setLanguageState((current) => (current === fromSession ? current : fromSession));
        didApplySessionFallbackRef.current = true;
        return;
      }

      try {
        const res = await fetch("/api/auth/me/preferences", {
          credentials: "include",
          cache: "no-store",
        });

        if (!res.ok) return;
        const json = (await res.json()) as { language?: string | null };
        if (json.language && !hasPersistedPreferenceRef.current) {
          setLanguageState(normalizeLocale(json.language, "ru"));
          didApplySessionFallbackRef.current = true;
        }
      } catch {
        // Keep current language when preference endpoint is unavailable.
      }
    };

    void loadUserPreference();
  }, [user?.language, user?.user_id]);

  useEffect(() => {
    if (!didHydrateLocaleRef.current) {
      return;
    }

    // Skip the stale first run where state is still the pre-hydration default.
    if (pendingHydratedLocaleRef.current !== null) {
      if (language !== pendingHydratedLocaleRef.current) {
        pendingHydratedLocaleRef.current = null;
      } else {
        pendingHydratedLocaleRef.current = null;
      }
    }

    persistLocale(language);

    const saveUserPreference = async () => {
      const userId = user?.user_id;
      if (!userId) return;

      try {
        const csrfHeaders = await buildCsrfHeaders("/api");
        await fetch("/api/auth/me/preferences/language", {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            ...csrfHeaders,
          },
          credentials: "include",
          body: JSON.stringify({ language }),
        });
      } catch {
        // Keep local selection even if remote preference save fails.
      }
    };

    void saveUserPreference();
  }, [language, user?.user_id]);

  const value = useMemo<LanguageContextValue>(() => {
    const selectedDict = getRuntimeDictionary(language);
    const defaultDict = getRuntimeDictionary(runtimeDefaultLanguage);
    const ruDict = commonTranslations.ru;
    const enDict = commonTranslations.en;

    return {
      language,
      setLanguage,
      supportedLanguages,
      reloadLanguages,
      t: (key: CommonTranslationKey) => selectedDict?.[key]
        ?? defaultDict?.[key]
        ?? ruDict[key]
        ?? enDict[key]
        ?? key,
    };
  }, [language, reloadLanguages, runtimeDefaultLanguage, setLanguage, supportedLanguages]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) {
    throw new Error("useLanguage must be used inside LanguageProvider");
  }
  return ctx;
}
