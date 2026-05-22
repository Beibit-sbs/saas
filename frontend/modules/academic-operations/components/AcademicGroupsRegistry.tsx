import type { AcademicGroup } from '../types';

export function AcademicGroupsRegistry({ groups }: { groups: AcademicGroup[] }) {
  return (
    <section className="rounded-lg border p-4" data-testid="academic-groups-registry">
      <h3 className="text-sm font-semibold">Academic group metadata</h3>
      {groups.length ? (
        <ul className="mt-3 space-y-2 text-sm">
          {groups.map((group) => (
            <li key={group.id} className="rounded-md border p-3">
              <div className="font-medium">{group.group_name}</div>
              <div className="text-muted-foreground">{group.group_code} · status {group.status}</div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">No academic group metadata yet.</p>
      )}
    </section>
  );
}