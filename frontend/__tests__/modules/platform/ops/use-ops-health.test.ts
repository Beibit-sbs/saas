import { describe, expect, it } from "vitest";

import { summarizeOverall, toOpsStatus } from "../../../../modules/platform/ops/use-ops-health";

describe("ops health status mapping", () => {
  it("maps skipped as first-class status", () => {
    expect(toOpsStatus("skipped")).toBe("skipped");
  });

  it("keeps previous healthy and unhealthy mappings", () => {
    expect(toOpsStatus("ok")).toBe("healthy");
    expect(toOpsStatus("healthy")).toBe("healthy");
    expect(toOpsStatus("error")).toBe("critical");
    expect(toOpsStatus("unhealthy")).toBe("critical");
  });

  it("treats all healthy or skipped as healthy overall", () => {
    expect(summarizeOverall(["healthy", "healthy", "skipped"])).toBe("healthy");
  });

  it("prefers degraded over healthy and skipped", () => {
    expect(summarizeOverall(["healthy", "degraded", "skipped"])).toBe("degraded");
  });

  it("returns unknown when an unknown status is present without critical or degraded", () => {
    expect(summarizeOverall(["healthy", "unknown", "skipped"])).toBe("unknown");
  });

  it("keeps critical as highest severity", () => {
    expect(summarizeOverall(["healthy", "critical", "skipped"])).toBe("critical");
  });
});
