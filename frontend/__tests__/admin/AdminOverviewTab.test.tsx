import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import AdminPage from "../../app/admin/page";

const realConsoleError = console.error;

vi.mock("../../app/components/LanguageProvider", () => ({
  useLanguage: () => ({
    t: (key: string) => {
      if (key === "admin.title") return "Platform Admin";
      if (key === "admin.subtitle") return "Operational console";
      return key;
    },
    language: "ru",
    supportedLanguages: [
      { code: "ru", name: "Russian", native_name: "Русский", enabled: true, system: true },
      { code: "en", name: "English", native_name: "English", enabled: true, system: true },
    ],
    reloadLanguages: vi.fn(async () => undefined),
  }),
}));

vi.mock("../../app/components/csrf", () => ({
  buildCsrfHeaders: vi.fn(async () => ({})),
}));

describe("AdminPage shell integration", () => {
  let consoleErrorSpy: { mockRestore: () => void };

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();

    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation((...args) => {
      const firstArg = String(args[0] ?? "");
      if (firstArg.includes("Warning: An update to %s inside a test was not wrapped in act(...).")) {
        return;
      }
      realConsoleError(...args);
    });

    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/i18n/catalog")) {
          return new Response(JSON.stringify({ languages: [] }), { status: 200 });
        }
        if (url.includes("/admin/dashboard")) {
          return new Response(
            JSON.stringify({
              status: "ok",
              generated_at: "2026-03-18T00:00:00Z",
              system: { backend_health: "ok", api_health: "ok", metrics_available: true },
              users: { local_users_count: 2 },
              rbac: { roles_count: 2, assignments_count: 3 },
              languages: { total_count: 2, enabled_count: 2, system_count: 2 },
              integrations: {
                ldap: { enabled: false, configured: false },
                ai_providers: { total_count: 1, configured_count: 0 },
              },
              backups: { active_profile: "default", profiles_count: 1, last_job: null },
              audit: { recent_events_count: 0, last_event: null },
            }),
            { status: 200 },
          );
        }
        if (url.includes("/api/bff/admin/system/health")) {
          return new Response(
            JSON.stringify({
              status: "ok",
              services: { api: "ok", worker: "ok" },
              metrics: {},
              queues: { default: 0 },
              disk: {
                path: "/tmp",
                total_bytes: 1000,
                used_bytes: 400,
                free_bytes: 600,
                usage_percent: 40,
              },
            }),
            { status: 200 },
          );
        }
        if (url.includes("/api/bff/admin/jobs")) {
          return new Response(JSON.stringify({ jobs: [] }), { status: 200 });
        }
        if (url.includes("/admin/i18n/languages")) {
          return new Response(JSON.stringify({ languages: [] }), { status: 200 });
        }
        if (url.includes("/api/bff/admin/local-users")) {
          return new Response(JSON.stringify({ users: [] }), { status: 200 });
        }
        if (url.includes("/api/bff/admin/feature-flags") || url.includes("/admin/feature-flags")) {
          return new Response(JSON.stringify({ flags: [] }), { status: 200 });
        }
        if (url.includes("/api/bff/admin/audit/events") || url.includes("/admin/audit/events")) {
          return new Response(JSON.stringify({ events: [] }), { status: 200 });
        }
        return new Response(JSON.stringify({}), { status: 200 });
      });
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it("renders real admin page inside shell and switches sections from sidebar", async () => {
    const user = userEvent.setup();

    render(<AdminPage />);

    // findByTestId uses waitFor internally, flushing React's async act queue
    await screen.findByTestId("admin-page-shell");

    expect(screen.getAllByText("Platform Admin").length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: "/console/platform" })).toHaveAttribute("href", "/console/platform");
    expect(screen.getByTestId("sidebar-section-overview")).toBeInTheDocument();
    expect(screen.getByTestId("sidebar-section-languages")).toBeInTheDocument();
    expect(screen.queryByTestId("sidebar-section-example-notes")).not.toBeInTheDocument();
    expect(screen.queryByText(/example notes/i)).not.toBeInTheDocument();

    await user.click(screen.getByTestId("sidebar-section-languages"));

    await waitFor(() => {
      expect(screen.getByTestId("sidebar-section-languages")).toHaveClass("active");
      expect(screen.getByRole("listbox")).toBeInTheDocument();
    });

    await user.click(screen.getByTestId("sidebar-section-overview"));

    await waitFor(() => {
      expect(screen.getByTestId("overview-route-integrations")).toBeInTheDocument();
      expect(screen.getByTestId("overview-insight-backup-missing")).toBeInTheDocument();
    });

    await user.click(screen.getByTestId("overview-insight-backup-missing"));

    await waitFor(() => {
      expect(screen.getByTestId("sidebar-section-backups")).toHaveClass("active");
    });
  });

  it("loads admin data without Authorization header and relies on cookie-first credentials", async () => {
    render(<AdminPage />);

    await screen.findByTestId("admin-page-shell");

    const dashboardCall = vi.mocked(fetch).mock.calls.find(([input]) => String(input).includes("/api/bff/admin/dashboard"));
    expect(dashboardCall).toBeDefined();

    const init = dashboardCall?.[1] as RequestInit | undefined;
    expect(init).toEqual(
      expect.objectContaining({
        credentials: "include",
        cache: "no-store",
      }),
    );
    expect(init?.headers).not.toHaveProperty("Authorization");
  });

  it("keeps overview stable when auxiliary datasets fail and avoids duplicate primary snapshot requests", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);

      if (url.includes("/i18n/catalog") || url.includes("/admin/i18n/languages")) {
        return new Response(JSON.stringify({ languages: [] }), { status: 200 });
      }
      if (url.includes("/api/bff/admin/dashboard")) {
        return new Response(
          JSON.stringify({
            status: "ok",
            generated_at: "2026-03-18T00:00:00Z",
            system: { backend_health: "ok", api_health: "ok", metrics_available: true },
            users: { local_users_count: 1 },
            rbac: { roles_count: 2, assignments_count: 1 },
            languages: { total_count: 2, enabled_count: 2, system_count: 2 },
            integrations: {
              ldap: { enabled: true, configured: true },
              ai_providers: { total_count: 1, configured_count: 1 },
            },
            backups: {
              active_profile: "default",
              profiles_count: 1,
              last_job: {
                job_id: "backup-1",
                status: "success",
                profile_id: "default",
                file_path: "/tmp/backup.dump",
                size_bytes: 128,
                started_at: "2026-03-17T23:00:00Z",
                finished_at: "2026-03-17T23:30:00Z",
              },
            },
            audit: { recent_events_count: 1, last_event: null },
          }),
          { status: 200 },
        );
      }
      if (url.includes("/api/bff/admin/system/health") || url.includes("/api/bff/admin/jobs") || url.includes("/api/bff/admin/local-users")) {
        return new Response(JSON.stringify({ detail: "temporary failure" }), { status: 503 });
      }
      if (url.includes("/api/bff/admin/audit/events")) {
        return new Response(JSON.stringify({ events: [] }), { status: 200 });
      }
      if (url.includes("/api/bff/admin/feature-flags") || url.includes("/admin/feature-flags")) {
        return new Response(JSON.stringify({ flags: [] }), { status: 200 });
      }

      return new Response(JSON.stringify({}), { status: 200 });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<AdminPage />);

    await screen.findByTestId("admin-page-shell");

    await waitFor(() => {
      expect(screen.getByText(/частично|partial/i)).toBeInTheDocument();
      expect(screen.getByTestId("overview-insight-backup-healthy")).toBeInTheDocument();
    });

    const dashboardCalls = vi.mocked(fetch).mock.calls.filter(([input]) => String(input).includes("/api/bff/admin/dashboard"));
    expect(dashboardCalls).toHaveLength(1);
  });

  it("restores persisted executive mode and toggles technical details visibility", async () => {
    const user = userEvent.setup();
    localStorage.setItem("admin.executiveMode", "1");

    render(<AdminPage />);

    await screen.findByTestId("admin-page-shell");

    const modeToggle = screen.getByTestId("admin-executive-mode-toggle");
    expect(modeToggle).toHaveAttribute("aria-pressed", "true");
    expect(localStorage.getItem("admin.executiveMode")).toBe("1");

    expect(screen.getByTestId("overview-executive-brief")).toBeInTheDocument();

    const technicalToggle = screen.getByTestId("overview-technical-toggle");
    expect(screen.queryByTestId("overview-technical-details")).not.toBeInTheDocument();

    await user.click(technicalToggle);
    expect(screen.getByTestId("overview-technical-details")).toBeInTheDocument();

    await user.click(technicalToggle);
    expect(screen.queryByTestId("overview-technical-details")).not.toBeInTheDocument();

    await user.click(modeToggle);

    await waitFor(() => {
      expect(modeToggle).toHaveAttribute("aria-pressed", "false");
      expect(screen.queryByTestId("overview-technical-toggle")).not.toBeInTheDocument();
    });

    expect(localStorage.getItem("admin.executiveMode")).toBe("0");
  });
});
