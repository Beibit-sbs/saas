"use client";

import Link from "next/link";
import type { ReactNode } from "react";

const nav = [
  { href: "/console/admissions", title: "Overview" },
  { href: "/console/admissions/leads", title: "Leads" },
  { href: "/console/admissions/applicants", title: "Applicants" },
  { href: "/console/admissions/applications", title: "Applications" },
  { href: "/console/admissions/workflows", title: "Workflows" },
  { href: "/console/admissions/audit", title: "Audit" },
  { href: "/console/admissions/dashboard", title: "Dashboard" },
];

export function AdmissionsPageLayout({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <main className="space-y-6 p-6" data-testid="acrm-page-layout">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold">{title}</h1>
        <p className="text-sm text-muted-foreground">{subtitle}</p>
      </header>
      <nav className="flex flex-wrap gap-2" aria-label="Admissions navigation">
        {nav.map((item) => (
          <Link key={item.href} href={item.href} className="rounded-full border px-3 py-1 text-xs hover:bg-slate-50">
            {item.title}
          </Link>
        ))}
      </nav>
      {children}
    </main>
  );
}
