"use client";

import { useMemo, useState } from "react";
import { ClipboardList, Search, UserCheck } from "lucide-react";
import { Wave1KpiBar } from "@/modules/platform/kpi/wave1-kpi-bar";

const DEGREE_KPI_KEYS = [
  "graduation_risk_students_count",
  "degree_progress_intervention_cases_count",
] as const;

const DEGREE_KPI_LABELS: Record<string, string> = {
  graduation_risk_students_count: "Graduation Risk Students",
  degree_progress_intervention_cases_count: "Degree Progress Cases",
};
import { PageHeader } from "@/shared/ui/page-header";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { ErrorState } from "@/shared/ui/error-state";
import { Badge } from "@/shared/ui/badge";
import { AccessDenied } from "@/shared/ui/permission-gate";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { PERMISSIONS } from "@/shared/config/permissions";
import {
  useCreateProgramRequirement,
  useDegreeProgress,
  useDegreeProgressConsistency,
  useGraduationEligibility,
  useProgramRequirements,
} from "@/modules/degree-progress/hooks";
import type { RequirementStatus } from "@/modules/degree-progress/types";
import {
  useStudents,
  useStudent,
  useActiveStudentProgram,
  useBindStudentProgram,
  useChangeStudentStatus,
} from "@/modules/students/hooks";
import { usePrograms } from "@/modules/programs/hooks";
import { useCourses } from "@/modules/courses/hooks";
import {
  useCreateDegreeProgressSnapshot,
  useReviewGraduationReadiness,
} from "@/modules/student-lifecycle/hooks";
import { DegreeProgressStatus } from "@/modules/student-lifecycle/types";

function formatNumber(value: number | string | null | undefined, decimals = 2): string {
  if (value === null || value === undefined || value === "") return "-";
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed.toFixed(decimals) : "-";
}

function RequirementTable({
  title,
  items,
  emptyMessage,
}: {
  title: string;
  items: RequirementStatus[];
  emptyMessage: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">{emptyMessage}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left">
                  <th className="py-2 pr-2 font-medium">Requirement item</th>
                  <th className="py-2 pr-2 font-medium">Course</th>
                  <th className="py-2 pr-2 font-medium">Credits</th>
                  <th className="py-2 pr-2 font-medium">Required</th>
                  <th className="py-2 pr-2 font-medium">Completed</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.requirement_item_id} className="border-b last:border-0">
                    <td className="py-2 pr-2">#{item.requirement_item_id}</td>
                    <td className="py-2 pr-2">{item.course_name ?? `#${item.course_id}`}</td>
                    <td className="py-2 pr-2">{item.credits}</td>
                    <td className="py-2 pr-2">{item.required ? "Yes" : "No"}</td>
                    <td className="py-2 pr-2">{item.completed ? "Yes" : "No"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function DegreeProgressPage() {
  const { hasPermission } = usePermissions();
  const [studentIdInput, setStudentIdInput] = useState("");
  const [requestedStudentId, setRequestedStudentId] = useState("");
  const [selectedProgramId, setSelectedProgramId] = useState("");
  const [requirementName, setRequirementName] = useState("Default graduation requirement");
  const [minimumCredits, setMinimumCredits] = useState("0");
  const [minimumGpa, setMinimumGpa] = useState("0");
  const [selectedCourseIds, setSelectedCourseIds] = useState<string[]>([]);

  const canRead = hasPermission(PERMISSIONS.DEGREE_PROGRESS_READ);
  const canWrite = hasPermission(PERMISSIONS.DEGREE_PROGRESS_WRITE);
  const canChangeStudentProfile = hasPermission(PERMISSIONS.STUDENTS_WRITE);
  const canComputeLifecycleDegreeProgress = hasPermission(PERMISSIONS.STUDENT_LIFECYCLE_DEGREE_PROGRESS_COMPUTE);
  const canReviewLifecycleGraduation = hasPermission(PERMISSIONS.STUDENT_LIFECYCLE_GRADUATION_READINESS_REVIEW);
  const activeStudentId = useMemo(() => requestedStudentId.trim(), [requestedStudentId]);

  const studentsQuery = useStudents({ page: 1, page_size: 200, status: "active" });
  const selectedStudentQuery = useStudent(activeStudentId);
  const programsQuery = usePrograms();
  const coursesQuery = useCourses();
  const activeProgramQuery = useActiveStudentProgram(activeStudentId);
  const bindProgram = useBindStudentProgram(activeStudentId);
  const changeStudentStatus = useChangeStudentStatus();
  const createRequirement = useCreateProgramRequirement();
  const createReviewSnapshot = useCreateDegreeProgressSnapshot();
  const reviewGraduationReadiness = useReviewGraduationReadiness();
  const requirementsQuery = useProgramRequirements({
    program_id: selectedProgramId || activeProgramQuery.data?.program_id?.toString(),
    active_only: true,
  });
  const {
    data: progress,
    isLoading: isProgressLoading,
    error: progressError,
    refetch: refetchProgress,
  } = useDegreeProgress(activeStudentId);
  const {
    data: eligibility,
    isLoading: isEligibilityLoading,
    error: eligibilityError,
    refetch: refetchEligibility,
  } = useGraduationEligibility(activeStudentId);
  const {
    data: consistency,
    isLoading: isConsistencyLoading,
    error: consistencyError,
    refetch: refetchConsistency,
  } = useDegreeProgressConsistency(canRead);

  if (!canRead) return <AccessDenied />;

  const isLoading = isProgressLoading || isEligibilityLoading;
  const hasLookupError = !!progressError || !!eligibilityError;
  const students = studentsQuery.data?.items ?? [];
  const selectedStudent = selectedStudentQuery.data;
  const selectedStudentStatus = selectedStudent?.current_status ?? selectedStudent?.status;
  const programs = programsQuery.data?.programs ?? [];
  const courses = coursesQuery.data?.courses ?? [];
  const activeProgramId = selectedProgramId || activeProgramQuery.data?.program_id?.toString() || "";
  const requirementCourses = courses.filter((course) => String(course.program_id) === activeProgramId);
  const activeRequirements = requirementsQuery.data?.items ?? [];
  const selectedRequirementCourses = selectedCourseIds.flatMap((courseId) => {
    const course = courses.find((item) => String(item.id) === courseId);
    return course ? [course] : [];
  });
  const canBindProgram = canWrite && !!activeStudentId && !!selectedProgramId && !bindProgram.isPending;
  const canCreateRequirement =
    canWrite &&
    !!activeProgramId &&
    requirementName.trim().length > 0 &&
    Number.isFinite(Number(minimumCredits)) &&
    Number(minimumCredits) >= 0 &&
    Number.isFinite(Number(minimumGpa)) &&
    Number(minimumGpa) >= 0 &&
    selectedRequirementCourses.length > 0 &&
    !createRequirement.isPending;
  const canCreateReviewSnapshot =
    canComputeLifecycleDegreeProgress &&
    !!activeStudentId &&
    !!progress &&
    !!eligibility &&
    !createReviewSnapshot.isPending;
  const canRecordGraduationReview =
    canReviewLifecycleGraduation &&
    !!activeStudentId &&
    !!eligibility &&
    !reviewGraduationReadiness.isPending;
  const canMarkGraduated =
    canChangeStudentProfile &&
    !!activeStudentId &&
    !!eligibility?.eligible &&
    selectedStudentStatus !== "graduated" &&
    typeof selectedStudent?.version === "number" &&
    !changeStudentStatus.isPending;

  return (
    <div className="space-y-6 max-w-6xl">
      <PageHeader
        title="Degree Progress"
        description="Check student graduation readiness, requirement completion, and tenant-level consistency."
        icon={ClipboardList}
      />

      <Wave1KpiBar metricKeys={[...DEGREE_KPI_KEYS]} labels={DEGREE_KPI_LABELS} />

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Student lookup</CardTitle>
          <CardDescription>Select a student profile and load progress details.</CardDescription>
        </CardHeader>
        <CardContent className="flex gap-2">
          {students.length > 0 ? (
            <select
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={studentIdInput}
              onChange={(event) => setStudentIdInput(event.target.value)}
              data-testid="degree-progress-student-select"
            >
              <option value="">Select student</option>
              {students.map((student) => (
                <option key={student.id} value={student.id}>
                  {student.student_number} / {student.first_name} {student.last_name} (#{student.id})
                </option>
              ))}
            </select>
          ) : (
            <Input
              placeholder="Student profile ID"
              value={studentIdInput}
              onChange={(e) => setStudentIdInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  setRequestedStudentId(studentIdInput);
                }
              }}
            />
          )}
          <Button onClick={() => setRequestedStudentId(studentIdInput)}>
            <Search className="h-4 w-4 mr-1" />
            Load
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Program and requirements setup</CardTitle>
          <CardDescription>Bind the student to a program and define the course requirements used by degree progress.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 lg:grid-cols-[1fr_auto]">
            <select
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={selectedProgramId}
              onChange={(event) => {
                setSelectedProgramId(event.target.value);
                setSelectedCourseIds([]);
              }}
              data-testid="degree-progress-program-select"
            >
              <option value="">Select program</option>
              {programs.map((program) => (
                <option key={program.id} value={program.id}>
                  {program.program_code} / {program.title} (#{program.id})
                </option>
              ))}
            </select>
            <Button
              variant="outline"
              disabled={!canBindProgram}
              onClick={() =>
                bindProgram.mutate({
                  program_id: Number(selectedProgramId),
                  is_primary: true,
                  binding_state: "active",
                  metadata_json: { source: "degree_progress_console" },
                })
              }
            >
              Bind program
            </Button>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <Input value={requirementName} onChange={(event) => setRequirementName(event.target.value)} placeholder="Requirement name" />
            <Input value={minimumCredits} onChange={(event) => setMinimumCredits(event.target.value)} placeholder="Minimum credits" />
            <Input value={minimumGpa} onChange={(event) => setMinimumGpa(event.target.value)} placeholder="Minimum GPA" />
          </div>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {requirementCourses.map((course) => (
              <label key={course.id} className="flex items-center gap-2 rounded-md border px-3 py-2 text-sm">
                <input
                  type="checkbox"
                  checked={selectedCourseIds.includes(String(course.id))}
                  onChange={(event) =>
                    setSelectedCourseIds((current) =>
                      event.target.checked
                        ? [...current, String(course.id)]
                        : current.filter((courseId) => courseId !== String(course.id)),
                    )
                  }
                />
                <span>{course.course_code} / {course.title} / {course.credits} credits</span>
              </label>
            ))}
          </div>
          <Button
            disabled={!canCreateRequirement}
            onClick={() =>
              createRequirement.mutate({
                program_id: Number(activeProgramId),
                name: requirementName.trim(),
                minimum_credits: Number(minimumCredits),
                minimum_gpa: Number(minimumGpa),
                is_active: true,
                items: selectedRequirementCourses.map((course) => ({
                  course_id: Number(course?.id),
                  credits: Number(course?.credits ?? 0),
                  required: true,
                })),
              })
            }
          >
            Save requirement
          </Button>
          <div className="text-xs text-muted-foreground">
            Active requirements for selected program: {activeRequirements.length}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Tenant consistency</CardTitle>
          <CardDescription>Quick snapshot of degree-progress data quality checks.</CardDescription>
        </CardHeader>
        <CardContent>
          {consistencyError ? (
            <ErrorState title="Failed to load consistency report" onRetry={refetchConsistency} />
          ) : isConsistencyLoading || !consistency ? (
            <p className="text-sm text-muted-foreground">Loading consistency report...</p>
          ) : (
            <div className="grid gap-3 sm:grid-cols-4 text-sm">
              <div className="rounded-lg border bg-card p-3">
                <p className="text-xs text-muted-foreground">Primary bindings</p>
                <p className="text-lg font-semibold">{consistency.active_primary_binding_count}</p>
              </div>
              <div className="rounded-lg border bg-card p-3">
                <p className="text-xs text-muted-foreground">Active requirements</p>
                <p className="text-lg font-semibold">{consistency.active_requirement_count}</p>
              </div>
              <div className="rounded-lg border bg-card p-3">
                <p className="text-xs text-muted-foreground">Requirement items</p>
                <p className="text-lg font-semibold">{consistency.requirement_item_count}</p>
              </div>
              <div className="rounded-lg border bg-card p-3">
                <p className="text-xs text-muted-foreground">Issues</p>
                <p className="text-lg font-semibold">{consistency.issue_count}</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {activeStudentId ? (
        hasLookupError ? (
          <ErrorState
            title="Failed to load degree progress"
            onRetry={() => {
              void refetchProgress();
              void refetchEligibility();
            }}
          />
        ) : isLoading || !progress || !eligibility ? (
          <Card>
            <CardContent className="py-6">
              <p className="text-sm text-muted-foreground">Loading student degree progress...</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-4 text-sm">
              <div className="rounded-lg border bg-card p-3">
                <p className="text-xs text-muted-foreground">Student profile</p>
                <p className="text-lg font-semibold">#{progress.student_profile_id}</p>
              </div>
              <div className="rounded-lg border bg-card p-3">
                <p className="text-xs text-muted-foreground">Program</p>
                <p className="text-lg font-semibold">{progress.program_name ?? `#${progress.program_id}`}</p>
              </div>
              <div className="rounded-lg border bg-card p-3">
                <p className="text-xs text-muted-foreground">Credits</p>
                <p className="text-lg font-semibold">
                  {progress.credits_earned} / {progress.minimum_credits}
                </p>
              </div>
              <div className="rounded-lg border bg-card p-3">
                <p className="text-xs text-muted-foreground">GPA</p>
                <p className="text-lg font-semibold">
                  {formatNumber(progress.gpa)} / {formatNumber(progress.minimum_gpa)}
                </p>
              </div>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Graduation status</CardTitle>
                <CardDescription>
                  Requirement set: {progress.requirement_name} (#{progress.requirement_id})
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-wrap items-center gap-3">
                <Badge variant={eligibility.eligible ? "default" : "secondary"}>
                  {eligibility.eligible ? "Eligible" : "Not eligible"}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  GPA {formatNumber(eligibility.gpa)} / {formatNumber(eligibility.minimum_gpa)} · Remaining required items: {eligibility.remaining_required_items}
                </span>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Graduation readiness review</CardTitle>
                <CardDescription>
                  Metadata-only human review. This does not graduate the student automatically.
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-2">
                <Button
                  variant="outline"
                  disabled={!canCreateReviewSnapshot}
                  onClick={() =>
                    createReviewSnapshot.mutate({
                      studentId: activeStudentId,
                      payload: {
                        student_id: Number(activeStudentId),
                        incomplete_data: false,
                        completion_summary: {
                          source: "official_degree_progress",
                          graduation_eligible: eligibility.eligible,
                          credits_earned: eligibility.credits_earned,
                          minimum_credits: eligibility.minimum_credits,
                          gpa: eligibility.gpa,
                          minimum_gpa: eligibility.minimum_gpa,
                          remaining_required_items: eligibility.remaining_required_items,
                        },
                      },
                    })
                  }
                >
                  Create review snapshot
                </Button>
                <Button
                  disabled={!canRecordGraduationReview}
                  onClick={() =>
                    reviewGraduationReadiness.mutate({
                      studentId: activeStudentId,
                      payload: {
                        new_status: eligibility.eligible
                          ? DegreeProgressStatus.GRADUATION_READY_METADATA
                          : DegreeProgressStatus.NOT_READY_METADATA,
                        note: eligibility.eligible
                          ? "Official degree progress indicates graduation-ready metadata; human approval still required."
                          : "Official degree progress indicates not-ready metadata; human follow-up required.",
                      },
                    })
                  }
                >
                  Record review metadata
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <UserCheck className="h-4 w-4" />
                  Student status transition
                </CardTitle>
                <CardDescription>
                  Graduation is written to the student profile only after the eligibility guard passes.
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-wrap items-center gap-3">
                <Badge variant={selectedStudentStatus === "graduated" ? "default" : "secondary"}>
                  {selectedStudentStatus ?? "unknown"}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  Version {selectedStudent?.version ?? "-"}
                </span>
                <Button
                  disabled={!canMarkGraduated}
                  onClick={() =>
                    changeStudentStatus.mutate({
                      id: activeStudentId,
                      payload: {
                        expected_version: selectedStudent?.version ?? 0,
                        to_status: "graduated",
                        reason: "Graduation readiness review completed.",
                        metadata_json: {
                          source: "degree_progress_console",
                          graduation_eligible: eligibility.eligible,
                          requirement_id: progress.requirement_id,
                          credits_earned: eligibility.credits_earned,
                          minimum_credits: eligibility.minimum_credits,
                        },
                      },
                    })
                  }
                >
                  Mark graduated
                </Button>
              </CardContent>
            </Card>

            <div className="grid gap-4 lg:grid-cols-2">
              <RequirementTable
                title="Completed requirements"
                items={progress.completed_requirements}
                emptyMessage="No completed requirement items yet."
              />
              <RequirementTable
                title="Remaining requirements"
                items={progress.remaining_requirements}
                emptyMessage="No remaining requirement items."
              />
            </div>
          </div>
        )
      ) : null}
    </div>
  );
}
