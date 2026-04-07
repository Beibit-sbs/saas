"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/shared/ui/page-header";
import { DataTable, Column } from "@/shared/ui/data-table";
import { FilterBar } from "@/shared/ui/filter-bar";
import { StatusBadge } from "@/shared/ui/status-badge";
import { Button } from "@/shared/ui/button";
import { DrawerPanel } from "@/shared/ui/drawer-panel";
import { DetailList } from "@/shared/ui/detail-list";
import { ErrorState } from "@/shared/ui/error-state";
import { useDetailDrawer } from "@/shared/hooks/use-detail-drawer";
import { useTableQueryState } from "@/shared/hooks/use-table-query-state";
import { useStudents } from "@/modules/students/hooks";
import { Student } from "@/modules/students/types";
import { formatDate } from "@/shared/utils/format";
import { GraduationCap } from "lucide-react";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { PERMISSIONS } from "@/shared/config/permissions";
import { AccessDenied } from "@/shared/ui/permission-gate";
import { useLanguage } from "@/app/components/LanguageProvider";

export default function StudentsPage() {
  const { t } = useLanguage();
  const { hasPermission } = usePermissions();
  const router = useRouter();
  const table = useTableQueryState({ filterKeys: ["search", "status"] as const, defaultPageSize: 20, defaultSort: { key: "created", direction: "desc" } });
  const detail = useDetailDrawer({ paramKey: "student" });

  const { data, isLoading, error, refetch } = useStudents({
    page: table.page,
    page_size: table.pageSize,
    search: table.filters.search,
    status: table.filters.status,
  });
  const selectedStudent = data?.items.find((item) => item.id === detail.selectedId) ?? null;

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
      <PageHeader title={t("nav.students")} description={t("console.students.description")} icon={GraduationCap} />

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
    </div>
  );
}
