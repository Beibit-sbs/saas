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
        if (url.includes("/admin/i18n/languages")) {
          return new Response(JSON.stringify({ languages: [] }), { status: 200 });
        }
        if (url.includes("/admin/feature-flags")) {
          return new Response(JSON.stringify({ flags: [] }), { status: 200 });
        }
        if (url.includes("/admin/audit/events")) {
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
    expect(screen.getByTestId("sidebar-section-overview")).toBeInTheDocument();
    expect(screen.getByTestId("sidebar-section-languages")).toBeInTheDocument();
    expect(screen.queryByTestId("sidebar-section-example-notes")).not.toBeInTheDocument();
    expect(screen.queryByText(/example notes/i)).not.toBeInTheDocument();

    await user.click(screen.getByTestId("sidebar-section-languages"));

    await waitFor(() => {
      expect(screen.getByTestId("sidebar-section-languages")).toHaveClass("active");
      expect(screen.getByRole("listbox")).toBeInTheDocument();
    });
  });

  it("loads admin data without Authorization header and relies on cookie-first credentials", async () => {
    render(<AdminPage />);

    await screen.findByTestId("admin-page-shell");

    const dashboardCall = vi.mocked(fetch).mock.calls.find(([input]) => String(input).includes("/admin/dashboard"));
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
});
