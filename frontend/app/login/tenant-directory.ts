export type LoginTenantOption = {
  tenantId: string;
  name: string;
  domains: string[];
};

export const LOGIN_LAST_TENANT_STORAGE_KEY = "login.lastTenantId";

export type LoginTenantDirectoryState = "ready" | "unavailable";

export type LoginTenantDirectoryResult = {
  state: LoginTenantDirectoryState;
  tenants: LoginTenantOption[];
  domainAutoDetectSupported: boolean;
};

const DEFAULT_TENANT_ID = String(process.env.NEXT_PUBLIC_DEFAULT_TENANT_ID ?? "1").trim() || "1";

type RawTenantOption = Partial<LoginTenantOption> & {
  tenant_id?: string | number;
  slug?: string;
  domains?: string[];
};

interface BackendLoginDirectoryResponse {
  tenants: Array<{
    tenant_id: number;
    slug?: string;
    name: string;
    domains?: string[];
  }>;
}

let cachedResult: LoginTenantDirectoryResult | null = null;
let cacheLoadPromise: Promise<LoginTenantDirectoryResult> | null = null;

function normalizeTenantOption(input: RawTenantOption): LoginTenantOption | null {
  const tenantId = String(input.tenantId ?? input.tenant_id ?? "").trim();
  const name = String(input.name ?? "").trim();

  if (!tenantId || !/^\d+$/.test(tenantId) || !name) {
    return null;
  }

  const seenDomains = new Set<string>();
  const domains = Array.isArray(input.domains)
    ? input.domains
      .map((domain) => String(domain).trim().toLowerCase())
      .filter((domain) => {
        if (!domain || seenDomains.has(domain)) {
          return false;
        }
        seenDomains.add(domain);
        return true;
      })
    : [];

  return {
    tenantId,
    name,
    domains,
  };
}

/**
 * Fetch login directory from backend endpoint.
 * Returns explicit status so UI can show an unavailable state instead of silently degrading.
 */
async function fetchLoginDirectoryFromBackend(): Promise<LoginTenantDirectoryResult> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch("/api/public/tenants/login-directory", {
      signal: controller.signal,
      headers: { "Accept": "application/json" },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      return {
        state: "unavailable",
        tenants: [],
        domainAutoDetectSupported: false,
      };
    }

    const data: BackendLoginDirectoryResponse = await response.json();
    if (!Array.isArray(data.tenants)) {
      return {
        state: "unavailable",
        tenants: [],
        domainAutoDetectSupported: false,
      };
    }

    const tenants = data.tenants
      .map((item) =>
        normalizeTenantOption({
          tenant_id: item.tenant_id,
          name: item.name,
          domains: item.domains,
        })
      )
      .filter((item): item is LoginTenantOption => item !== null);

    const hasDomainArrays = data.tenants.every((item) => Array.isArray(item.domains));
    const domainAutoDetectSupported = hasDomainArrays && tenants.some((item) => item.domains.length > 0);

    return {
      state: "ready",
      tenants,
      domainAutoDetectSupported,
    };
  } catch (error) {
    console.warn("[login-directory] Failed to fetch from backend:", error);
    return {
      state: "unavailable",
      tenants: [],
      domainAutoDetectSupported: false,
    };
  }
}

/**
 * Load login directory once per browser session.
 */
export async function loadLoginTenantDirectory(): Promise<LoginTenantDirectoryResult> {
  if (cachedResult !== null) {
    return cachedResult;
  }

  if (cacheLoadPromise !== null) {
    return cacheLoadPromise;
  }

  cacheLoadPromise = fetchLoginDirectoryFromBackend();
  cachedResult = await cacheLoadPromise;
  cacheLoadPromise = null;

  return cachedResult;
}

export function getDefaultTenantId(): string {
  return DEFAULT_TENANT_ID;
}

export function findTenantById(tenants: LoginTenantOption[], tenantId: string): LoginTenantOption | null {
  const normalized = String(tenantId).trim();
  return tenants.find((item) => item.tenantId === normalized) ?? null;
}

export function findTenantByDomain(tenants: LoginTenantOption[], domain: string): LoginTenantOption | null {
  const normalized = String(domain).trim().toLowerCase();
  if (!normalized) {
    return null;
  }

  return tenants.find((item) => item.domains.includes(normalized)) ?? null;
}