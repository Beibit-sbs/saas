import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import LoginPage from "../../app/login/page";

const replaceMock = vi.fn();
const refreshMock = vi.fn();
const toastMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: replaceMock,
    refresh: refreshMock,
    push: vi.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("../../app/components/LanguageProvider", () => ({
  useLanguage: () => ({
    t: (key: string) => {
      const dict: Record<string, string> = {
        "auth.required": "Required",
        "auth.loginFailed": "Login failed",
        "auth.tryAgain": "Please try again.",
        "auth.loginTitle": "AI University Platform",
        "auth.loginSubtitle": "Sign in to continue",
        "auth.username": "Username",
        "auth.password": "Password",
        "auth.signIn": "Sign in",
        "auth.universityLabel": "University",
        "auth.universityHelp": "Choose the university workspace for this sign-in.",
        "auth.universityAutoDetected": "University auto-detected from {domain}: {name}",
        "auth.universityManualRequired": "No university mapping was found for {domain}. Choose one manually.",
        "auth.universityRemembered": "Last used university restored: {name}",
        "auth.universityRequired": "Choose a university before signing in.",
        "auth.universityLoading": "Loading university directory...",
        "auth.universityUnavailable": "University directory is temporarily unavailable. Use technical tenant ID fallback.",
        "auth.platformAdminDetected": "Platform administrator login detected. University binding is not required for this sign-in.",
        "auth.technicalTenantToggle": "Advanced tenant ID fallback",
        "auth.technicalTenantLabel": "Technical tenant ID",
        "auth.technicalTenantHelp": "Use only when your university is not yet present in the login directory.",
        "auth.technicalTenantInvalid": "Tenant ID must be a positive integer.",
      };
      return dict[key] ?? key;
    },
    language: "en",
    setLanguage: vi.fn(),
    supportedLanguages: [
      { code: "ru", name: "Russian", native_name: "Русский", enabled: true, system: true },
      { code: "en", name: "English", native_name: "English", enabled: true, system: true },
    ],
  }),
}));

vi.mock("@/shared/ui/use-toast", () => ({
  useToast: () => ({
    toast: toastMock,
  }),
}));

vi.mock("../../app/components/LanguageSwitcher", () => ({
  default: () => <div data-testid="language-switcher" />,
}));

vi.mock("../../app/login/tenant-directory", () => {
  const directory = [
    { tenantId: "1", name: "Default Organization", domains: ["default.edu"] },
    { tenantId: "2", name: "Northwind University", domains: ["northwind.edu"] },
    { tenantId: "3", name: "Eastbridge Medical University", domains: ["eastbridge.edu"] },
  ];

  return {
    LOGIN_LAST_TENANT_STORAGE_KEY: "login.lastTenantId",
    getDefaultTenantId: () => "1",
    loadLoginTenantDirectory: async () => ({
      state: "ready",
      tenants: directory,
      domainAutoDetectSupported: false,
    }),
    findTenantById: (tenants: typeof directory, tenantId: string) => tenants.find((item) => item.tenantId === tenantId) ?? null,
    findTenantByDomain: (tenants: typeof directory, domain: string) => tenants.find((item) => item.domains.includes(domain)) ?? null,
  };
});

describe("LoginPage tenant UX", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
  });

  it("omits tenant_id for local/ platform admin login", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/auth/me")) {
        return new Response(JSON.stringify({ authenticated: false }), { status: 401 });
      }
      if (url.endsWith("/api/auth/login")) {
        return new Response(JSON.stringify({ ok: true }), { status: 200 });
      }
      return new Response(JSON.stringify({}), { status: 200 });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<LoginPage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText("Username"), { target: { value: "local/root" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "secret" } });

    expect(screen.queryByLabelText("University")).not.toBeInTheDocument();
    expect(screen.getByText(/platform administrator login detected/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith("/api/auth/login"))).toBe(true);
    });

    const loginCall = fetchMock.mock.calls.find(([input]) => String(input).endsWith("/api/auth/login"));
    expect(loginCall).toBeDefined();
    const [, init] = loginCall as [RequestInfo | URL, RequestInit];
    expect(JSON.parse(String(init.body))).toEqual({ username: "local/root", password: "secret" });
  });

  it("loads directory and submits selected university", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/auth/me")) {
        return new Response(JSON.stringify({ authenticated: false }), { status: 401 });
      }
      if (url.endsWith("/api/auth/login")) {
        return new Response(JSON.stringify({ ok: true }), { status: 200 });
      }
      return new Response(JSON.stringify({}), { status: 200 });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<LoginPage />);

    await waitFor(() => {
      expect(screen.getByLabelText("University")).toBeInTheDocument();
    });

    fireEvent.change(screen.getByLabelText("University"), { target: { value: "2" } });
    fireEvent.change(screen.getByLabelText("Username"), { target: { value: "dean@northwind.edu" } });

    await waitFor(() => {
      expect(window.localStorage.getItem("login.lastTenantId")).toBe("2");
    });

    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "secret" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith("/api/auth/login"))).toBe(true);
    });

    const loginCall = fetchMock.mock.calls.find(([input]) => String(input).endsWith("/api/auth/login"));
    expect(loginCall).toBeDefined();
    const [, init] = loginCall as [RequestInfo | URL, RequestInit];
    expect(JSON.parse(String(init.body))).toEqual({
      username: "dean@northwind.edu",
      password: "secret",
      tenant_id: 2,
    });
  });

  it("restores the remembered tenant and allows manual fallback selection", async () => {
    window.localStorage.setItem("login.lastTenantId", "3");

    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/auth/me")) {
        return new Response(JSON.stringify({ authenticated: false }), { status: 401 });
      }
      if (url.endsWith("/api/auth/login")) {
        return new Response(JSON.stringify({ ok: true }), { status: 200 });
      }
      return new Response(JSON.stringify({}), { status: 200 });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<LoginPage />);

    await waitFor(() => {
      expect(screen.getByLabelText("University")).toHaveValue("3");
    });

    expect(screen.getByText(/last used university restored/i)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Username"), { target: { value: "student@unknown.edu" } });

    fireEvent.change(screen.getByLabelText("University"), { target: { value: "1" } });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "secret" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith("/api/auth/login"))).toBe(true);
    });

    const loginCall = fetchMock.mock.calls.find(([input]) => String(input).endsWith("/api/auth/login"));
    expect(loginCall).toBeDefined();
    const [, init] = loginCall as [RequestInfo | URL, RequestInit];
    expect(JSON.parse(String(init.body))).toEqual({
      username: "student@unknown.edu",
      password: "secret",
      tenant_id: 1,
    });
    expect(window.localStorage.getItem("login.lastTenantId")).toBe("1");
  });
});