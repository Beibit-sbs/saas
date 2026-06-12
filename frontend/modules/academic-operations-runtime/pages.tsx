'use client';

import { useQuery } from '@tanstack/react-query';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';
import { academicOperationsRuntimeApi } from './api';
import type {
  AttendanceRuntimeSection,
  AcademicOperationsRuntimeShellSection,
  AcademicRegistryRuntimeSection,
  AssessmentRuntimeSection,
  CurriculumRuntimeSection,
  TimetableRuntimeSection,
} from './types';

function RuntimeSectionCard({
  title,
  section,
  testId,
}: {
  title: string;
  section: AcademicOperationsRuntimeShellSection;
  testId: string;
}) {
  return (
    <section className="rounded-lg border p-4" data-testid={testId}>
      <h2 className="text-lg font-semibold">{title}</h2>
      <div className="mt-2 space-y-1 text-sm">
        <p>
          <span className="font-medium">Owner module:</span> {section.owner_module}
        </p>
        <p>
          <span className="font-medium">Records:</span> {section.records}
        </p>
        <p>
          <span className="font-medium">Read-only:</span> {String(section.read_only)}
        </p>
        <p>
          <span className="font-medium">Aggregator-only:</span> {String(section.aggregator_only)}
        </p>
        <p>
          <span className="font-medium">Sources:</span> {section.source_modules.join(', ')}
        </p>
      </div>
    </section>
  );
}

export function AcademicOperationsRuntimeShellPage() {
  const runtimeShell = useQuery({
    queryKey: ['academic-operations:runtime-shell'],
    queryFn: academicOperationsRuntimeApi.getRuntimeShell,
    staleTime: 30000,
  });

  if (runtimeShell.isPending) {
    return <LoadingState title="Loading Academic Operations runtime shell" />;
  }

  if (runtimeShell.error) {
    return <ErrorState message="Failed to load Academic Operations runtime shell." error={runtimeShell.error} />;
  }

  if (!runtimeShell.data) {
    return <ErrorState message="Academic Operations runtime shell is unavailable." />;
  }

  return (
    <section className="space-y-6" data-testid="academic-operations-runtime-shell">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Academic Operations Runtime Shell</h1>
        <p className="text-sm text-muted-foreground">Read-only aggregator shell for Academic Operations runtime visibility and readiness boundaries.</p>
      </header>

      <section className="grid gap-4 md:grid-cols-2">
        <RuntimeSectionCard title="Runtime Shell Summary" section={runtimeShell.data.runtime_shell_summary} testId="runtime-shell-summary-panel" />
        <RuntimeSectionCard title="Runtime Domain" section={runtimeShell.data.runtime_shell_domain} testId="runtime-shell-domain-panel" />
        <RuntimeSectionCard title="Runtime Surface" section={runtimeShell.data.runtime_shell_runtime} testId="runtime-shell-runtime-panel" />
        <RuntimeSectionCard title="Runtime Integration" section={runtimeShell.data.runtime_shell_integration} testId="runtime-shell-integration-panel" />
        <RuntimeSectionCard title="Runtime Readiness" section={runtimeShell.data.runtime_shell_readiness} testId="runtime-shell-readiness-panel" />
      </section>

      <section className="rounded-lg border p-4" data-testid="academic-operations-runtime-safety">
        <h2 className="text-lg font-semibold">Runtime safety</h2>
        <div className="mt-3 grid gap-2 text-sm md:grid-cols-2">
          <p>Read-only: {String(runtimeShell.data.safety.read_only)}</p>
          <p>Aggregator-only: {String(runtimeShell.data.safety.aggregator_only)}</p>
          <p>Tenant-aware: {String(runtimeShell.data.safety.tenant_aware)}</p>
          <p>SUMMARY_READ required: {String(runtimeShell.data.safety.summary_read_required)}</p>
          <p>Workflow execution enabled: {String(runtimeShell.data.safety.workflow_execution_enabled)}</p>
          <p>Approval execution enabled: {String(runtimeShell.data.safety.approval_execution_enabled)}</p>
          <p>Background jobs enabled: {String(runtimeShell.data.safety.background_jobs_enabled)}</p>
          <p>Provider mutation enabled: {String(runtimeShell.data.safety.provider_mutation_enabled)}</p>
        </div>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm">
          {runtimeShell.data.safety.limitations.map((limitation) => (
            <li key={limitation}>{limitation}</li>
          ))}
        </ul>
      </section>
    </section>
  );
}

function RegistrySectionCard({
  title,
  section,
  testId,
}: {
  title: string;
  section:
    | AcademicRegistryRuntimeSection
    | CurriculumRuntimeSection
    | TimetableRuntimeSection
    | AttendanceRuntimeSection
    | AssessmentRuntimeSection;
  testId: string;
}) {
  return (
    <section className="rounded-lg border p-4" data-testid={testId}>
      <h2 className="text-lg font-semibold">{title}</h2>
      <div className="mt-2 space-y-1 text-sm">
        <p>
          <span className="font-medium">Owner module:</span> {section.owner_module}
        </p>
        <p>
          <span className="font-medium">Records:</span> {section.records}
        </p>
        <p>
          <span className="font-medium">Read-only:</span> {String(section.read_only)}
        </p>
        <p>
          <span className="font-medium">Aggregator-only:</span> {String(section.aggregator_only)}
        </p>
        <p>
          <span className="font-medium">Sources:</span> {section.source_modules.join(', ')}
        </p>
      </div>
    </section>
  );
}

export function AcademicRegistryRuntimePage() {
  const runtime = useQuery({
    queryKey: ['academic-operations:academic-registry-runtime'],
    queryFn: academicOperationsRuntimeApi.getAcademicRegistryRuntime,
    staleTime: 30000,
  });

  if (runtime.isPending) {
    return <LoadingState title="Loading Academic Registry runtime" />;
  }

  if (runtime.error) {
    return <ErrorState message="Failed to load Academic Registry runtime." error={runtime.error} />;
  }

  if (!runtime.data) {
    return <ErrorState message="Academic Registry runtime is unavailable." />;
  }

  return (
    <section className="space-y-6" data-testid="academic-registry-overview-panel">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Academic Registry Runtime</h1>
        <p className="text-sm text-muted-foreground">Read-only Academic Registry runtime for operational visibility and readiness monitoring.</p>
      </header>

      <section className="rounded-lg border p-4" data-testid="academic-registry-statistics-panel">
        <h2 className="text-lg font-semibold">Registry statistics</h2>
        <div className="mt-3 grid gap-2 text-sm md:grid-cols-2">
          <p>Academic periods total: {runtime.data.registry_statistics.academic_periods_total}</p>
          <p>Academic groups total: {runtime.data.registry_statistics.academic_groups_total}</p>
          <p>Curriculum registry total: {runtime.data.registry_statistics.curriculum_registry_total}</p>
          <p>Course catalog linkage total: {runtime.data.registry_statistics.course_catalog_linkage_total}</p>
          <p>Student registry linkage total: {runtime.data.registry_statistics.student_registry_linkage_total}</p>
          <p>Canonical bridge total: {runtime.data.registry_statistics.canonical_bridge_total}</p>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <RegistrySectionCard title="Academic Periods" section={runtime.data.academic_periods} testId="academic-registry-periods-panel" />
        <RegistrySectionCard title="Academic Groups" section={runtime.data.academic_groups} testId="academic-registry-groups-panel" />
        <RegistrySectionCard title="Curriculum Linkage" section={runtime.data.curriculum_linkage} testId="academic-registry-curriculum-panel" />
        <RegistrySectionCard title="Catalog Linkage" section={runtime.data.catalog_linkage} testId="academic-registry-catalog-panel" />
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <section className="rounded-lg border p-4" data-testid="academic-registry-sis-panel">
          <h2 className="text-lg font-semibold">SIS integration</h2>
          <div className="mt-2 space-y-1 text-sm">
            <p>Provider: {runtime.data.sis_status.provider}</p>
            <p>Status: {runtime.data.sis_status.status}</p>
            <p>Mode: {runtime.data.sis_status.integration_mode}</p>
            <p>Ready: {String(runtime.data.sis_status.ready)}</p>
          </div>
        </section>
        <section className="rounded-lg border p-4" data-testid="academic-registry-lms-panel">
          <h2 className="text-lg font-semibold">LMS integration</h2>
          <div className="mt-2 space-y-1 text-sm">
            <p>Provider: {runtime.data.lms_status.provider}</p>
            <p>Status: {runtime.data.lms_status.status}</p>
            <p>Mode: {runtime.data.lms_status.integration_mode}</p>
            <p>Ready: {String(runtime.data.lms_status.ready)}</p>
          </div>
        </section>
      </section>

      <section className="rounded-lg border p-4" data-testid="academic-registry-health-panel">
        <h2 className="text-lg font-semibold">Registry health</h2>
        <p className="mt-2 text-sm">Healthy: {String(runtime.data.health.healthy)}</p>
        <p className="text-sm">Consistency score: {runtime.data.health.consistency_score}</p>
      </section>

      <section className="rounded-lg border p-4" data-testid="academic-registry-readiness-panel">
        <h2 className="text-lg font-semibold">Operational readiness</h2>
        <p className="mt-2 text-sm">Ready for runtime: {String(runtime.data.readiness.ready_for_runtime)}</p>
        <p className="text-sm">Readiness score: {runtime.data.readiness.readiness_score}</p>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
          {runtime.data.readiness.checklist.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </section>
  );
}

export function CurriculumRuntimePage() {
  const runtime = useQuery({
    queryKey: ['academic-operations:curriculum-runtime'],
    queryFn: academicOperationsRuntimeApi.getCurriculumRuntime,
    staleTime: 30000,
  });

  if (runtime.isPending) {
    return <LoadingState title="Loading Curriculum runtime" />;
  }

  if (runtime.error) {
    return <ErrorState message="Failed to load Curriculum runtime." error={runtime.error} />;
  }

  if (!runtime.data) {
    return <ErrorState message="Curriculum runtime is unavailable." />;
  }

  return (
    <section className="space-y-6" data-testid="curriculum-overview-panel">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Curriculum Runtime</h1>
        <p className="text-sm text-muted-foreground">
          Read-only Curriculum runtime for structure, outcomes, prerequisite chains, and readiness visibility.
        </p>
      </header>

      <section className="rounded-lg border p-4" data-testid="curriculum-statistics-panel">
        <h2 className="text-lg font-semibold">Curriculum statistics</h2>
        <div className="mt-3 grid gap-2 text-sm md:grid-cols-2">
          <p>Program structures total: {runtime.data.curriculum_statistics.program_structures_total}</p>
          <p>Curriculum versions total: {runtime.data.curriculum_statistics.curriculum_versions_total}</p>
          <p>Curriculum health score: {runtime.data.curriculum_statistics.curriculum_health_score}</p>
          <p>Course catalog linkage total: {runtime.data.curriculum_statistics.course_catalog_linkage_total}</p>
          <p>Prerequisite chains total: {runtime.data.curriculum_statistics.prerequisite_chains_total}</p>
          <p>Learning outcomes total: {runtime.data.curriculum_statistics.learning_outcomes_total}</p>
          <p>Academic plans total: {runtime.data.curriculum_statistics.academic_plans_total}</p>
          <p>Canonical bridge total: {runtime.data.curriculum_statistics.canonical_bridge_total}</p>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <RegistrySectionCard
          title="Program structures"
          section={runtime.data.program_structures}
          testId="curriculum-program-structures-panel"
        />
        <RegistrySectionCard
          title="Curriculum versions"
          section={runtime.data.curriculum_versions}
          testId="curriculum-versions-panel"
        />
      </section>

      <section className="rounded-lg border p-4" data-testid="curriculum-health-panel">
        <h2 className="text-lg font-semibold">Curriculum health</h2>
        <p className="mt-2 text-sm">Healthy: {String(runtime.data.curriculum_health.healthy)}</p>
        <p className="text-sm">Consistency score: {runtime.data.curriculum_health.consistency_score}</p>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <RegistrySectionCard
          title="Course catalog linkage"
          section={runtime.data.course_catalog_linkage}
          testId="curriculum-catalog-linkage-panel"
        />
        <RegistrySectionCard
          title="Prerequisite chains"
          section={runtime.data.prerequisite_chains}
          testId="curriculum-prerequisites-panel"
        />
      </section>

      <section className="rounded-lg border p-4" data-testid="curriculum-learning-outcomes-panel">
        <h2 className="text-lg font-semibold">Learning outcomes summary</h2>
        <div className="mt-2 space-y-1 text-sm">
          <p>Owner module: {runtime.data.learning_outcomes_summary.owner_module}</p>
          <p>Records: {runtime.data.learning_outcomes_summary.records}</p>
          <p>Read-only: {String(runtime.data.learning_outcomes_summary.read_only)}</p>
          <p>Aggregator-only: {String(runtime.data.learning_outcomes_summary.aggregator_only)}</p>
        </div>
      </section>

      <section className="rounded-lg border p-4" data-testid="curriculum-risks-panel">
        <h2 className="text-lg font-semibold">Curriculum risks</h2>
        <p className="mt-2 text-sm">Risk score: {runtime.data.curriculum_risks.risk_score}</p>
        <p className="text-sm">Open risks: {runtime.data.curriculum_risks.open_risks}</p>
      </section>

      <section className="rounded-lg border p-4" data-testid="curriculum-readiness-panel">
        <h2 className="text-lg font-semibold">Curriculum readiness</h2>
        <p className="mt-2 text-sm">Ready for runtime: {String(runtime.data.curriculum_readiness.ready_for_runtime)}</p>
        <p className="text-sm">Readiness score: {runtime.data.curriculum_readiness.readiness_score}</p>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
          {runtime.data.curriculum_readiness.checklist.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </section>
  );
}

export function TimetableRuntimePage() {
  const runtime = useQuery({
    queryKey: ['academic-operations:timetable-runtime'],
    queryFn: academicOperationsRuntimeApi.getTimetableRuntime,
    staleTime: 30000,
  });

  if (runtime.isPending) {
    return <LoadingState title="Loading Timetable runtime" />;
  }

  if (runtime.error) {
    return <ErrorState message="Failed to load Timetable runtime." error={runtime.error} />;
  }

  if (!runtime.data) {
    return <ErrorState message="Timetable runtime is unavailable." />;
  }

  return (
    <section className="space-y-6" data-testid="timetable-overview-panel">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Timetable Runtime</h1>
        <p className="text-sm text-muted-foreground">
          Read-only timetable runtime for calendar coverage, room utilization, instructor allocation, and conflict visibility.
        </p>
      </header>

      <section className="rounded-lg border p-4" data-testid="timetable-statistics-panel">
        <h2 className="text-lg font-semibold">Timetable statistics</h2>
        <div className="mt-3 grid gap-2 text-sm md:grid-cols-2">
          <p>Course sections total: {runtime.data.timetable_statistics.course_sections_total}</p>
          <p>Schedules total: {runtime.data.timetable_statistics.schedules_total}</p>
          <p>Calendar periods total: {runtime.data.timetable_statistics.calendar_periods_total}</p>
          <p>Rooms total: {runtime.data.timetable_statistics.rooms_total}</p>
          <p>Instructors total: {runtime.data.timetable_statistics.instructors_total}</p>
          <p>Students total: {runtime.data.timetable_statistics.students_total}</p>
          <p>Conflicts total: {runtime.data.timetable_statistics.conflicts_total}</p>
          <p>Capacity alerts total: {runtime.data.timetable_statistics.capacity_alerts_total}</p>
        </div>
      </section>

      <RegistrySectionCard
        title="Academic calendar summary"
        section={runtime.data.academic_calendar_summary}
        testId="academic-calendar-panel"
      />

      <section className="grid gap-4 md:grid-cols-2">
        <section className="rounded-lg border p-4" data-testid="room-utilization-panel">
          <h2 className="text-lg font-semibold">Room utilization</h2>
          <div className="mt-2 space-y-1 text-sm">
            <p>Rooms tracked: {runtime.data.room_utilization.records}</p>
            <p>Utilization rate: {runtime.data.room_utilization.utilization_rate}</p>
            <p>Underutilized rooms: {runtime.data.room_utilization.underutilized_rooms}</p>
            <p>Overloaded rooms: {runtime.data.room_utilization.overloaded_rooms}</p>
          </div>
        </section>
        <section className="rounded-lg border p-4" data-testid="instructor-allocation-panel">
          <h2 className="text-lg font-semibold">Instructor allocation</h2>
          <div className="mt-2 space-y-1 text-sm">
            <p>Instructor records: {runtime.data.instructor_allocation.records}</p>
            <p>Assigned instructors: {runtime.data.instructor_allocation.assigned_instructors}</p>
            <p>Unassigned sections: {runtime.data.instructor_allocation.unassigned_sections}</p>
          </div>
        </section>
      </section>

      <RegistrySectionCard
        title="Student schedule summary"
        section={runtime.data.student_schedule_summary}
        testId="student-schedule-panel"
      />

      <section className="grid gap-4 md:grid-cols-2">
        <section className="rounded-lg border p-4" data-testid="schedule-conflicts-panel">
          <h2 className="text-lg font-semibold">Schedule conflicts</h2>
          <div className="mt-2 space-y-1 text-sm">
            <p>Conflict records: {runtime.data.schedule_conflicts.records}</p>
            <p>Conflict rate: {runtime.data.schedule_conflicts.conflict_rate}</p>
            <p>Critical conflicts: {runtime.data.schedule_conflicts.critical_conflicts}</p>
          </div>
        </section>
        <section className="rounded-lg border p-4" data-testid="capacity-indicators-panel">
          <h2 className="text-lg font-semibold">Capacity indicators</h2>
          <div className="mt-2 space-y-1 text-sm">
            <p>Indicator records: {runtime.data.capacity_indicators.records}</p>
            <p>Over-capacity sections: {runtime.data.capacity_indicators.over_capacity_sections}</p>
            <p>Under-capacity sections: {runtime.data.capacity_indicators.under_capacity_sections}</p>
          </div>
        </section>
      </section>

      <section className="rounded-lg border p-4" data-testid="timetable-health-panel">
        <h2 className="text-lg font-semibold">Timetable health</h2>
        <p className="mt-2 text-sm">Healthy: {String(runtime.data.timetable_health.healthy)}</p>
        <p className="text-sm">Consistency score: {runtime.data.timetable_health.consistency_score}</p>
      </section>

      <section className="rounded-lg border p-4" data-testid="timetable-readiness-panel">
        <h2 className="text-lg font-semibold">Timetable readiness</h2>
        <p className="mt-2 text-sm">Ready for runtime: {String(runtime.data.timetable_readiness.ready_for_runtime)}</p>
        <p className="text-sm">Readiness score: {runtime.data.timetable_readiness.readiness_score}</p>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
          {runtime.data.timetable_readiness.checklist.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </section>
  );
}

export function AttendanceRuntimePage() {
  const runtime = useQuery({
    queryKey: ['academic-operations:attendance-runtime'],
    queryFn: academicOperationsRuntimeApi.getAttendanceRuntime,
    staleTime: 30000,
  });

  if (runtime.isPending) {
    return <LoadingState title="Loading Attendance runtime" />;
  }

  if (runtime.error) {
    return <ErrorState message="Failed to load Attendance runtime." error={runtime.error} />;
  }

  if (!runtime.data) {
    return <ErrorState message="Attendance runtime is unavailable." />;
  }

  return (
    <section className="space-y-6" data-testid="attendance-overview-panel">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Attendance Runtime</h1>
        <p className="text-sm text-muted-foreground">
          Read-only attendance runtime for health, risk, trends, intervention candidates, and readiness visibility.
        </p>
      </header>

      <section className="rounded-lg border p-4" data-testid="attendance-statistics-panel">
        <h2 className="text-lg font-semibold">Attendance statistics</h2>
        <div className="mt-3 grid gap-2 text-sm md:grid-cols-2">
          <p>Tracked students total: {runtime.data.attendance_statistics.tracked_students_total}</p>
          <p>Tracked courses total: {runtime.data.attendance_statistics.tracked_courses_total}</p>
          <p>Average attendance rate: {runtime.data.attendance_statistics.average_attendance_rate}</p>
          <p>At-risk students total: {runtime.data.attendance_statistics.at_risk_students_total}</p>
          <p>Intervention candidates total: {runtime.data.attendance_statistics.intervention_candidates_total}</p>
          <p>Trend windows total: {runtime.data.attendance_statistics.trend_windows_total}</p>
        </div>
      </section>

      <section className="rounded-lg border p-4" data-testid="attendance-distribution-panel">
        <h2 className="text-lg font-semibold">Attendance distribution</h2>
        <div className="mt-2 space-y-1 text-sm">
          <p>Excellent band: {runtime.data.attendance_distribution.excellent_band}</p>
          <p>Good band: {runtime.data.attendance_distribution.good_band}</p>
          <p>Warning band: {runtime.data.attendance_distribution.warning_band}</p>
          <p>Critical band: {runtime.data.attendance_distribution.critical_band}</p>
        </div>
      </section>

      <section className="rounded-lg border p-4" data-testid="attendance-trends-panel">
        <h2 className="text-lg font-semibold">Attendance trends</h2>
        <div className="mt-2 space-y-1 text-sm">
          <p>Improving count: {runtime.data.attendance_trends.improving_count}</p>
          <p>Stable count: {runtime.data.attendance_trends.stable_count}</p>
          <p>Declining count: {runtime.data.attendance_trends.declining_count}</p>
          <p>Trend score: {runtime.data.attendance_trends.trend_score}</p>
        </div>
      </section>

      <section className="rounded-lg border p-4" data-testid="attendance-risk-summary-panel">
        <h2 className="text-lg font-semibold">Attendance risk summary</h2>
        <div className="mt-2 space-y-1 text-sm">
          <p>Risk score: {runtime.data.attendance_risk_summary.risk_score}</p>
          <p>Open risks: {runtime.data.attendance_risk_summary.open_risks}</p>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <RegistrySectionCard
          title="High-risk population"
          section={runtime.data.high_risk_population}
          testId="high-risk-population-panel"
        />
        <RegistrySectionCard
          title="Course attendance health"
          section={runtime.data.course_attendance_health}
          testId="course-attendance-health-panel"
        />
      </section>

      <RegistrySectionCard
        title="Attendance intervention candidates"
        section={runtime.data.attendance_intervention_candidates}
        testId="attendance-intervention-panel"
      />

      <section className="rounded-lg border p-4" data-testid="attendance-signals-panel">
        <h2 className="text-lg font-semibold">Attendance signals</h2>
        <div className="mt-2 space-y-1 text-sm">
          <p>Generated signals: {runtime.data.attendance_signals.generated_signals}</p>
          <p>Signal types: {runtime.data.attendance_signals.signal_types.join(', ') || 'none'}</p>
        </div>
      </section>

      <section className="rounded-lg border p-4" data-testid="attendance-readiness-panel">
        <h2 className="text-lg font-semibold">Attendance readiness</h2>
        <p className="mt-2 text-sm">Ready for runtime: {String(runtime.data.attendance_readiness.ready_for_runtime)}</p>
        <p className="text-sm">Readiness score: {runtime.data.attendance_readiness.readiness_score}</p>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
          {runtime.data.attendance_readiness.checklist.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </section>
  );
}

export function AssessmentRuntimePage() {
  const runtime = useQuery({
    queryKey: ['academic-operations:assessment-runtime'],
    queryFn: academicOperationsRuntimeApi.getAssessmentRuntime,
    staleTime: 30000,
  });

  if (runtime.isPending) {
    return <LoadingState title="Loading Assessment runtime" />;
  }

  if (runtime.error) {
    return <ErrorState message="Failed to load Assessment runtime." error={runtime.error} />;
  }

  if (!runtime.data) {
    return <ErrorState message="Assessment runtime is unavailable." />;
  }

  return (
    <section className="space-y-6" data-testid="assessment-overview-panel">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Assessment Runtime</h1>
        <p className="text-sm text-muted-foreground">
          Read-only assessment runtime for exam visibility, gradebook readiness, risk signals, and operational readiness.
        </p>
      </header>

      <section className="rounded-lg border p-4" data-testid="assessment-statistics-panel">
        <h2 className="text-lg font-semibold">Assessment statistics</h2>
        <div className="mt-3 grid gap-2 text-sm md:grid-cols-2">
          <p>Exams total: {runtime.data.assessment_statistics.exams_total}</p>
          <p>Completed exams total: {runtime.data.assessment_statistics.completed_exams_total}</p>
          <p>Gradebook entries total: {runtime.data.assessment_statistics.gradebook_entries_total}</p>
          <p>Grading distribution total: {runtime.data.assessment_statistics.grading_distribution_total}</p>
          <p>Schedule alignment total: {runtime.data.assessment_statistics.schedule_alignment_total}</p>
          <p>Assessment signals total: {runtime.data.assessment_statistics.assessment_signals_total}</p>
          <p>Canonical bridge total: {runtime.data.assessment_statistics.canonical_bridge_total}</p>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <RegistrySectionCard
          title="Exam governance summary"
          section={runtime.data.exam_governance_summary}
          testId="exam-governance-panel"
        />
        <RegistrySectionCard
          title="Gradebook readiness"
          section={runtime.data.gradebook_readiness}
          testId="gradebook-readiness-panel"
        />
      </section>

      <section className="rounded-lg border p-4" data-testid="grading-distribution-panel">
        <h2 className="text-lg font-semibold">Grading distribution</h2>
        <div className="mt-2 space-y-1 text-sm">
          <p>Excellent band: {runtime.data.grading_distribution.excellent_band}</p>
          <p>Good band: {runtime.data.grading_distribution.good_band}</p>
          <p>Warning band: {runtime.data.grading_distribution.warning_band}</p>
          <p>Critical band: {runtime.data.grading_distribution.critical_band}</p>
        </div>
      </section>

      <RegistrySectionCard
        title="Assessment schedule alignment"
        section={runtime.data.assessment_schedule_alignment}
        testId="assessment-schedule-alignment-panel"
      />

      <section className="rounded-lg border p-4" data-testid="assessment-risk-summary-panel">
        <h2 className="text-lg font-semibold">Assessment risk summary</h2>
        <div className="mt-2 space-y-1 text-sm">
          <p>Risk score: {runtime.data.assessment_risk_summary.risk_score}</p>
          <p>Open risks: {runtime.data.assessment_risk_summary.open_risks}</p>
          <p>Indicators: {runtime.data.assessment_risk_summary.indicators.join(', ') || 'none'}</p>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <RegistrySectionCard
          title="High-risk assessments"
          section={runtime.data.high_risk_assessments}
          testId="high-risk-assessments-panel"
        />
        <section className="rounded-lg border p-4" data-testid="assessment-signals-panel">
          <h2 className="text-lg font-semibold">Assessment signals</h2>
          <div className="mt-2 space-y-1 text-sm">
            <p>Generated signals: {runtime.data.assessment_signals.generated_signals}</p>
            <p>Signal types: {runtime.data.assessment_signals.signal_types.join(', ') || 'none'}</p>
          </div>
        </section>
      </section>

      <section className="rounded-lg border p-4" data-testid="assessment-readiness-panel">
        <h2 className="text-lg font-semibold">Assessment readiness</h2>
        <p className="mt-2 text-sm">Ready for runtime: {String(runtime.data.assessment_readiness.ready_for_runtime)}</p>
        <p className="text-sm">Readiness score: {runtime.data.assessment_readiness.readiness_score}</p>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
          {runtime.data.assessment_readiness.checklist.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </section>
  );
}
