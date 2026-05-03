import { format as dateFnsFormat } from "date-fns";

export function formatDate(dateStr: string | null | undefined, fmt = "dd MMM yyyy, HH:mm"): string {
  if (!dateStr) return "—";
  try {
    return dateFnsFormat(new Date(dateStr), fmt);
  } catch {
    return dateStr;
  }
}

export function formatDateShort(dateStr: string | null | undefined): string {
  return formatDate(dateStr, "dd MMM yyyy");
}

export function formatRelative(dateStr: string | null | undefined): string {
  if (!dateStr) return "—";
  try {
    const diff = Date.now() - new Date(dateStr).getTime();
    const sec = Math.floor(diff / 1000);
    if (sec < 60) return `${sec}s ago`;
    const min = Math.floor(sec / 60);
    if (min < 60) return `${min}m ago`;
    const hr = Math.floor(min / 60);
    if (hr < 24) return `${hr}h ago`;
    return formatDate(dateStr, "dd MMM");
  } catch {
    return dateStr;
  }
}

export function formatNumber(n: number | null | undefined): string {
  if (n == null) return "—";
  return new Intl.NumberFormat().format(n);
}

function normalizeLocale(languageCode?: string | null): string {
  switch ((languageCode ?? "").toLowerCase()) {
    case "kk":
      return "kk-KZ";
    case "ru":
      return "ru-RU";
    case "en":
      return "en-US";
    default:
      return languageCode && languageCode.trim().length > 0 ? languageCode : "en-US";
  }
}

export function formatCurrencyAmount(
  amount: number | null | undefined,
  options?: {
    currencyCode?: string | null;
    languageCode?: string | null;
  },
): string {
  if (amount == null) return "—";

  const currency = (options?.currencyCode ?? "USD").toUpperCase();
  const locale = normalizeLocale(options?.languageCode);

  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    currencyDisplay: "code",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
    .format(amount)
    .replace(/\u00a0/g, " ")
    .trim();
}

export function formatBytes(bytes: number | null | undefined): string {
  if (bytes == null) return "—";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let i = 0;
  let b = bytes;
  while (b >= 1024 && i < units.length - 1) {
    b /= 1024;
    i++;
  }
  return `${b.toFixed(1)} ${units[i]}`;
}

export function truncate(str: string | null | undefined, len = 48): string {
  if (!str) return "—";
  return str.length > len ? `${str.slice(0, len)}…` : str;
}

export function capitalize(str: string | null | undefined): string {
  if (!str) return "";
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}
