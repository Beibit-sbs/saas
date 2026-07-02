import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiRequestError, apiGet } from "@/shared/api/client";
import { BACKEND_UNAVAILABLE_EVENT } from "@/shared/auth/session-events";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("api client backend unavailable event", () => {
  it("does not emit a global backend outage for module-level 503 responses", async () => {
    const listener = vi.fn();
    window.addEventListener(BACKEND_UNAVAILABLE_EVENT, listener);
    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          error: {
            status: 503,
            code: "UPSTREAM_ERROR",
            detail: "module database unavailable",
          },
        }),
        { status: 503, headers: { "content-type": "application/json" } },
      ),
    );

    await expect(apiGet("/api/admin/students")).rejects.toBeInstanceOf(ApiRequestError);

    expect(listener).not.toHaveBeenCalled();
    window.removeEventListener(BACKEND_UNAVAILABLE_EVENT, listener);
  });

  it("emits a global backend outage for BFF transport failures", async () => {
    const listener = vi.fn();
    window.addEventListener(BACKEND_UNAVAILABLE_EVENT, listener);
    vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          error: {
            status: 503,
            code: "BACKEND_UNAVAILABLE",
            detail: "Upstream unavailable",
          },
        }),
        { status: 503, headers: { "content-type": "application/json" } },
      ),
    );

    await expect(apiGet("/api/admin/students")).rejects.toBeInstanceOf(ApiRequestError);

    expect(listener).toHaveBeenCalledTimes(1);
    window.removeEventListener(BACKEND_UNAVAILABLE_EVENT, listener);
  });
});
