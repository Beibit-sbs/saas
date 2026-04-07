import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

import {
  NAVIGATION,
  STUDENT_NAVIGATION,
  TEACHER_NAVIGATION,
  DEAN_NAVIGATION,
  SUPERADMIN_NAVIGATION,
  getNavigationForRoles,
} from "../../shared/config/navigation";

function collectHrefs(groups: Array<{ items: Array<{ href: string; children?: Array<{ href: string }> }> }>): string[] {
  const result: string[] = [];
  for (const group of groups) {
    for (const item of group.items) {
      result.push(item.href);
      for (const child of item.children ?? []) {
        result.push(child.href);
      }
    }
  }
  return Array.from(new Set(result));
}

function toCandidatePaths(href: string): string[] {
  const clean = href.replace(/^\/+/, "");
  return [clean];
}

function collectPageFiles(dir: string): string[] {
  const result: string[] = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      result.push(...collectPageFiles(fullPath));
      continue;
    }
    if (entry.isFile() && entry.name === "page.tsx") {
      result.push(fullPath);
    }
  }
  return result;
}

function routeFromPageFile(appRoot: string, filePath: string): string {
  const relative = path.relative(appRoot, filePath).replace(/\\/g, "/");
  const noPage = relative.replace(/\/page\.tsx$/, "");
  const segments = noPage
    .split("/")
    .filter(Boolean)
    .filter((segment) => !(segment.startsWith("(") && segment.endsWith(")")));
  return "/" + segments.join("/");
}

function routePatternToRegex(route: string): RegExp {
  const escaped = route
    .replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
    .replace(/\\\[\.\.\.[^\]]+\\\]/g, ".+")
    .replace(/\\\[[^\]]+\\\]/g, "[^/]+");
  return new RegExp(`^${escaped}$`);
}

describe("navigation hardening", () => {
  it("shows platform management only for superadmin role", () => {
    const superadmin = getNavigationForRoles(["superadmin"]);
    const legacyAdmin = getNavigationForRoles(["admin"]);
    const tenantAdmin = getNavigationForRoles(["teacher"]);

    expect(superadmin.some((group) => group.label === "Platform Management")).toBe(true);
    expect(legacyAdmin.some((group) => group.label === "Platform Management")).toBe(true);
    expect(tenantAdmin.some((group) => group.label === "Platform Management")).toBe(false);
  });

  it("contains no demo/debug placeholder wording", () => {
    const labels = [
      ...NAVIGATION,
      ...STUDENT_NAVIGATION,
      ...TEACHER_NAVIGATION,
      ...DEAN_NAVIGATION,
      ...SUPERADMIN_NAVIGATION,
    ]
      .flatMap((group) => group.items)
      .flatMap((item) => [item.label, ...(item.children ?? []).map((child) => child.label)]);

    for (const label of labels) {
      const normalized = label.toLowerCase();
      expect(normalized).not.toContain("demo");
      expect(normalized).not.toContain("coming soon");
      expect(normalized).not.toContain("test");
      expect(normalized).not.toContain("internal");
      expect(normalized).not.toContain("example");
    }
  });

  it("does not contain dead links", () => {
    const appRoot = path.join(process.cwd(), "app");
    const routes = collectPageFiles(appRoot).map((filePath) => routeFromPageFile(appRoot, filePath));
    const routeRegexes = routes.map(routePatternToRegex);
    const hrefs = collectHrefs([
      ...NAVIGATION,
      ...STUDENT_NAVIGATION,
      ...TEACHER_NAVIGATION,
      ...DEAN_NAVIGATION,
      ...SUPERADMIN_NAVIGATION,
    ] as Array<{ items: Array<{ href: string; children?: Array<{ href: string }> }> }>);

    for (const href of hrefs) {
      const candidates = toCandidatePaths(href);
      expect(candidates.some((candidate) => routeRegexes.some((pattern) => pattern.test("/" + candidate)))).toBe(true);
    }
  });
});
