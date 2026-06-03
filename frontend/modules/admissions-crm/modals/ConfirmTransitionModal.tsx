"use client";

export function ConfirmTransitionModal({
  from,
  to,
  onConfirm,
}: {
  from: string;
  to: string;
  onConfirm?: () => void;
}) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="acrm-confirm-transition-modal">
      <h3 className="text-base font-semibold">Confirm transition</h3>
      <p className="mt-2 text-sm text-muted-foreground">
        Transition from <strong>{from}</strong> to <strong>{to}</strong> requires human approval.
      </p>
      <button type="button" className="mt-3 rounded border px-3 py-2 text-sm" onClick={onConfirm}>
        Confirm
      </button>
    </section>
  );
}
