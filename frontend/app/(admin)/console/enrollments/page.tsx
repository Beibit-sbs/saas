"use client";

import { useState } from "react";
import { PageHeader } from "@/shared/ui/page-header";
import { DataTable, Column } from "@/shared/ui/data-table";
import { FilterBar } from "@/shared/ui/filter-bar";
import { StatusBadge } from "@/shared/ui/status-badge";
import { useEnrollments, useDropEnrollment, useCreateEnrollment } from "@/modules/enrollments/hooks";
import { Enrollment } from "@/modules/enrollments/types";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { ConfirmActionDialog } from "@/shared/ui/confirm-action-dialog";
import { DrawerPanel } from "@/shared/ui/drawer-panel";
import { DetailList } from "@/shared/ui/detail-list";
import { ErrorState } from "@/shared/ui/error-state";
import { PermissionGate } from "@/shared/ui/permission-gate";
import { useDetailDrawer } from "@/shared/hooks/use-detail-drawer";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useTableQueryState } from "@/shared/hooks/use-table-query-state";
import { formatDate } from "@/shared/utils/format";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useLanguage } from "@/app/components/LanguageProvider";
import { BookOpen, Plus } from "lucide-react";

const FILTER_FIELDS = [
  {
    key: "status",
    label: "Status",
    type: "select" as const,
    options: [
      { label: "Enrolled", value: "enrolled" },
      { label: "Dropped", value: "dropped" },
      { label: "Completed", value: "completed" },
      { label: "Waitlisted", value: "waitlisted" },
    ],
  },
];

export default function EnrollmentsPage() {
  const { t } = useLanguage();
  const [createOpen, setCreateOpen] = useState(false);
  const [studentId, setStudentId] = useState("");
  const [sectionId, setSectionId] = useState("");
  const table = useTableQueryState({ filterKeys: ["status"] as const, defaultPageSize: 20, defaultSort: { key: "enrolled", direction: "desc" } });
  const detail = useDetailDrawer({ paramKey: "enrollment" });
  const { getHandlers } = useMutationFeedback();

  const { data, isLoading, error, refetch } = useEnrollments({ page: table.page, page_size: table.pageSize, status: table.filters.status });
  const createEnrollment = useCreateEnrollment();
  const drop = useDropEnrollment();
  const selectedEnrollment = data?.items.find((item) => item.id === detail.selectedId) ?? null;
  const canCreate = studentId.trim().length > 0 && sectionId.trim().length > 0;

  if (error) {
    return <ErrorState title="Failed to load enrollments" onRetry={refetch} />;
  }

  const columns: Column<Enrollment>[] = [
    { key: "student", header: "Student", cell: (r) => r.student_name, sortValue: (r) => r.student_name.toLowerCase() },
    { key: "section", header: "Section", cell: (r) => <code className="text-xs">{r.section_code}</code>, sortValue: (r) => r.section_code },
    { key: "course", header: "Course", cell: (r) => r.course_name, sortValue: (r) => r.course_name.toLowerCase() },
    { key: "status", header: "Status", cell: (r) => <StatusBadge status={r.status} />, sortValue: (r) => r.status },
    { key: "enrolled", header: "Enrolled", cell: (r) => formatDate(r.enrolled_at), sortValue: (r) => r.enrolled_at },
    {
      key: "actions",
      header: "",
      width: "80px",
      cell: (r) =>
        r.status === "enrolled" ? (
          <PermissionGate permission={PERMISSIONS.ENROLLMENTS_WRITE}>
            <ConfirmActionDialog
              title="Drop enrollment?"
              description={`${r.student_name} will be dropped from ${r.section_code}.`}
              variant="destructive"
              onConfirm={() =>
                drop.mutate(r.id, {
                  ...getHandlers({ successTitle: "Enrollment dropped" }),
                })
              }
              trigger={
                <Button variant="ghost" size="sm" disabled={drop.isPending}>
                  Drop
                </Button>
              }
            />
          </PermissionGate>
        ) : null,
    },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title={t("nav.enrollments")}
        description={t("console.enrollments.description")}
        icon={BookOpen}
        actions={
          <PermissionGate permission={PERMISSIONS.ENROLLMENTS_WRITE}>
            <Button size="sm" onClick={() => setCreateOpen(true)}>
              <Plus className="h-4 w-4 mr-1" />
              Enroll student
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
        emptyTitle="No enrollments found"
      />

      <DrawerPanel
        open={detail.isOpen}
        onClose={detail.close}
        title={selectedEnrollment?.student_name ?? "Enrollment summary"}
        description={selectedEnrollment?.section_code ?? "Select an enrollment from the table."}
      >
        {selectedEnrollment ? (
          <DetailList
            items={[
              { label: "Course", value: selectedEnrollment.course_name },
              { label: "Status", value: <StatusBadge status={selectedEnrollment.status} /> },
              { label: "Student ID", value: selectedEnrollment.student_id },
              { label: "Section ID", value: selectedEnrollment.section_id },
              { label: "University", value: selectedEnrollment.tenant_id },
              { label: "Enrolled", value: formatDate(selectedEnrollment.enrolled_at) },
            ]}
          />
        ) : (
          <ErrorState title="Enrollment not found" message="The selected enrollment is not present on this page of results." />
        )}
      </DrawerPanel>

      <DrawerPanel
        open={createOpen}
        onClose={() => {
          setCreateOpen(false);
          setStudentId("");
          setSectionId("");
        }}
        title="Enroll student"
        description="Create a new enrollment by student and section IDs."
      >
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="enrollment-student-id">Student ID</Label>
            <Input
              id="enrollment-student-id"
              value={studentId}
              onChange={(event) => setStudentId(event.target.value)}
              placeholder="student-1"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="enrollment-section-id">Section ID</Label>
            <Input
              id="enrollment-section-id"
              value={sectionId}
              onChange={(event) => setSectionId(event.target.value)}
              placeholder="section-1"
            />
          </div>
          <PermissionGate permission={PERMISSIONS.ENROLLMENTS_WRITE}>
            <Button
              disabled={!canCreate || createEnrollment.isPending}
              onClick={() =>
                createEnrollment.mutate(
                  { student_id: studentId.trim(), section_id: sectionId.trim() },
                  {
                    ...getHandlers({ successTitle: "Enrollment created" }),
                    onSuccess: () => {
                      setCreateOpen(false);
                      setStudentId("");
                      setSectionId("");
                    },
                  },
                )
              }
            >
              Create enrollment
            </Button>
          </PermissionGate>
        </div>
      </DrawerPanel>
    </div>
  );
}
