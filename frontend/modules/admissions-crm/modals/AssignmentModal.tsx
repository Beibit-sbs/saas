"use client";

import { useState } from "react";

export function AssignmentModal({ onSubmit }: { onSubmit?: (value: { counselor_user_id: string; reason: string }) => void }) {
  const [counselorUserId, setCounselorUserId] = useState("");
  const [reason, setReason] = useState("");

  return (
    <section className="rounded-xl border bg-card p-4" data-testid="acrm-assignment-modal">
      <h3 className="text-base font-semibold">Assignment</h3>
      <div className="mt-3 grid gap-3">
        <input
          value={counselorUserId}
          onChange={(event) => setCounselorUserId(event.target.value)}
          className="rounded border px-3 py-2"
          placeholder="Counselor user id"
        />
        <textarea
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          className="rounded border px-3 py-2"
          placeholder="Reason"
        />
        <button
          type="button"
          className="rounded border px-3 py-2 text-sm"
          onClick={() => onSubmit?.({ counselor_user_id: counselorUserId.trim(), reason: reason.trim() })}
        >
          Save assignment
        </button>
      </div>
    </section>
  );
}
