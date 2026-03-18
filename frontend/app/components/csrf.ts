let csrfTokenInMemory: string | null = null;

function readCookie(name: string): string | null {
  if (typeof document === "undefined") {
    return null;
  }

  const encodedName = `${encodeURIComponent(name)}=`;
  const parts = document.cookie.split(";");
  for (const part of parts) {
    const item = part.trim();
    if (item.startsWith(encodedName)) {
      return decodeURIComponent(item.slice(encodedName.length));
    }
  }
  return null;
}

export async function ensureCsrfToken(baseUrl: string): Promise<string | null> {
  if (csrfTokenInMemory) {
    return csrfTokenInMemory;
  }

  const fromCookie = readCookie("app_csrf_token");
  if (fromCookie) {
    csrfTokenInMemory = fromCookie;
    return csrfTokenInMemory;
  }

  try {
    const res = await fetch(`${baseUrl}/auth/csrf`, {
      method: "GET",
      credentials: "include",
      cache: "no-store",
    });
    if (!res.ok) {
      return null;
    }

    const json = (await res.json()) as { csrf_token?: string };
    const token = json.csrf_token?.trim() || readCookie("app_csrf_token");
    if (!token) {
      return null;
    }

    csrfTokenInMemory = token;
    return csrfTokenInMemory;
  } catch {
    return null;
  }
}

export async function buildCsrfHeaders(baseUrl: string): Promise<Record<string, string>> {
  const token = await ensureCsrfToken(baseUrl);
  return token ? { "X-CSRF-Token": token } : {};
}

export function clearCsrfToken(): void {
  csrfTokenInMemory = null;
}
