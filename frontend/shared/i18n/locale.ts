export const LOCALE_COOKIE_KEY = "app.locale";
export const LOCALE_STORAGE_KEY = "app.language";

export const BASE_LOCALES = ["ru", "kk", "en", "ar"] as const;
export type BaseLocale = (typeof BASE_LOCALES)[number];
export type AppLocale = BaseLocale | string;

const BASE_LOCALE_SET = new Set<string>(BASE_LOCALES);

export function normalizeLocale(input: unknown, fallback: BaseLocale = "ru"): AppLocale {
  const raw = String(input ?? "").trim();
  if (!raw) return fallback;
  const lowered = raw.toLowerCase();
  const base = lowered.split(/[-_]/)[0];
  return base || fallback;
}

export function toBaseLocale(input: unknown, fallback: BaseLocale = "ru"): BaseLocale {
  const normalized = normalizeLocale(input, fallback);
  return BASE_LOCALE_SET.has(normalized) ? (normalized as BaseLocale) : fallback;
}
