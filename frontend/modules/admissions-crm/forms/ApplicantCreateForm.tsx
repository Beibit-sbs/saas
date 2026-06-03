"use client";

import { useState } from "react";

export interface ApplicantCreateValues {
  lead_id: number;
  applicant_ref: string;
  full_name: string;
  email: string;
}

export function ApplicantCreateForm({ onSubmit }: { onSubmit?: (values: ApplicantCreateValues) => void }) {
  const [values, setValues] = useState<ApplicantCreateValues>({
    lead_id: 0,
    applicant_ref: "",
    full_name: "",
    email: "",
  });
  const [error, setError] = useState<string | null>(null);

  const submit = () => {
    if (values.lead_id <= 0 || !values.applicant_ref.trim() || !values.full_name.trim() || !values.email.trim()) {
      setError("lead_id, applicant_ref, full_name, and email are required");
      return;
    }
    setError(null);
    onSubmit?.(values);
  };

  return (
    <section className="rounded-xl border bg-card p-4" data-testid="acrm-applicant-create-form">
      <h3 className="text-base font-semibold">ApplicantCreateForm</h3>
      {error ? <p className="mt-2 text-sm text-red-700">{error}</p> : null}
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <input className="rounded border px-3 py-2" placeholder="lead_id" type="number" value={values.lead_id} onChange={(e) => setValues({ ...values, lead_id: Number(e.target.value) })} />
        <input className="rounded border px-3 py-2" placeholder="applicant_ref" value={values.applicant_ref} onChange={(e) => setValues({ ...values, applicant_ref: e.target.value })} />
        <input className="rounded border px-3 py-2" placeholder="full_name" value={values.full_name} onChange={(e) => setValues({ ...values, full_name: e.target.value })} />
        <input className="rounded border px-3 py-2" placeholder="email" value={values.email} onChange={(e) => setValues({ ...values, email: e.target.value })} />
      </div>
      <button type="button" className="mt-3 rounded border px-3 py-2 text-sm" onClick={submit}>Create applicant</button>
    </section>
  );
}
