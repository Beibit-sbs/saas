"use client";

import type { ApplicantRecord } from "../hooks";

export function ApplicantTable({ applicants }: { applicants: ApplicantRecord[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="acrm-applicant-table">
      <h3 className="mb-3 text-base font-semibold">Applicant Table</h3>
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
          {applicants.map((applicant) => (
            <tr key={applicant.id} className="border-b last:border-0">
              <td className="py-2 font-mono text-xs">{applicant.applicant_ref}</td>
              <td className="py-2">{applicant.full_name}</td>
              <td className="py-2">{applicant.email}</td>
              <td className="py-2">{applicant.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
