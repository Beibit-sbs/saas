import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import LoginPage from "../../app/login/page";

const replaceMock = vi.fn();
const refreshMock = vi.fn();

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
    t: (key: string) => key,
    language: "ru",
    setLanguage: vi.fn(),
    supportedLanguages: [
      { code: "ru", name: "Russian", native_name: "Русский", enabled: true, system: true },
      { code: "en", name: "English", native_name: "English", enabled: true, system: true },
      { code: "kk", name: "Kazakh", native_name: "Қазақша", enabled: true, system: true },
    ],
  }),
}));

vi.mock("@/shared/ui/use-toast", () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

describe("LoginPage session redirect", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("redirects to /console when session is already authenticated", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith("/api/auth/me")) {
          return new Response(JSON.stringify({ authenticated: true }), { status: 200 });
        }
        return new Response(JSON.stringify({}), { status: 200 });
      }),
    );

    render(<LoginPage />);

    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith("/console");
      expect(refreshMock).toHaveBeenCalled();
    });
  });

  it("keeps login form visible when session is not authenticated", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith("/api/auth/me")) {
          return new Response(JSON.stringify({ authenticated: false }), { status: 401 });
        }
        return new Response(JSON.stringify({}), { status: 200 });
      }),
    );

    render(<LoginPage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "auth.signIn" })).toBeInTheDocument();
    });

    expect(replaceMock).not.toHaveBeenCalled();
  });
});
