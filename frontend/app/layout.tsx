import type { Metadata } from "next";
import { cookies } from "next/headers";
import "./admin-console.css";

import { AuthProvider } from "./components/AuthProvider";
import { LanguageProvider } from "./components/LanguageProvider";
import RootLayoutOverlays from "./components/RootLayoutOverlays";
import { normalizeLocale } from "@/shared/i18n/locale";

const API_BASE = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

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
  const localeCookie = cookies().get("app.locale")?.value;

  let initialLanguage = normalizeLocale(localeCookie, "ru");

  try {
    const res = await fetch(`${API_BASE}/api/i18n/languages`, {
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

  return (
    <html lang={initialLanguage}>
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