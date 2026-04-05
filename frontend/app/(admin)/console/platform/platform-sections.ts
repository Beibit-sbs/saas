export const PLATFORM_SECTION_TO_TAB = {
  overview: "overview",
  tenants: "tenants",
  "billing-plans": "billing-plans",
  "usage-quotas": "usage-quotas",
  "feature-flags": "feature-flags",
  integrations: "integrations",
  automation: "automation",
  "service-accounts": "service-accounts",
} as const;

export type PlatformConsoleTab = (typeof PLATFORM_SECTION_TO_TAB)[keyof typeof PLATFORM_SECTION_TO_TAB];

export const TAB_TO_PLATFORM_SECTION = Object.fromEntries(
  Object.entries(PLATFORM_SECTION_TO_TAB).map(([slug, tab]) => [tab, slug]),
) as Record<PlatformConsoleTab, keyof typeof PLATFORM_SECTION_TO_TAB>;

export type PlatformSectionSlug = keyof typeof PLATFORM_SECTION_TO_TAB;

export function isPlatformSectionSlug(value: string): value is PlatformSectionSlug {
  return value in PLATFORM_SECTION_TO_TAB;
}
