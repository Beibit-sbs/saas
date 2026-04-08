"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/shared/ui/page-header";
import { DataTable, Column } from "@/shared/ui/data-table";
import { FilterBar } from "@/shared/ui/filter-bar";
import { StatusBadge } from "@/shared/ui/status-badge";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { DrawerPanel } from "@/shared/ui/drawer-panel";
import { DetailList } from "@/shared/ui/detail-list";
import { ErrorState } from "@/shared/ui/error-state";
import { useDetailDrawer } from "@/shared/hooks/use-detail-drawer";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useTableQueryState } from "@/shared/hooks/use-table-query-state";
import { useCreateStudent, useStudents } from "@/modules/students/hooks";
import { Student } from "@/modules/students/types";
import { formatDate } from "@/shared/utils/format";
import { GraduationCap, Plus } from "lucide-react";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { PERMISSIONS } from "@/shared/config/permissions";
import { AccessDenied, PermissionGate } from "@/shared/ui/permission-gate";
import { useLanguage } from "@/app/components/LanguageProvider";

export default function StudentsPage() {
  const { t } = useLanguage();
  const { hasPermission } = usePermissions();
  const router = useRouter();
  const [createOpen, setCreateOpen] = useState(false);
  const [personId, setPersonId] = useState("");
  const [studentNumber, setStudentNumber] = useState("");
  const [cohortYear, setCohortYear] = useState("2026");
  const table = useTableQueryState({ filterKeys: ["search", "status"] as const, defaultPageSize: 20, defaultSort: { key: "created", direction: "desc" } });
  const detail = useDetailDrawer({ paramKey: "student" });
  const { getHandlers } = useMutationFeedback();

  const { data, isLoading, error, refetch } = useStudents({
    page: table.page,
    page_size: table.pageSize,
    search: table.filters.search,
    status: table.filters.status,
  });
  const createStudent = useCreateStudent();
  const selectedStudent = data?.items.find((item) => item.id === detail.selectedId) ?? null;
  const canCreate = personId.trim().length > 0 && studentNumber.trim().length > 0 && cohortYear.trim().length > 0;

  const filterFields = useMemo(
    () => [
      { key: "search", label: t("students.filter.search"), type: "text" as const, placeholder: t("students.filter.searchPlaceholder") },
      {
        key: "status",
        label: t("students.filter.status"),
        type: "select" as const,
        options: [
          { label: t("students.status.active"), value: "active" },
          { label: t("students.status.inactive"), value: "inactive" },
          { label: t("students.status.graduated"), value: "graduated" },
          { label: t("students.status.suspended"), value: "suspended" },
        ],
      },
    ],
    [t],
  );

  if (!hasPermission(PERMISSIONS.STUDENTS_READ)) return <AccessDenied />;

  if (error) {
    return <ErrorState title={t("students.loadFailed")} onRetry={refetch} />;
  }

  const columns: Column<Student>[] = [
    { key: "number", header: "#", width: "100px", cell: (r) => <code className="text-xs">{r.student_number}</code>, sortValue: (r) => r.student_number },
    {
      key: "name",
      header: t("students.columns.name"),
      cell: (r) => (
        <span className="font-medium">
          {r.first_name} {r.last_name}
        </span>
      ),
      sortValue: (r) => `${r.first_name} ${r.last_name}`.toLowerCase(),
    },
    { key: "email", header: t("students.columns.email"), cell: (r) => r.email, sortValue: (r) => r.email.toLowerCase() },
    { key: "program", header: t("students.columns.program"), cell: (r) => r.program ?? "-", sortValue: (r) => r.program ?? "" },
    { key: "status", header: t("students.columns.status"), cell: (r) => <StatusBadge status={r.status} />, sortValue: (r) => r.status },
    { key: "created", header: t("students.columns.enrolled"), cell: (r) => formatDate(r.created_at), sortValue: (r) => r.created_at },
    {
      key: "actions",
      header: "",
      width: "80px",
      cell: (r) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={(event) => {
            event.stopPropagation();
            router.push(`/console/students/${r.id}`);
          }}
        >
          {t("students.actions.view")}
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title={t("nav.students")}
        description={t("console.students.description")}
        icon={GraduationCap}
        actions={
          <PermissionGate permission={PERMISSIONS.STUDENTS_WRITE}>
            <Button size="sm" onClick={() => setCreateOpen(true)}>
              <Plus className="h-4 w-4 mr-1" />
              {t("students.createAction")}
            </Button>
          </PermissionGate>
        }
      />

      <FilterBar
        fields={filterFields}
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
        emptyTitle={t("students.emptyTitle")}
      />

      <DrawerPanel
        open={detail.isOpen}
        onClose={detail.close}
        title={selectedStudent ? `${selectedStudent.first_name} ${selectedStudent.last_name}` : t("students.summaryTitle")}
        description={selectedStudent?.student_number ?? t("students.selectFromTable")}
      >
        {selectedStudent ? (
          <DetailList
            items={[
              { label: t("students.columns.email"), value: selectedStudent.email },
              { label: t("students.columns.status"), value: <StatusBadge status={selectedStudent.status} /> },
              { label: t("students.columns.program"), value: selectedStudent.program ?? "-" },
              { label: t("students.columns.enrollmentYear"), value: selectedStudent.enrollment_year ?? "-" },
              { label: t("students.columns.tenant"), value: selectedStudent.tenant_id },
              { label: t("students.columns.created"), value: formatDate(selectedStudent.created_at) },
            ]}
          />
        ) : (
          <ErrorState title={t("students.notFound")} message={t("students.notFoundDescription")} />
        )}
      </DrawerPanel>

      <DrawerPanel
        open={createOpen}
        onClose={() => {
          setCreateOpen(false);
          setPersonId("");
          setStudentNumber("");
          setCohortYear("2026");
        }}
        title={t("students.createTitle")}
        description={t("students.createDescription")}
      >
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="student-person-id">{t("students.create.personId")}</Label>
            <Input
              id="student-person-id"
              value={personId}
              onChange={(event) => setPersonId(event.target.value)}
              placeholder="101"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="student-number">{t("students.create.studentNumber")}</Label>
            <Input
              id="student-number"
              value={studentNumber}
              onChange={(event) => setStudentNumber(event.target.value)}
              placeholder="ADM-1-1001"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="student-cohort-year">{t("students.create.cohortYear")}</Label>
            <Input
              id="student-cohort-year"
              value={cohortYear}
              onChange={(event) => setCohortYear(event.target.value)}
              placeholder="2026"
            />
          </div>
          <PermissionGate permission={PERMISSIONS.STUDENTS_WRITE}>
            <Button
              disabled={!canCreate || createStudent.isPending}
              onClick={() =>
                createStudent.mutate(
                  {
                    person_id: Number(personId),
                    student_number: studentNumber.trim(),
                    cohort_year: Number(cohortYear),
                    admission_source: "manual",
                  },
                  {
                    ...getHandlers({ successTitle: t("students.createdSuccess") }),
                    onSuccess: () => {
                      setCreateOpen(false);
                      setPersonId("");
                      setStudentNumber("");
                      setCohortYear("2026");
                    },
                  },
                )
              }
            >
              {t("students.createAction")}
            </Button>
          </PermissionGate>
        </div>
      </DrawerPanel>
    </div>
  );
}
