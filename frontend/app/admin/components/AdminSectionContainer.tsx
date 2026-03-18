"use client";

import React, { useEffect } from "react";

const STYLE_ID = "admin-section-container-styles";
const STYLE_CSS = `
.admin-section-container {
  padding: 1.15rem 1.25rem 1.5rem;
  background: transparent;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}
.admin-section-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
  color: #17212f;
  padding-bottom: 0.8rem;
  border-bottom: 1px solid #e3e8ef;
}
.admin-section-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  max-width: 1360px;
  width: 100%;
  margin: 0 auto;
}
@media (max-width: 780px) {
  .admin-section-container {
    padding: 0.9rem 0.8rem 1.1rem;
  }
}
`;

export interface AdminSectionContainerProps {
  children: React.ReactNode;
  title?: string;
}

export function AdminSectionContainer({
  children,
  title,
}: AdminSectionContainerProps) {
  useEffect(() => {
    if (typeof document === "undefined") return;
    if (document.getElementById(STYLE_ID)) return;
    const el = document.createElement("style");
    el.id = STYLE_ID;
    el.textContent = STYLE_CSS;
    document.head.appendChild(el);
  }, []);

  return (
    <section className="admin-section-container">
      {title && <h2 className="admin-section-title">{title}</h2>}
      <div className="admin-section-content">{children}</div>
    </section>
  );
}
