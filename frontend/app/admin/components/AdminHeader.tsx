"use client";

import { useEffect } from "react";
import type { ReactNode } from "react";

const HEADER_STYLE_ID = "admin-header-styles";
const HEADER_STYLE_CSS = `
.admin-header {
  background: rgba(255, 255, 255, 0.96);
  border-bottom: 1px solid #e3e8ef;
  padding: 0.95rem 1.35rem;
  position: sticky;
  top: 0;
  z-index: 40;
  backdrop-filter: blur(8px);
  box-shadow: 0 1px 0 rgba(15, 23, 42, 0.03);
}
.admin-header.executive {
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.98), rgba(246, 250, 255, 0.96));
}
.admin-header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  max-width: 1560px;
  margin: 0 auto;
}
.admin-header-left {
  display: flex;
  flex-direction: column;
  gap: 0.18rem;
  min-width: 0;
}
.admin-header-title {
  font-size: 1.12rem;
  font-weight: 700;
  margin: 0;
  color: #162032;
  line-height: 1.2;
  letter-spacing: 0.01em;
}
.admin-header-subtitle {
  font-size: 0.76rem;
  color: #64748b;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.admin-header-right {
  display: flex;
  gap: 0.7rem;
  align-items: center;
  min-width: 0;
}
.admin-presentation-toggle {
  border: 1px solid #b7cae5;
  background: #ffffff;
  color: #143355;
  border-radius: 999px;
  padding: 0.34rem 0.72rem;
  font-size: 0.76rem;
  font-weight: 700;
  cursor: pointer;
}
.admin-presentation-toggle:hover {
  background: #eef4ff;
  border-color: #9bbbe3;
  color: #102d4e;
}
.admin-presentation-toggle[aria-pressed="true"] {
  background: #dcecff;
  border-color: #8fb5e4;
  color: #0f2d52;
}
.admin-presentation-toggle:focus-visible {
  outline: 3px solid rgba(37, 99, 235, 0.32);
  outline-offset: 2px;
}
.admin-presentation-toggle:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
`;

export interface AdminHeaderProps {
  platformName?: string;
  rightContent?: ReactNode;
  presentationMode?: boolean;
  adminSubtitle?: string;
  executiveSubtitle?: string;
}

export function AdminHeader({
  platformName = "Platform",
  rightContent,
  presentationMode = false,
  adminSubtitle = "Admin Console",
  executiveSubtitle = "Executive Briefing",
}: AdminHeaderProps) {
  useEffect(() => {
    if (typeof document === "undefined") return;
    if (document.getElementById(HEADER_STYLE_ID)) return;
    const el = document.createElement("style");
    el.id = HEADER_STYLE_ID;
    el.textContent = HEADER_STYLE_CSS;
    document.head.appendChild(el);
  }, []);

  return (
    <header className={`admin-header ${presentationMode ? "executive" : ""}`}>
      <div className="admin-header-content">
        <div className="admin-header-left">
          <h1 className="admin-header-title">{platformName}</h1>
          <span className="admin-header-subtitle">
            {presentationMode ? executiveSubtitle : adminSubtitle}
          </span>
        </div>
        <div className="admin-header-right">{rightContent}</div>
      </div>
    </header>
  );
}
