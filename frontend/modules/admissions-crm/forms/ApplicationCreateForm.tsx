"use client";

import { useState } from "react";

export interface ApplicationCreateValues {
  applicant_id: number;
  application_ref: string;
  program_code: string;
  intake_term: string;
}

export function ApplicationCreateForm({ onSubmit }: { onSubmit?: (values: ApplicationCreateValues) => void }) {
  const [values, setValues] = useState<ApplicationCreateValues>({
    applicant_id: 0,
    application_ref: "",
    program_code: "",
    intake_term: "",
  });
  const [error, setError] = useState<string | null>(null);

  const submit = () => {
    if (values.applicant_id <= 0 || !values.application_ref.trim() || !values.program_code.trim() || !values.intake_term.trim()) {
      setError("applicant_id, application_ref, program_code, intake_term are required");
      return;
    }
    setError(null);
    onSubmit?.(values);
  };

  return (
    <section className="rounded-xl border bg-card p-4" data-testid="acrm-application-create-form">
      <h3 className="text-base font-semibold">ApplicationCreateForm</h3>
      {error ? <p className="mt-2 text-sm text-red-700">{error}</p> : null}
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <input className="rounded border px-3 py-2" placeholder="applicant_id" type="number" value={values.applicant_id} onChange={(e) => setValues({ ...values, applicant_id: Number(e.target.value) })} />
        <input className="rounded border px-3 py-2" placeholder="application_ref" value={values.application_ref} onChange={(e) => setValues({ ...values, application_ref: e.target.value })} />
        <input className="rounded border px-3 py-2" placeholder="program_code" value={values.program_code} onChange={(e) => setValues({ ...values, program_code: e.target.value })} />
        <input className="rounded border px-3 py-2" placeholder="intake_term" value={values.intake_term} onChange={(e) => setValues({ ...values, intake_term: e.target.value })} />
      </div>
      <button type="button" className="mt-3 rounded border px-3 py-2 text-sm" onClick={submit}>Create application</button>
    </section>
  );
}
