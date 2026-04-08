"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/shared/ui/page-header";
import { DataTable, Column } from "@/shared/ui/data-table";
import { FilterBar } from "@/shared/ui/filter-bar";
import { ErrorState } from "@/shared/ui/error-state";
import { Button } from "@/shared/ui/button";
import { DrawerPanel } from "@/shared/ui/drawer-panel";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { PermissionGate, RequirePermission } from "@/shared/ui/permission-gate";
import { useDetailDrawer } from "@/shared/hooks/use-detail-drawer";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useTableQueryState } from "@/shared/hooks/use-table-query-state";
import { useGrades, useUpsertGrade } from "@/modules/grades/hooks";
import { Grade } from "@/modules/grades/types";
import { formatDate } from "@/shared/utils/format";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useLanguage } from "@/app/components/LanguageProvider";
import { BarChart2 } from "lucide-react";

const FILTER_FIELDS = [
  { key: "student_id", label: "Student ID", type: "text" as const, placeholder: "Student ID…" },
  { key: "section_id", label: "Section ID", type: "text" as const, placeholder: "Section ID…" },
];

export default function GradesPage() {
  const { t } = useLanguage();
  const table = useTableQueryState({ filterKeys: ["student_id", "section_id"] as const, defaultPageSize: 20, defaultSort: { key: "graded", direction: "desc" } });
  const detail = useDetailDrawer({ paramKey: "grade" });
  const { getHandlers } = useMutationFeedback();
  const [createOpen, setCreateOpen] = useState(false);
  const [newEnrollmentId, setNewEnrollmentId] = useState("");
  const [newGradeValue, setNewGradeValue] = useState("");
  const [newNumericValue, setNewNumericValue] = useState("");
  const [gradeValue, setGradeValue] = useState("");
  const [numericValue, setNumericValue] = useState("");

  const { data, isLoading, error, refetch } = useGrades({
    page: table.page,
    page_size: table.pageSize,
    student_id: table.filters.student_id,
    section_id: table.filters.section_id,
  });
  const upsertGrade = useUpsertGrade();
  const selectedGrade = data?.items.find((item) => item.id === detail.selectedId) ?? null;
  const canCreateGrade = newEnrollmentId.trim().length > 0 && newGradeValue.trim().length > 0;

  useEffect(() => {
    setGradeValue(selectedGrade?.grade_value ?? "");
    setNumericValue(selectedGrade?.numeric_value?.toString() ?? "");
  }, [selectedGrade]);

  if (error) {
    return <ErrorState title="Failed to load grades" onRetry={refetch} />;
  }

  const columns: Column<Grade>[] = [
    { key: "student", header: "Student", cell: (r) => r.student_name, sortValue: (r) => r.student_name.toLowerCase() },
    { key: "section", header: "Section", cell: (r) => <code className="text-xs">{r.section_code}</code>, sortValue: (r) => r.section_code },
    { key: "course", header: "Course", cell: (r) => r.course_name, sortValue: (r) => r.course_name.toLowerCase() },
    { key: "grade", header: "Grade", cell: (r) => <span className="font-semibold">{r.grade_value ?? "—"}</span>, sortValue: (r) => r.grade_value ?? "" },
    { key: "numeric", header: "Score", cell: (r) => r.numeric_value?.toFixed(1) ?? "—", sortValue: (r) => r.numeric_value ?? -1 },
    { key: "graded", header: "Graded", cell: (r) => (r.graded_at ? formatDate(r.graded_at) : "—"), sortValue: (r) => r.graded_at ?? "" },
    {
      key: "actions",
      header: "",
      width: "90px",
      cell: (r) => (
        <PermissionGate permission={PERMISSIONS.GRADES_WRITE}>
          <Button
            variant="ghost"
            size="sm"
            onClick={(event) => {
              event.stopPropagation();
              detail.open(r.id);
            }}
          >
            Edit
          </Button>
        </PermissionGate>
      ),
    },
  ];

  return (
    <RequirePermission permission={PERMISSIONS.GRADES_READ}>
    <div className="space-y-4">
      <PageHeader
        title={t("nav.grades")}
        description={t("console.grades.description")}
        icon={BarChart2}
        actions={
          <PermissionGate permission={PERMISSIONS.GRADES_WRITE}>
            <Button size="sm" onClick={() => setCreateOpen(true)}>
              Add grade
            </Button>
          </PermissionGate>
        }
      />

      <FilterBar
        fields={FILTER_FIELDS}
        values={table.filters}
        onChange={table.setFilter}
        onReset={table.resetFilters}
      />

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        isLoading={isLoading}
        getRowKey={(r) => r.id}
        pagination={{ page: table.page, pageSize: table.pageSize, total: data?.total ?? 0 }}
        pageSizeOptions={[10, 20, 50]}
        onPageChange={table.setPage}
        onPageSizeChange={table.setPageSize}
        sort={table.sort}
        onSortChange={table.setSort}
        onRowClick={(row) => detail.open(row.id)}
        emptyTitle="No grades found"
      />

      <DrawerPanel
        open={detail.isOpen}
        onClose={detail.close}
        title={selectedGrade ? `Update ${selectedGrade.student_name}` : "Update grade"}
        description={selectedGrade?.course_name ?? "Select a grade row to update."}
      >
        {selectedGrade ? (
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="grade-value">Letter grade</Label>
              <Input id="grade-value" value={gradeValue} onChange={(event) => setGradeValue(event.target.value)} placeholder="A" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="numeric-value">Numeric score</Label>
              <Input id="numeric-value" value={numericValue} onChange={(event) => setNumericValue(event.target.value)} placeholder="4.0" />
            </div>
            <PermissionGate permission={PERMISSIONS.GRADES_WRITE}>
              <Button
                disabled={!gradeValue.trim() || upsertGrade.isPending}
                onClick={() =>
                  upsertGrade.mutate(
                    {
                      enrollment_id: selectedGrade.enrollment_id,
                      grade_value: gradeValue.trim(),
                      numeric_value: numericValue.trim() ? Number(numericValue) : undefined,
                    },
                    {
                      ...getHandlers({ successTitle: "Grade updated" }),
                      onSuccess: () => {
                        getHandlers<Grade>({ successTitle: "Grade updated" }).onSuccess(selectedGrade);
                        detail.close();
                      },
                    },
                  )
                }
              >
                Save grade
              </Button>
            </PermissionGate>
          </div>
        ) : (
          <ErrorState title="Grade not found" message="The selected grade is not present on this page of results." />
        )}
      </DrawerPanel>

      <DrawerPanel
        open={createOpen}
        onClose={() => {
          setCreateOpen(false);
          setNewEnrollmentId("");
          setNewGradeValue("");
          setNewNumericValue("");
        }}
        title="Add grade"
        description="Create or update grade by enrollment ID."
      >
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="new-grade-enrollment-id">Enrollment ID</Label>
            <Input
              id="new-grade-enrollment-id"
              value={newEnrollmentId}
              onChange={(event) => setNewEnrollmentId(event.target.value)}
              placeholder="e1"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="new-grade-value">Letter grade</Label>
            <Input
              id="new-grade-value"
              value={newGradeValue}
              onChange={(event) => setNewGradeValue(event.target.value)}
              placeholder="A"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="new-numeric-value">Numeric score</Label>
            <Input
              id="new-numeric-value"
              value={newNumericValue}
              onChange={(event) => setNewNumericValue(event.target.value)}
              placeholder="4.0"
            />
          </div>
          <PermissionGate permission={PERMISSIONS.GRADES_WRITE}>
            <Button
              disabled={!canCreateGrade || upsertGrade.isPending}
              onClick={() =>
                upsertGrade.mutate(
                  {
                    enrollment_id: newEnrollmentId.trim(),
                    grade_value: newGradeValue.trim(),
                    numeric_value: newNumericValue.trim() ? Number(newNumericValue) : undefined,
                  },
                  {
                    ...getHandlers({ successTitle: "Grade saved" }),
                    onSuccess: () => {
                      setCreateOpen(false);
                      setNewEnrollmentId("");
                      setNewGradeValue("");
                      setNewNumericValue("");
                    },
                  },
                )
              }
            >
              Save grade
            </Button>
          </PermissionGate>
        </div>
      </DrawerPanel>
    </div>
    </RequirePermission>
  );
}
