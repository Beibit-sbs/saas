"use client";

import { usePathname } from "next/navigation";
import SessionPanel from "./SessionPanel";
import LanguageSwitcher from "./LanguageSwitcher";
import HelpAssistant from "./HelpAssistant";

/**
 * Root-level overlay components (SessionPanel, LanguageSwitcher, HelpAssistant)
 * are only relevant for legacy /admin pages.
 * The new /console layout has its own AppTopbar and sidebar controls.
 */
export default function RootLayoutOverlays() {
  const pathname = usePathname();
  if (!pathname?.startsWith("/admin")) {
    return null;
  }
  return (
    <>
      <SessionPanel />
      <LanguageSwitcher />
      <HelpAssistant />
    </>
  );
}
