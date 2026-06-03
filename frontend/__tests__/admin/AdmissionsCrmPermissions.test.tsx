import { describe, expect, it } from "vitest";
import {
  ADMISSIONS_CRM_PERMISSION_MATRIX_64,
  ADMISSIONS_CRM_RUNTIME_PERMISSIONS,
  hasAdmissionsCrmPermission,
  hasAnyAdmissionsCrmPermission,
} from "@/modules/admissions-crm/permissions";

describe("Admissions CRM permissions", () => {
  it("contains the expected runtime permission values", () => {
    expect(ADMISSIONS_CRM_RUNTIME_PERMISSIONS.READ).toBe("admin.admissions_crm.read");
    expect(ADMISSIONS_CRM_RUNTIME_PERMISSIONS.WRITE).toBe("admin.admissions_crm.write");
    expect(ADMISSIONS_CRM_RUNTIME_PERMISSIONS.AUDIT_READ).toBe("admin.admissions_crm.audit.read");
  });

  it("keeps 64 permission matrix entries", () => {
    expect(ADMISSIONS_CRM_PERMISSION_MATRIX_64).toHaveLength(64);
    expect(new Set(ADMISSIONS_CRM_PERMISSION_MATRIX_64).size).toBe(64);
  });

  it("evaluates permission helper checks", () => {
    const perms = [
      ADMISSIONS_CRM_RUNTIME_PERMISSIONS.READ,
      ADMISSIONS_CRM_RUNTIME_PERMISSIONS.WRITE,
    ];
    expect(hasAdmissionsCrmPermission(perms, ADMISSIONS_CRM_RUNTIME_PERMISSIONS.READ)).toBe(true);
    expect(hasAdmissionsCrmPermission(perms, ADMISSIONS_CRM_RUNTIME_PERMISSIONS.CONVERT)).toBe(false);
    expect(hasAnyAdmissionsCrmPermission(perms, [ADMISSIONS_CRM_RUNTIME_PERMISSIONS.CONVERT, ADMISSIONS_CRM_RUNTIME_PERMISSIONS.WRITE])).toBe(true);
  });
});
