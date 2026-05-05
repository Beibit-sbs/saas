"use client";

import { useMemo, useState } from "react";
import { ClipboardList, Search } from "lucide-react";
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
  useDegreeProgress,
  useDegreeProgressConsistency,
  useGraduationEligibility,
} from "@/modules/degree-progress/hooks";
import type { RequirementStatus } from "@/modules/degree-progress/types";

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

  const canRead = hasPermission(PERMISSIONS.DEGREE_PROGRESS_READ);
  const activeStudentId = useMemo(() => requestedStudentId.trim(), [requestedStudentId]);

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
          <CardDescription>Enter student profile ID and load progress details.</CardDescription>
        </CardHeader>
        <CardContent className="flex gap-2">
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
          <Button onClick={() => setRequestedStudentId(studentIdInput)}>
            <Search className="h-4 w-4 mr-1" />
            Load
          </Button>
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
                  {progress.gpa ?? "-"} / {progress.minimum_gpa}
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
                  Remaining required items: {eligibility.remaining_required_items}
                </span>
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
