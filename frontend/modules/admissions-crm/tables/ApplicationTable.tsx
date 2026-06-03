"use client";

import type { ApplicationRecord } from "../hooks";

export function ApplicationTable({ applications }: { applications: ApplicationRecord[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="acrm-application-table">
      <h3 className="mb-3 text-base font-semibold">Application Table</h3>
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b text-xs uppercase text-muted-foreground">
            <th className="py-2">Ref</th>
            <th className="py-2">Program</th>
            <th className="py-2">Intake</th>
            <th className="py-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {applications.map((application) => (
            <tr key={application.id} className="border-b last:border-0">
              <td className="py-2 font-mono text-xs">{application.application_ref}</td>
              <td className="py-2">{application.program_code}</td>
              <td className="py-2">{application.intake_term}</td>
              <td className="py-2">{application.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
