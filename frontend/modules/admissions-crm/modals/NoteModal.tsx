"use client";

import { useState } from "react";

export function NoteModal({ onSubmit }: { onSubmit?: (value: { note: string }) => void }) {
  const [note, setNote] = useState("");

  return (
    <section className="rounded-xl border bg-card p-4" data-testid="acrm-note-modal">
      <h3 className="text-base font-semibold">Add Note</h3>
      <textarea
        value={note}
        onChange={(event) => setNote(event.target.value)}
        className="mt-3 w-full rounded border px-3 py-2"
        placeholder="Operational note"
      />
      <button
        type="button"
        className="mt-3 rounded border px-3 py-2 text-sm"
        onClick={() => onSubmit?.({ note: note.trim() })}
      >
        Save note
      </button>
    </section>
  );
}
