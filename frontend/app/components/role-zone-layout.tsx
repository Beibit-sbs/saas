"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/shared/utils/cn";

type RoleNavItem = {
  href: string;
  label: string;
};

type RoleZoneLayoutProps = {
  zoneTitle: string;
  navItems: RoleNavItem[];
  backHref?: string | null;
  backLabel?: string;
  children: React.ReactNode;
};

export function RoleZoneLayout({ zoneTitle, navItems, backHref = "/console", backLabel = "Back to Console", children }: RoleZoneLayoutProps) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,rgba(232,246,250,0.95)_0%,rgba(244,249,252,0.92)_18%,rgba(248,250,252,1)_100%)] text-foreground">
      <header className="sticky top-0 z-10 border-b border-border/70 bg-background/82 backdrop-blur-xl">
        <div className="mx-auto max-w-6xl px-4 py-4 sm:px-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="m-0 text-[0.72rem] font-semibold uppercase tracking-[0.2em] text-primary/80">
                Role Workspace
              </p>
              <h2 className="mt-1 text-lg font-semibold text-foreground">{zoneTitle}</h2>
            </div>
            {backHref ? (
              <Link
                href={backHref}
                className="rounded-full border border-border/70 bg-card/80 px-4 py-2 text-sm font-medium text-foreground shadow-sm transition hover:border-primary/35 hover:bg-accent"
              >
                {backLabel}
              </Link>
            ) : null}
          </div>
          <nav aria-label={`${zoneTitle} navigation`} className="mt-4 flex flex-wrap gap-2">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "rounded-full border px-3.5 py-1.5 text-sm font-medium transition",
                  pathname === item.href || pathname.startsWith(`${item.href}/`)
                    ? "border-primary/40 bg-primary text-primary-foreground shadow-[0_10px_24px_rgba(8,145,178,0.22)]"
                    : "border-border/70 bg-card/80 text-foreground hover:border-primary/35 hover:bg-accent",
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      {children}
    </div>
  );
}
