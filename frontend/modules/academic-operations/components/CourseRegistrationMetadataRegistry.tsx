import type { CourseRegistrationMetadata } from '../types';

export function CourseRegistrationMetadataRegistry({ items }: { items: CourseRegistrationMetadata[] }) {
  return (
    <section className="rounded-lg border p-4" data-testid="course-registration-metadata-registry">
      <h3 className="text-sm font-semibold">Course registration metadata</h3>
      {items.length ? (
        <ul className="mt-3 space-y-2 text-sm">
          {items.map((item) => (
            <li key={item.id} className="rounded-md border p-3">
              <div className="font-medium">{item.student_ref ?? 'opaque student ref'}</div>
              <div className="text-muted-foreground">course ref {item.course_ref ?? 'n/a'} · canonical {item.canonical_module_ref ?? 'n/a'}</div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">No course registration metadata yet.</p>
      )}
    </section>
  );
}