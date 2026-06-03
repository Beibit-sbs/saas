"use client";

import { useState } from "react";

export interface LeadEditValues {
  full_name: string;
  email: string;
  phone?: string;
  source_channel?: string;
  note?: string;
}

export function LeadEditForm({
  initial,
  onSubmit,
}: {
  initial?: LeadEditValues;
  onSubmit?: (values: LeadEditValues) => void;
}) {
  const [values, setValues] = useState<LeadEditValues>(
    initial ?? { full_name: "", email: "", phone: "", source_channel: "direct", note: "" },
  );
  const [error, setError] = useState<string | null>(null);

  const submit = () => {
    if (!values.full_name.trim() || !values.email.trim()) {
      setError("full_name and email are required");
      return;
    }
    if (values.note && values.note.length > 500) {
      setError("note exceeds 500 characters");
      return;
    }
    setError(null);
    onSubmit?.(values);
  };

  return (
    <section className="rounded-xl border bg-card p-4" data-testid="acrm-lead-edit-form">
      <h3 className="text-base font-semibold">LeadEditForm</h3>
      {error ? <p className="mt-2 text-sm text-red-700">{error}</p> : null}
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <input className="rounded border px-3 py-2" placeholder="full_name" value={values.full_name} onChange={(e) => setValues({ ...values, full_name: e.target.value })} />
        <input className="rounded border px-3 py-2" placeholder="email" value={values.email} onChange={(e) => setValues({ ...values, email: e.target.value })} />
        <input className="rounded border px-3 py-2" placeholder="phone" value={values.phone} onChange={(e) => setValues({ ...values, phone: e.target.value })} />
        <textarea className="rounded border px-3 py-2" placeholder="note" value={values.note} onChange={(e) => setValues({ ...values, note: e.target.value })} />
      </div>
      <button type="button" className="mt-3 rounded border px-3 py-2 text-sm" onClick={submit}>Save lead</button>
    </section>
  );
}
