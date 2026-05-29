import { describe, expect, it, vi } from "vitest";

const redirectMock = vi.fn();

vi.mock("next/navigation", () => ({
  redirect: redirectMock,
}));

describe("Student Services welfare support alias route", () => {
  it("redirects legacy path to canonical student services support route", async () => {
    redirectMock.mockImplementation(() => {
      throw new Error("NEXT_REDIRECT");
    });

    const module = await import("@/app/(admin)/console/student-services-welfare-support/page");

    expect(() => module.default()).toThrow();
    expect(redirectMock).toHaveBeenCalledWith("/console/student-services-support");
  });
});
