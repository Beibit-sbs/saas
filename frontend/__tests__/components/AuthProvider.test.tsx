import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

vi.mock("../../app/components/csrf", () => ({
  buildCsrfHeaders: vi.fn(async () => ({ "X-CSRF-Token": "csrf-test" })),
  clearCsrfToken: vi.fn(),
  ensureCsrfToken: vi.fn(async () => "csrf-test"),
}));

import { AuthProvider, useAuth } from "../../app/components/AuthProvider";

function AuthConsumer() {
  const { user, loginWithCredentials } = useAuth();

  return (
    <div>
      <div data-testid="auth-user">{user ? `${user.display_name}:${user.user_id}` : "anonymous"}</div>
      <button type="button" onClick={() => void loginWithCredentials("local.admin", "secret123")}>login</button>
    </div>
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("bootstraps current user from cookie-backed profile endpoint", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/auth/me")) {
        expect(init).toEqual(expect.objectContaining({ credentials: "include", cache: "no-store" }));
        return Promise.resolve(
          new Response(
            JSON.stringify({
              authenticated: true,
              user: {
                sub: "local.001",
                displayName: "Cookie User",
                roles: ["admin"],
              },
            }),
            { status: 200 },
          ),
        );
      }
      return Promise.resolve(new Response(JSON.stringify({}), { status: 200 }));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("auth-user")).toHaveTextContent("Cookie User:local.001");
    });

    expect(localStorage.setItem).not.toHaveBeenCalledWith("app.token", expect.anything());
    expect(localStorage.setItem).not.toHaveBeenCalledWith("app.session", expect.anything());
    expect(localStorage.setItem).not.toHaveBeenCalledWith("app.userId", expect.anything());
  });

  it("logs in via cookie-first flow without persisting access token in localStorage", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/auth/me")) {
        return Promise.resolve(new Response(JSON.stringify({ detail: "unauthorized" }), { status: 401 }));
      }
      if (url.endsWith("/api/auth/login")) {
        expect(init).toEqual(
          expect.objectContaining({
            method: "POST",
            credentials: "include",
            headers: expect.objectContaining({
              "Content-Type": "application/json",
              "X-CSRF-Token": "csrf-test",
            }),
          }),
        );
        return Promise.resolve(
          new Response(
            JSON.stringify({
              user_id: "local.002",
              display_name: "Local Cookie User",
              roles: ["admin"],
              language: "en",
            }),
            { status: 200 },
          ),
        );
      }
      return Promise.resolve(new Response(JSON.stringify({}), { status: 200 }));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "login" }));

    await waitFor(() => {
      expect(screen.getByTestId("auth-user")).toHaveTextContent("Local Cookie User:local.002");
    });

    expect(localStorage.setItem).not.toHaveBeenCalledWith("app.token", expect.anything());
    expect(localStorage.setItem).not.toHaveBeenCalledWith("app.session", expect.anything());
    expect(localStorage.setItem).not.toHaveBeenCalledWith("app.userId", expect.anything());
  });
});
