import type { AdminTab } from "@/app/admin/types";

export const PLATFORM_SECTION_TO_TAB = {
  overview: "overview",
  languages: "languages",
  "local-users": "local-users",
  rbac: "rbac",
  integrations: "integrations",
  backups: "backups",
  jobs: "jobs",
  audit: "audit",
  "feature-flags": "feature-flags",
  system: "system",
  university: "university",
  tenants: "tenants",
} as const satisfies Record<string, AdminTab>;

export const TAB_TO_PLATFORM_SECTION = Object.fromEntries(
  Object.entries(PLATFORM_SECTION_TO_TAB).map(([slug, tab]) => [tab, slug]),
) as Record<AdminTab, keyof typeof PLATFORM_SECTION_TO_TAB>;

export type PlatformSectionSlug = keyof typeof PLATFORM_SECTION_TO_TAB;

export function isPlatformSectionSlug(value: string): value is PlatformSectionSlug {
  return value in PLATFORM_SECTION_TO_TAB;
}
