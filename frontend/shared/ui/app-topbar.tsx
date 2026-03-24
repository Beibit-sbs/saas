"use client";

import { useAdminAuth } from "@/shared/auth/hooks";
import { Button } from "./button";
import { LogOut, User } from "lucide-react";

export function AppTopbar() {
  const { user, logout } = useAdminAuth();

  return (
    <header className="flex h-14 items-center justify-end gap-3 border-b bg-background px-4">
      {user && (
        <div className="flex items-center gap-2 text-sm">
          <User className="h-4 w-4 text-muted-foreground" />
          <span className="text-muted-foreground">{user.displayName ?? user.sub}</span>
          {user.tenantId && (
            <span className="rounded bg-muted px-1.5 py-0.5 text-xs text-muted-foreground">
              {user.tenantId}
            </span>
          )}
        </div>
      )}
      <Button variant="ghost" size="sm" onClick={logout} className="gap-1.5 text-muted-foreground">
        <LogOut className="h-4 w-4" />
        Sign out
      </Button>
    </header>
  );
}
