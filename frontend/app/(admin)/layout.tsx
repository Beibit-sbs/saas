import { ReactNode } from "react";
import "@/app/admin-console.css";
import { Providers } from "@/shared/ui/providers";
import { AppSidebar } from "@/shared/ui/app-sidebar";
import { AppTopbar } from "@/shared/ui/app-topbar";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <Providers>
      <div className="flex h-screen overflow-hidden">
        <AppSidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <AppTopbar />
          <main className="flex-1 overflow-y-auto p-6 bg-muted/20">{children}</main>
        </div>
      </div>
    </Providers>
  );
}
