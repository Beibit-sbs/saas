"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAVIGATION } from "@/shared/config/navigation";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { cn } from "@/shared/utils/cn";
import { GraduationCap } from "lucide-react";

export function AppSidebar() {
  const pathname = usePathname();
  const { hasPermission } = usePermissions();

  return (
    <aside className="flex h-screen w-60 flex-col border-r bg-sidebar">
      <div className="flex h-14 items-center gap-2 border-b px-4">
        <GraduationCap className="h-5 w-5 text-primary" />
        <span className="font-semibold text-sm">EduAdmin</span>
      </div>

      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-4">
        {NAVIGATION.map((group) => {
          const visibleItems = group.items.filter((item) => (item.permission ? hasPermission(item.permission) : true));
          if (visibleItems.length === 0) return null;
          return (
            <div key={group.label}>
              <p className="mb-1 px-2 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                {group.label}
              </p>
              {visibleItems.map((item) => {
                const Icon = item.icon;
                const active = pathname === item.href || pathname.startsWith(item.href + "/");
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm transition-colors",
                      active
                        ? "bg-primary/10 text-primary font-medium"
                        : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                    )}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          );
        })}
      </nav>
    </aside>
  );
}
