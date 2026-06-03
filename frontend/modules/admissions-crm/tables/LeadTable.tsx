"use client";

import type { LeadRecord } from "../hooks";

export function LeadTable({ leads }: { leads: LeadRecord[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="acrm-lead-table">
      <h3 className="mb-3 text-base font-semibold">Lead Table</h3>
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b text-xs uppercase text-muted-foreground">
            <th className="py-2">Ref</th>
            <th className="py-2">Name</th>
            <th className="py-2">Email</th>
            <th className="py-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {leads.map((lead) => (
            <tr key={lead.id} className="border-b last:border-0">
              <td className="py-2 font-mono text-xs">{lead.lead_ref}</td>
              <td className="py-2">{lead.full_name}</td>
              <td className="py-2">{lead.email}</td>
              <td className="py-2">{lead.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
