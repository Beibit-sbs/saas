"use client";

import { useState } from "react";

export interface LeadCreateValues {
  lead_ref: string;
  full_name: string;
  email: string;
  phone?: string;
  source_channel?: string;
}

export function LeadCreateForm({ onSubmit }: { onSubmit?: (values: LeadCreateValues) => void }) {
  const [values, setValues] = useState<LeadCreateValues>({
    lead_ref: "",
    full_name: "",
    email: "",
    phone: "",
    source_channel: "direct",
  });
  const [error, setError] = useState<string | null>(null);

  const submit = () => {
    if (!values.lead_ref.trim() || !values.full_name.trim() || !values.email.trim()) {
      setError("lead_ref, full_name, and email are required");
      return;
    }
    setError(null);
    onSubmit?.(values);
  };

  return (
    <section className="rounded-xl border bg-card p-4" data-testid="acrm-lead-create-form">
      <h3 className="text-base font-semibold">LeadCreateForm</h3>
      {error ? <p className="mt-2 text-sm text-red-700">{error}</p> : null}
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <input className="rounded border px-3 py-2" placeholder="lead_ref" value={values.lead_ref} onChange={(e) => setValues({ ...values, lead_ref: e.target.value })} />
        <input className="rounded border px-3 py-2" placeholder="full_name" value={values.full_name} onChange={(e) => setValues({ ...values, full_name: e.target.value })} />
        <input className="rounded border px-3 py-2" placeholder="email" value={values.email} onChange={(e) => setValues({ ...values, email: e.target.value })} />
        <input className="rounded border px-3 py-2" placeholder="phone" value={values.phone} onChange={(e) => setValues({ ...values, phone: e.target.value })} />
      </div>
      <button type="button" className="mt-3 rounded border px-3 py-2 text-sm" onClick={submit}>Create lead</button>
    </section>
  );
}
