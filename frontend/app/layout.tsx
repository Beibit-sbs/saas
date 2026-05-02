import type { Metadata } from "next";
import { cookies } from "next/headers";
import "./admin-console.css";

import { AuthProvider } from "./components/AuthProvider";
import { LanguageProvider } from "./components/LanguageProvider";
import RootLayoutOverlays from "./components/RootLayoutOverlays";
import { normalizeLocale } from "@/shared/i18n/locale";
import { getServerApiBaseUrl } from "@/shared/server/runtime-env";

type RuntimeLanguage = {
  code: string;
  enabled?: boolean;
};

function resolveDefaultLanguage(defaultLanguage: unknown, enabledCodes: Set<string>): string {
  const normalizedDefault = normalizeLocale(defaultLanguage, "ru");
  if (enabledCodes.has(normalizedDefault)) {
    return normalizedDefault;
  }
  if (enabledCodes.has("ru")) {
    return "ru";
  }
  if (enabledCodes.has("en")) {
    return "en";
  }
  return Array.from(enabledCodes)[0] || "ru";
}

export const metadata: Metadata = {
  title: "AI University Platform",
  description: "Unified platform for university and operations workflows",
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const apiBase = getServerApiBaseUrl();
  const localeCookie = cookies().get("app.locale")?.value;

  let initialLanguage = normalizeLocale(localeCookie, "ru");

  try {
    const res = await fetch(new URL("/api/i18n/languages", apiBase), {
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
    });
    if (res.ok) {
      const text = await res.text();
      const payload = text ? (JSON.parse(text) as { languages?: RuntimeLanguage[]; default_language?: string }) : null;
      if (payload) {
        const languages = (payload.languages || [])
          .filter((item) => item.enabled !== false)
          .map((item) => normalizeLocale(item.code, "ru"));

        const enabledCodes = new Set<string>(languages.length > 0 ? languages : ["ru", "en", "kk"]);
        const runtimeDefault = resolveDefaultLanguage(payload.default_language, enabledCodes);
        const cookieLocale = localeCookie
          ? normalizeLocale(localeCookie, "ru")
          : runtimeDefault;

        initialLanguage = enabledCodes.has(cookieLocale) ? cookieLocale : runtimeDefault;
      }
    }
  } catch {
    // Keep cookie/default fallback when runtime config is unavailable.
  }

  const dir = initialLanguage === "ar" ? "rtl" : "ltr";

  return (
    <html lang={initialLanguage} dir={dir}>
      <body>
        <AuthProvider>
          <LanguageProvider initialLanguage={initialLanguage}>
            {children}
            <RootLayoutOverlays />
          </LanguageProvider>
        </AuthProvider>
      </body>
    </html>
  );
}