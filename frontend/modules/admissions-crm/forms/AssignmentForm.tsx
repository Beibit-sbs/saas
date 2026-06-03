"use client";

import { useState } from "react";

export interface AssignmentValues {
  entity_type: "lead" | "applicant";
  entity_id: number;
  counselor_user_id: string;
  reason: string;
}

export function AssignmentForm({ onSubmit }: { onSubmit?: (values: AssignmentValues) => void }) {
  const [values, setValues] = useState<AssignmentValues>({
    entity_type: "lead",
    entity_id: 0,
    counselor_user_id: "",
    reason: "",
  });
  const [error, setError] = useState<string | null>(null);

  const submit = () => {
    if (values.entity_id <= 0 || !values.counselor_user_id.trim() || !values.reason.trim()) {
      setError("entity_id, counselor_user_id and reason are required");
      return;
    }
    setError(null);
    onSubmit?.(values);
  };

  return (
    <section className="rounded-xl border bg-card p-4" data-testid="acrm-assignment-form">
      <h3 className="text-base font-semibold">AssignmentForm</h3>
      {error ? <p className="mt-2 text-sm text-red-700">{error}</p> : null}
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <select className="rounded border px-3 py-2" value={values.entity_type} onChange={(e) => setValues({ ...values, entity_type: e.target.value as "lead" | "applicant" })}>
          <option value="lead">lead</option>
          <option value="applicant">applicant</option>
        </select>
        <input className="rounded border px-3 py-2" type="number" placeholder="entity_id" value={values.entity_id} onChange={(e) => setValues({ ...values, entity_id: Number(e.target.value) })} />
        <input className="rounded border px-3 py-2" placeholder="counselor_user_id" value={values.counselor_user_id} onChange={(e) => setValues({ ...values, counselor_user_id: e.target.value })} />
        <input className="rounded border px-3 py-2" placeholder="reason" value={values.reason} onChange={(e) => setValues({ ...values, reason: e.target.value })} />
      </div>
      <button type="button" className="mt-3 rounded border px-3 py-2 text-sm" onClick={submit}>Save assignment</button>
    </section>
  );
}
