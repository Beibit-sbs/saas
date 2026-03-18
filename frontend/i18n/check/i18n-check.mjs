import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

/**
 * Compare locale dictionaries against ru canonical keys.
 */
function readKeys(relativePath) {
  const currentDir = path.dirname(fileURLToPath(import.meta.url));
  const fullPath = path.resolve(currentDir, relativePath);
  const content = fs.readFileSync(fullPath, "utf-8");
  const keyRegex = /"([^"]+)":/g;
  const keys = new Set();

  for (const match of content.matchAll(keyRegex)) {
    keys.add(match[1]);
  }

  return keys;
}

function checkScope(scopeName, canonicalKeys, locales) {
  const issues = [];

  for (const [locale, localeKeys] of Object.entries(locales)) {

    for (const key of canonicalKeys) {
      if (!localeKeys.has(key)) {
        issues.push(`[${scopeName}] missing key in ${locale}: ${key}`);
      }
    }

    for (const key of localeKeys) {
      if (!canonicalKeys.has(key)) {
        issues.push(`[${scopeName}] extra key in ${locale}: ${key}`);
      }
    }
  }

  return issues;
}

const errors = [
  ...checkScope("common", readKeys("../common/ru.ts"), {
    en: readKeys("../common/en.ts"),
    kk: readKeys("../common/kk.ts"),
  }),
  ...checkScope("admin", readKeys("../admin/ru.ts"), {
    en: readKeys("../admin/en.ts"),
    kk: readKeys("../admin/kk.ts"),
  }),
];

if (errors.length > 0) {
  console.error("i18n parity check failed:");
  for (const issue of errors) {
    console.error(`- ${issue}`);
  }
  process.exit(1);
}

console.log("i18n parity check passed (ru/en/kk).");
