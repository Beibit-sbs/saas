"use client";

import React, { useEffect } from "react";
import { AdminHeader } from "./AdminHeader";
import { AdminSidebar, type AdminSection } from "./AdminSidebar";
import { AdminSectionContainer } from "./AdminSectionContainer";

export type { AdminSection } from "./AdminSidebar";

const SHELL_STYLE_ID = "admin-shell-layout-styles";
const SHELL_STYLE_CSS = `
.admin-shell-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f6f8fb;
}
.admin-shell-container {
  display: flex;
  flex: 1;
  overflow: hidden;
}
.admin-shell-main {
  flex: 1;
  display: flex;
  overflow-y: auto;
  background: #f8fafc;
}
`;

export interface AdminShellProps {
  children: React.ReactNode;
  activeTab: string;
  onTabChange: (tab: string) => void;
  sections: AdminSection[];
  platformName?: string;
  headerControls?: React.ReactNode;
}

export function AdminShell({
  children,
  activeTab,
  onTabChange,
  sections,
  platformName = "Platform",
  headerControls,
}: AdminShellProps) {
  useEffect(() => {
    if (typeof document === "undefined") return;
    if (document.getElementById(SHELL_STYLE_ID)) return;
    const el = document.createElement("style");
    el.id = SHELL_STYLE_ID;
    el.textContent = SHELL_STYLE_CSS;
    document.head.appendChild(el);
  }, []);

  return (
    <div className="admin-shell-layout">
      <AdminHeader platformName={platformName} rightContent={headerControls} />
      <div className="admin-shell-container">
        <AdminSidebar
          sections={sections}
          activeSection={activeTab}
          onSectionClick={onTabChange}
        />
        <main className="admin-shell-main">
          <AdminSectionContainer>{children}</AdminSectionContainer>
        </main>
      </div>
    </div>
  );
}
