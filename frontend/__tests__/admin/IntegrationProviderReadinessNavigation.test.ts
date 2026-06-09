import { describe, expect, it } from "vitest";

import { SUPERADMIN_NAVIGATION } from "../../shared/config/navigation";

describe("Integration provider readiness navigation", () => {
  it("includes provider readiness route in admin console route map", () => {
    const allItems = SUPERADMIN_NAVIGATION.flatMap((group) => group.items);
    const providerReadiness = allItems.find((item) => item.href === "/console/integrations/provider-readiness");

    expect(providerReadiness).toBeDefined();
    expect(providerReadiness?.label).toBe("Provider Readiness");
  });
});
