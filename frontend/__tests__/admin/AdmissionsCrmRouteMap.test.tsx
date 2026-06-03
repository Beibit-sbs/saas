import { describe, expect, it } from "vitest";
import {
  ADMISSIONS_CRM_BASE_ROUTE,
  ADMISSIONS_CRM_ROUTE_COUNT,
  ADMISSIONS_CRM_ROUTES,
} from "@/modules/admissions-crm/routeMap";

describe("Admissions CRM route map", () => {
  it("declares the expected route inventory", () => {
    expect(ADMISSIONS_CRM_ROUTE_COUNT).toBe(14);
    expect(ADMISSIONS_CRM_ROUTES).toHaveLength(14);
    expect(ADMISSIONS_CRM_BASE_ROUTE).toBe("/console/admissions");
  });

  it("keeps route paths unique and tenant scoped", () => {
    const paths = ADMISSIONS_CRM_ROUTES.map((route) => route.path);
    expect(new Set(paths).size).toBe(paths.length);
    expect(ADMISSIONS_CRM_ROUTES.every((route) => route.tenantScoped)).toBe(true);
  });

  it("retains settings-permissions route and required permission", () => {
    const route = ADMISSIONS_CRM_ROUTES.find((item) => item.key === "settings-permissions");
    expect(route?.path).toBe("/console/admissions/settings/permissions");
    expect(route?.requiredPermissions).toContain("admin.admissions_crm.audit.read");
  });
});
