const FORBIDDEN_RUNTIME_HOST_MARKERS = ["local" + "host", "127.0.0." + "1", "host." + "docker.internal"];

function readRequiredEnv(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) {
    throw new Error(`${name} is required`);
  }
  return value;
}

function assertNoForbiddenRuntimeHosts(name: string, value: string): string {
  if (process.env.NODE_ENV !== "production") {
    return value;
  }

  const lowered = value.toLowerCase();
  if (FORBIDDEN_RUNTIME_HOST_MARKERS.some((marker) => lowered.includes(marker))) {
    throw new Error(`${name} must not reference local host runtime targets`);
  }
  return value;
}

export function getServerApiBaseUrl(): string {
  return assertNoForbiddenRuntimeHosts("API_BASE_URL", readRequiredEnv("API_BASE_URL"));
}

export function shouldUseSecureCookie(request: Request): boolean {
  const explicit = process.env.AUTH_COOKIE_SECURE;
  if (explicit === "true") return true;
  if (explicit === "false") return false;

  const forwardedProto = request.headers.get("x-forwarded-proto");
  if (forwardedProto && forwardedProto.toLowerCase().includes("https")) {
    return true;
  }

  try {
    return new URL(request.url).protocol === "https:";
  } catch {
    return false;
  }
}
