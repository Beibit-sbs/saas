"use client";

import { useMemo, useState } from "react";
import { HeartPulse } from "lucide-react";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { DataTable, type Column } from "@/shared/ui/data-table";
import { ErrorState } from "@/shared/ui/error-state";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import {
  useAccessibilitySupports,
  useCounselingCases,
  useCreateAccessibilitySupport,
  useCreateCounselingCase,
  useCreateDisciplinaryCase,
  useCreateWellbeingCheckin,
  useDisciplinaryCases,
  useStudentLifeHealth,
  useWellbeingCheckins,
} from "@/modules/student_life/hooks";
import type {
  AccessibilitySupport,
  CounselingCase,
  DisciplinaryCase,
  WellbeingCheckin,
} from "@/modules/student_life/types";

interface CounselingFormState {
  case_code: string;
  student_id: string;
  concern_type: string;
}

interface WellbeingFormState {
  student_id: string;
  wellbeing_score: string;
}

interface AccessibilityFormState {
  support_code: string;
  student_id: string;
  support_type: string;
}

interface DisciplinaryFormState {
  incident_code: string;
  student_id: string;
  incident_type: string;
  severity: string;
}

const EMPTY_COUNSELING: CounselingFormState = {
  case_code: "",
  student_id: "",
  concern_type: "",
};

const EMPTY_WELLBEING: WellbeingFormState = {
  student_id: "",
  wellbeing_score: "",
};

const EMPTY_ACCESSIBILITY: AccessibilityFormState = {
  support_code: "",
  student_id: "",
  support_type: "",
};

const EMPTY_DISCIPLINARY: DisciplinaryFormState = {
  incident_code: "",
  student_id: "",
  incident_type: "",
  severity: "",
};

const COUNSELING_STATUS_COLORS: Record<string, string> = {
  open: "bg-blue-100 text-blue-700",
  in_progress: "bg-amber-100 text-amber-700",
  closed: "bg-gray-100 text-gray-700",
};

const WELLBEING_STATUS_COLORS: Record<string, string> = {
  stable: "bg-green-100 text-green-700",
  watch: "bg-amber-100 text-amber-700",
  at_risk: "bg-red-100 text-red-700",
};

const ACCESSIBILITY_STATUS_COLORS: Record<string, string> = {
  requested: "bg-blue-100 text-blue-700",
  active: "bg-emerald-100 text-emerald-700",
  completed: "bg-gray-100 text-gray-700",
  denied: "bg-red-100 text-red-700",
};

const DISCIPLINARY_STATUS_COLORS: Record<string, string> = {
  reported: "bg-blue-100 text-blue-700",
  under_review: "bg-amber-100 text-amber-700",
  resolved: "bg-emerald-100 text-emerald-700",
  appealed: "bg-violet-100 text-violet-700",
};

export default function StudentLifePage() {
  const { getHandlers } = useMutationFeedback();
  const [counselingForm, setCounselingForm] = useState<CounselingFormState>(EMPTY_COUNSELING);
  const [wellbeingForm, setWellbeingForm] = useState<WellbeingFormState>(EMPTY_WELLBEING);
  const [accessibilityForm, setAccessibilityForm] = useState<AccessibilityFormState>(
    EMPTY_ACCESSIBILITY,
  );
  const [disciplinaryForm, setDisciplinaryForm] = useState<DisciplinaryFormState>(
    EMPTY_DISCIPLINARY,
  );

  const { data: healthData } = useStudentLifeHealth();
  const {
    data: counselingData,
    isLoading: counselingLoading,
    error: counselingError,
    refetch: refetchCounseling,
  } = useCounselingCases();
  const {
    data: wellbeingData,
    isLoading: wellbeingLoading,
    error: wellbeingError,
    refetch: refetchWellbeing,
  } = useWellbeingCheckins();
  const {
    data: accessibilityData,
    isLoading: accessibilityLoading,
    error: accessibilityError,
    refetch: refetchAccessibility,
  } = useAccessibilitySupports();
  const {
    data: disciplinaryData,
    isLoading: disciplinaryLoading,
    error: disciplinaryError,
    refetch: refetchDisciplinary,
  } = useDisciplinaryCases();

  const createCounselingCase = useCreateCounselingCase();
  const createWellbeingCheckin = useCreateWellbeingCheckin();
  const createAccessibilitySupport = useCreateAccessibilitySupport();
  const createDisciplinaryCase = useCreateDisciplinaryCase();

  const isSubmitting =
    createCounselingCase.isPending ||
    createWellbeingCheckin.isPending ||
    createAccessibilitySupport.isPending ||
    createDisciplinaryCase.isPending;

  const canCreateCounseling = useMemo(
    () =>
      counselingForm.case_code.trim().length > 0 &&
      counselingForm.student_id.trim().length > 0 &&
      counselingForm.concern_type.trim().length > 0,
    [counselingForm],
  );

  const canCreateWellbeing = useMemo(() => {
    const score = Number(wellbeingForm.wellbeing_score);
    return (
      wellbeingForm.student_id.trim().length > 0 &&
      Number.isInteger(score) &&
      score >= 0 &&
      score <= 100
    );
  }, [wellbeingForm]);

  const canCreateAccessibility = useMemo(
    () =>
      accessibilityForm.support_code.trim().length > 0 &&
      accessibilityForm.student_id.trim().length > 0 &&
      accessibilityForm.support_type.trim().length > 0,
    [accessibilityForm],
  );

  const canCreateDisciplinary = useMemo(
    () =>
      disciplinaryForm.incident_code.trim().length > 0 &&
      disciplinaryForm.student_id.trim().length > 0 &&
      disciplinaryForm.incident_type.trim().length > 0 &&
      disciplinaryForm.severity.trim().length > 0,
    [disciplinaryForm],
  );

  const health = healthData?.item;

  const counselingColumns: Column<CounselingCase>[] = [
    {
      key: "case_code",
      header: "Case Code",
      cell: (row) => <span className="font-mono text-xs">{row.case_code}</span>,
      sortValue: (row) => row.case_code,
    },
    {
      key: "student_id",
      header: "Student ID",
      cell: (row) => row.student_id,
      sortValue: (row) => row.student_id,
    },
    {
      key: "concern_type",
      header: "Concern",
      cell: (row) => row.concern_type,
      sortValue: (row) => row.concern_type.toLowerCase(),
    },
    {
      key: "status",
      header: "Status",
      cell: (row) => (
        <Badge className={COUNSELING_STATUS_COLORS[row.status] ?? ""}>{row.status}</Badge>
      ),
      sortValue: (row) => row.status,
    },
  ];

  const wellbeingColumns: Column<WellbeingCheckin>[] = [
    {
      key: "student_id",
      header: "Student ID",
      cell: (row) => row.student_id,
      sortValue: (row) => row.student_id,
    },
    {
      key: "wellbeing_score",
      header: "Score",
      cell: (row) => <span className="font-medium">{row.wellbeing_score}</span>,
      sortValue: (row) => row.wellbeing_score,
    },
    {
      key: "status",
      header: "Status",
      cell: (row) => (
        <Badge className={WELLBEING_STATUS_COLORS[row.status] ?? ""}>{row.status}</Badge>
      ),
      sortValue: (row) => row.status,
    },
  ];

  const accessibilityColumns: Column<AccessibilitySupport>[] = [
    {
      key: "support_code",
      header: "Support Code",
      cell: (row) => <span className="font-mono text-xs">{row.support_code}</span>,
      sortValue: (row) => row.support_code,
    },
    {
      key: "student_id",
      header: "Student ID",
      cell: (row) => row.student_id,
      sortValue: (row) => row.student_id,
    },
    {
      key: "support_type",
      header: "Support Type",
      cell: (row) => row.support_type,
      sortValue: (row) => row.support_type.toLowerCase(),
    },
    {
      key: "status",
      header: "Status",
      cell: (row) => (
        <Badge className={ACCESSIBILITY_STATUS_COLORS[row.status] ?? ""}>{row.status}</Badge>
      ),
      sortValue: (row) => row.status,
    },
  ];

  const disciplinaryColumns: Column<DisciplinaryCase>[] = [
    {
      key: "incident_code",
      header: "Incident Code",
      cell: (row) => <span className="font-mono text-xs">{row.incident_code}</span>,
      sortValue: (row) => row.incident_code,
    },
    {
      key: "student_id",
      header: "Student ID",
      cell: (row) => row.student_id,
      sortValue: (row) => row.student_id,
    },
    {
      key: "incident_type",
      header: "Incident Type",
      cell: (row) => row.incident_type,
      sortValue: (row) => row.incident_type.toLowerCase(),
    },
    {
      key: "severity",
      header: "Severity",
      cell: (row) => row.severity,
      sortValue: (row) => row.severity.toLowerCase(),
    },
    {
      key: "status",
      header: "Status",
      cell: (row) => (
        <Badge className={DISCIPLINARY_STATUS_COLORS[row.status] ?? ""}>{row.status}</Badge>
      ),
      sortValue: (row) => row.status,
    },
  ];

  if (counselingError && wellbeingError && accessibilityError && disciplinaryError) {
    return (
      <ErrorState
        title="Failed to load student life data"
        onRetry={() => {
          refetchCounseling();
          refetchWellbeing();
          refetchAccessibility();
          refetchDisciplinary();
        }}
      />
    );
  }

  return (
    <RequirePermission permission={PERMISSIONS.STUDENT_LIFE_READ}>
      <div className="space-y-6" data-testid="student-life-page">
        <PageHeader
          title="Student Life"
          description="Manage counseling cases, wellbeing check-ins, accessibility supports, and disciplinary cases."
          icon={HeartPulse}
        />

        {health && (
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <div className="rounded-lg border p-3 text-center">
              <p className="text-2xl font-bold">{health.open_counseling_cases}</p>
              <p className="text-xs text-muted-foreground">Open Counseling</p>
            </div>
            <div className="rounded-lg border p-3 text-center">
              <p className="text-2xl font-bold text-red-600">{health.at_risk_wellbeing_checkins}</p>
              <p className="text-xs text-muted-foreground">At-Risk Wellbeing</p>
            </div>
            <div className="rounded-lg border p-3 text-center">
              <p className="text-2xl font-bold">{health.active_accessibility_supports}</p>
              <p className="text-xs text-muted-foreground">Active Accessibility</p>
            </div>
            <div className="rounded-lg border p-3 text-center">
              <p className="text-2xl font-bold text-amber-600">{health.unresolved_disciplinary_cases}</p>
              <p className="text-xs text-muted-foreground">Unresolved Disciplinary</p>
            </div>
          </div>
        )}

        <RequirePermission permission={PERMISSIONS.STUDENT_LIFE_WRITE}>
          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-3 rounded-lg border p-4">
              <h3 className="font-semibold">New Counseling Case</h3>
              <div className="space-y-1">
                <Label htmlFor="case-code">Case Code</Label>
                <Input
                  id="case-code"
                  value={counselingForm.case_code}
                  onChange={(e) => setCounselingForm((p) => ({ ...p, case_code: e.target.value }))}
                  placeholder="CSL-2026-01"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="c-student-id">Student ID</Label>
                <Input
                  id="c-student-id"
                  value={counselingForm.student_id}
                  onChange={(e) => setCounselingForm((p) => ({ ...p, student_id: e.target.value }))}
                  placeholder="STU-500"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="concern-type">Concern Type</Label>
                <Input
                  id="concern-type"
                  value={counselingForm.concern_type}
                  onChange={(e) => setCounselingForm((p) => ({ ...p, concern_type: e.target.value }))}
                  placeholder="anxiety_support"
                />
              </div>
              <Button
                disabled={!canCreateCounseling || isSubmitting}
                onClick={() =>
                  createCounselingCase.mutate(
                    { ...counselingForm, status: "open" },
                    (() => {
                      const handlers = getHandlers({ successTitle: "Counseling case created" });
                      return {
                        ...handlers,
                        onSuccess: (result: unknown) => {
                          handlers.onSuccess(result);
                          setCounselingForm(EMPTY_COUNSELING);
                        },
                      };
                    })(),
                  )
                }
              >
                Create Case
              </Button>
            </div>

            <div className="space-y-3 rounded-lg border p-4">
              <h3 className="font-semibold">New Wellbeing Check-in</h3>
              <div className="space-y-1">
                <Label htmlFor="wb-student-id">Student ID</Label>
                <Input
                  id="wb-student-id"
                  value={wellbeingForm.student_id}
                  onChange={(e) => setWellbeingForm((p) => ({ ...p, student_id: e.target.value }))}
                  placeholder="STU-500"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="wb-score">Wellbeing Score (0-100)</Label>
                <Input
                  id="wb-score"
                  type="number"
                  min={0}
                  max={100}
                  value={wellbeingForm.wellbeing_score}
                  onChange={(e) => setWellbeingForm((p) => ({ ...p, wellbeing_score: e.target.value }))}
                  placeholder="75"
                />
              </div>
              <Button
                disabled={!canCreateWellbeing || isSubmitting}
                onClick={() =>
                  createWellbeingCheckin.mutate(
                    {
                      student_id: wellbeingForm.student_id,
                      wellbeing_score: Number(wellbeingForm.wellbeing_score),
                    },
                    (() => {
                      const handlers = getHandlers({ successTitle: "Wellbeing check-in recorded" });
                      return {
                        ...handlers,
                        onSuccess: (result: unknown) => {
                          handlers.onSuccess(result);
                          setWellbeingForm(EMPTY_WELLBEING);
                        },
                      };
                    })(),
                  )
                }
              >
                Record Check-in
              </Button>
            </div>

            <div className="space-y-3 rounded-lg border p-4">
              <h3 className="font-semibold">New Accessibility Support</h3>
              <div className="space-y-1">
                <Label htmlFor="support-code">Support Code</Label>
                <Input
                  id="support-code"
                  value={accessibilityForm.support_code}
                  onChange={(e) => setAccessibilityForm((p) => ({ ...p, support_code: e.target.value }))}
                  placeholder="ACC-2026-01"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="a-student-id">Student ID</Label>
                <Input
                  id="a-student-id"
                  value={accessibilityForm.student_id}
                  onChange={(e) => setAccessibilityForm((p) => ({ ...p, student_id: e.target.value }))}
                  placeholder="STU-500"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="support-type">Support Type</Label>
                <Input
                  id="support-type"
                  value={accessibilityForm.support_type}
                  onChange={(e) => setAccessibilityForm((p) => ({ ...p, support_type: e.target.value }))}
                  placeholder="screen_reader"
                />
              </div>
              <Button
                disabled={!canCreateAccessibility || isSubmitting}
                onClick={() =>
                  createAccessibilitySupport.mutate(
                    { ...accessibilityForm, status: "requested" },
                    (() => {
                      const handlers = getHandlers({ successTitle: "Accessibility support created" });
                      return {
                        ...handlers,
                        onSuccess: (result: unknown) => {
                          handlers.onSuccess(result);
                          setAccessibilityForm(EMPTY_ACCESSIBILITY);
                        },
                      };
                    })(),
                  )
                }
              >
                Create Support
              </Button>
            </div>

            <div className="space-y-3 rounded-lg border p-4">
              <h3 className="font-semibold">New Disciplinary Case</h3>
              <div className="space-y-1">
                <Label htmlFor="incident-code">Incident Code</Label>
                <Input
                  id="incident-code"
                  value={disciplinaryForm.incident_code}
                  onChange={(e) => setDisciplinaryForm((p) => ({ ...p, incident_code: e.target.value }))}
                  placeholder="DISC-2026-01"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="d-student-id">Student ID</Label>
                <Input
                  id="d-student-id"
                  value={disciplinaryForm.student_id}
                  onChange={(e) => setDisciplinaryForm((p) => ({ ...p, student_id: e.target.value }))}
                  placeholder="STU-500"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="incident-type">Incident Type</Label>
                <Input
                  id="incident-type"
                  value={disciplinaryForm.incident_type}
                  onChange={(e) => setDisciplinaryForm((p) => ({ ...p, incident_type: e.target.value }))}
                  placeholder="conduct_violation"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="severity">Severity</Label>
                <Input
                  id="severity"
                  value={disciplinaryForm.severity}
                  onChange={(e) => setDisciplinaryForm((p) => ({ ...p, severity: e.target.value }))}
                  placeholder="medium"
                />
              </div>
              <Button
                disabled={!canCreateDisciplinary || isSubmitting}
                onClick={() =>
                  createDisciplinaryCase.mutate(
                    { ...disciplinaryForm, status: "reported" },
                    (() => {
                      const handlers = getHandlers({ successTitle: "Disciplinary case created" });
                      return {
                        ...handlers,
                        onSuccess: (result: unknown) => {
                          handlers.onSuccess(result);
                          setDisciplinaryForm(EMPTY_DISCIPLINARY);
                        },
                      };
                    })(),
                  )
                }
              >
                Create Disciplinary Case
              </Button>
            </div>
          </div>
        </RequirePermission>

        <div className="space-y-4">
          <h3 className="font-semibold">Counseling Cases</h3>
          <DataTable
            columns={counselingColumns}
            data={counselingData?.items ?? []}
            isLoading={counselingLoading}
            getRowKey={(row) => String(row.id)}
            emptyDescription="No counseling cases found."
          />
        </div>

        <div className="space-y-4">
          <h3 className="font-semibold">Wellbeing Check-ins</h3>
          <DataTable
            columns={wellbeingColumns}
            data={wellbeingData?.items ?? []}
            isLoading={wellbeingLoading}
            getRowKey={(row) => String(row.id)}
            emptyDescription="No wellbeing check-ins found."
          />
        </div>

        <div className="space-y-4">
          <h3 className="font-semibold">Accessibility Supports</h3>
          <DataTable
            columns={accessibilityColumns}
            data={accessibilityData?.items ?? []}
            isLoading={accessibilityLoading}
            getRowKey={(row) => String(row.id)}
            emptyDescription="No accessibility supports found."
          />
        </div>

        <div className="space-y-4">
          <h3 className="font-semibold">Disciplinary Cases</h3>
          <DataTable
            columns={disciplinaryColumns}
            data={disciplinaryData?.items ?? []}
            isLoading={disciplinaryLoading}
            getRowKey={(row) => String(row.id)}
            emptyDescription="No disciplinary cases found."
          />
        </div>
      </div>
    </RequirePermission>
  );
}
