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
.admin-shell-layout.executive {
  background:
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.08), transparent 32%),
    linear-gradient(180deg, #f8fafe 0%, #f2f6fc 100%);
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
.admin-shell-layout.executive .admin-shell-main {
  background: linear-gradient(180deg, #fbfdff 0%, #f4f8fe 100%);
}
.admin-shell-layout.executive .admin-sidebar-item:not(.active) {
  opacity: 1;
  color: #2f4563;
}
.admin-shell-layout.executive .admin-sidebar-item.active {
  background: #d7e9ff;
  border-color: #8bb2e2;
  color: #0f2d52;
  box-shadow: inset 4px 0 0 #2563eb;
}
.admin-shell-layout.executive .admin-sidebar-item:hover:not(.active) {
  background: #edf4ff;
  border-color: #bed2ec;
  color: #1c385b;
}
`;

export interface AdminShellProps {
  children: React.ReactNode;
  activeTab: string;
  onTabChange: (tab: string) => void;
  sections: AdminSection[];
  platformName?: string;
  headerControls?: React.ReactNode;
  presentationMode?: boolean;
  adminSubtitle?: string;
  executiveSubtitle?: string;
}

export function AdminShell({
  children,
  activeTab,
  onTabChange,
  sections,
  platformName = "Platform",
  headerControls,
  presentationMode = false,
  adminSubtitle,
  executiveSubtitle,
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
    <div className={`admin-shell-layout ${presentationMode ? "executive" : ""}`}>
      <AdminHeader
        platformName={platformName}
        rightContent={headerControls}
        presentationMode={presentationMode}
        adminSubtitle={adminSubtitle}
        executiveSubtitle={executiveSubtitle}
      />
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
