import type { SummerSemesterTerm } from '../types';

export function SummerSemesterRegistry({ terms }: { terms: SummerSemesterTerm[] }) {
  return (
    <section className="rounded-lg border p-4" data-testid="summer-semester-registry">
      <h3 className="text-sm font-semibold">Summer semester terms</h3>
      {terms.length ? (
        <ul className="mt-3 space-y-2 text-sm">
          {terms.map((term) => (
            <li key={term.id} className="rounded-md border p-3">
              <div className="font-medium">{term.display_name}</div>
              <div className="text-muted-foreground">{term.term_code} · calendar ref {term.calendar_ref ?? 'n/a'}</div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">No summer semester metadata yet.</p>
      )}
    </section>
  );
}