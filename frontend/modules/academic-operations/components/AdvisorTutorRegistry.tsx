import { ACADEMIC_OPERATIONS_BOUNDARY_LABELS } from '../boundaryLabels';
import type { AdvisorTutorAssignment } from '../types';

export function AdvisorTutorRegistry({ assignments }: { assignments: AdvisorTutorAssignment[] }) {
  return (
    <section className="rounded-lg border p-4" data-testid="advisor-tutor-registry">
      <h3 className="text-sm font-semibold">Advisor / tutor assignments</h3>
      <p className="mt-1 text-sm text-muted-foreground">{ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noHiddenScore}</p>
      {assignments.length ? (
        <ul className="mt-3 space-y-2 text-sm">
          {assignments.map((assignment) => (
            <li key={assignment.id} className="rounded-md border p-3">
              <div className="font-medium">{assignment.assignment_code}</div>
              <div className="text-muted-foreground">student ref {assignment.student_ref ?? 'n/a'} · faculty ref {assignment.faculty_ref ?? 'n/a'}</div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">No advisor or tutor assignment metadata yet.</p>
      )}
    </section>
  );
}