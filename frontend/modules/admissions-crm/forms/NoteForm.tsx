"use client";

import { useState } from "react";

export interface NoteValues {
  entity_type: "lead" | "applicant" | "application";
  entity_id: number;
  note: string;
}

export function NoteForm({ onSubmit }: { onSubmit?: (values: NoteValues) => void }) {
  const [values, setValues] = useState<NoteValues>({
    entity_type: "lead",
    entity_id: 0,
    note: "",
  });
  const [error, setError] = useState<string | null>(null);

  const submit = () => {
    if (values.entity_id <= 0 || !values.note.trim()) {
      setError("entity_id and note are required");
      return;
    }
    if (values.note.length > 500) {
      setError("note exceeds 500 characters");
      return;
    }
    setError(null);
    onSubmit?.(values);
  };

  return (
    <section className="rounded-xl border bg-card p-4" data-testid="acrm-note-form">
      <h3 className="text-base font-semibold">NoteForm</h3>
      {error ? <p className="mt-2 text-sm text-red-700">{error}</p> : null}
      <div className="mt-3 grid gap-3">
        <select className="rounded border px-3 py-2" value={values.entity_type} onChange={(e) => setValues({ ...values, entity_type: e.target.value as "lead" | "applicant" | "application" })}>
          <option value="lead">lead</option>
          <option value="applicant">applicant</option>
          <option value="application">application</option>
        </select>
        <input className="rounded border px-3 py-2" placeholder="entity_id" type="number" value={values.entity_id} onChange={(e) => setValues({ ...values, entity_id: Number(e.target.value) })} />
        <textarea className="rounded border px-3 py-2" placeholder="note" value={values.note} onChange={(e) => setValues({ ...values, note: e.target.value })} />
      </div>
      <button type="button" className="mt-3 rounded border px-3 py-2 text-sm" onClick={submit}>Save note</button>
    </section>
  );
}
