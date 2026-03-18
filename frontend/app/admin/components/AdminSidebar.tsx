"use client";

import { useEffect } from "react";

const SIDEBAR_STYLE_ID = "admin-sidebar-styles";
const SIDEBAR_STYLE_CSS = `
.admin-sidebar {
  background: #f7f9fc;
  border-right: 1px solid #e3e8ef;
  width: 252px;
  height: calc(100vh - 74px);
  overflow-y: auto;
  position: sticky;
  top: 74px;
  z-index: 30;
}
.admin-sidebar-nav {
  display: flex;
  flex-direction: column;
  padding: 0.9rem 0.7rem 1rem;
  gap: 0.3rem;
}
.admin-sidebar-item {
  all: unset;
  display: flex;
  align-items: center;
  gap: 0.68rem;
  padding: 0.62rem 0.72rem;
  font-size: 0.9rem;
  color: #354052;
  cursor: pointer;
  border: 1px solid transparent;
  transition: background-color 0.18s ease, color 0.18s ease, border-color 0.18s ease;
  border-radius: 10px;
  text-align: left;
  width: 100%;
  box-sizing: border-box;
  font-weight: 500;
}
.admin-sidebar-item:hover {
  background-color: #eef3f9;
  border-color: #dce4ef;
  color: #17212f;
}
.admin-sidebar-item.active {
  background-color: #e9f0fb;
  border-color: #cddbf0;
  color: #1f3250;
  box-shadow: inset 2px 0 0 #3b82f6;
  font-weight: 600;
}
.admin-sidebar-icon {
  width: 1.2rem;
  text-align: center;
  font-size: 0.92rem;
  flex-shrink: 0;
  opacity: 0.9;
}
.admin-sidebar-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.2;
}
.admin-sidebar::-webkit-scrollbar {
  width: 6px;
}
.admin-sidebar::-webkit-scrollbar-track {
  background: transparent;
}
.admin-sidebar::-webkit-scrollbar-thumb {
  background: #c7d1de;
  border-radius: 3px;
}
.admin-sidebar::-webkit-scrollbar-thumb:hover {
  background: #adb8c7;
}
`;

export interface AdminSection {
  id: string;
  label: string;
  icon?: string;
}

export interface AdminSidebarProps {
  sections: AdminSection[];
  activeSection: string;
  onSectionClick: (sectionId: string) => void;
}

export function AdminSidebar({
  sections,
  activeSection,
  onSectionClick,
}: AdminSidebarProps) {
  useEffect(() => {
    if (typeof document === "undefined") return;
    if (document.getElementById(SIDEBAR_STYLE_ID)) return;
    const el = document.createElement("style");
    el.id = SIDEBAR_STYLE_ID;
    el.textContent = SIDEBAR_STYLE_CSS;
    document.head.appendChild(el);
  }, []);

  return (
    <aside className="admin-sidebar">
      <nav className="admin-sidebar-nav">
        {sections.map((section) => (
          <button
            key={section.id}
            onClick={() => onSectionClick(section.id)}
            className={`admin-sidebar-item ${
              activeSection === section.id ? "active" : ""
            }`}
            data-testid={`sidebar-section-${section.id}`}
          >
            {section.icon && <span className="admin-sidebar-icon">{section.icon}</span>}
            <span className="admin-sidebar-label">{section.label}</span>
          </button>
        ))}
      </nav>
    </aside>
  );
}
