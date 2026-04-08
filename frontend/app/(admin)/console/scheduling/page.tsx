"use client";

import { PageHeader } from "@/shared/ui/page-header";
import { DataTable, Column } from "@/shared/ui/data-table";
import { FilterBar } from "@/shared/ui/filter-bar";
import { StatusBadge } from "@/shared/ui/status-badge";
import { ErrorState } from "@/shared/ui/error-state";
import { useTableQueryState } from "@/shared/hooks/use-table-query-state";
import { useSections } from "@/modules/scheduling/hooks";
import { CourseSection } from "@/modules/scheduling/types";
import { Calendar } from "lucide-react";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { PERMISSIONS } from "@/shared/config/permissions";
import { AccessDenied } from "@/shared/ui/permission-gate";
import { useLanguage } from "@/app/components/LanguageProvider";

const FILTER_FIELDS = [
  { key: "semester", label: "Semester", type: "text" as const, placeholder: "e.g. 2024-spring" },
  {
    key: "status",
    label: "Status",
    type: "select" as const,
    options: [
      { label: "Open", value: "open" },
      { label: "Closed", value: "closed" },
      { label: "Cancelled", value: "cancelled" },
    ],
  },
];

export default function SchedulingPage() {
  const { t } = useLanguage();
  const { hasPermission } = usePermissions();
  const table = useTableQueryState({ filterKeys: ["semester", "status"] as const, defaultPageSize: 20, defaultSort: { key: "semester", direction: "desc" } });

  const { data, isLoading, error, refetch } = useSections({
    page: table.page,
    page_size: table.pageSize,
    semester: table.filters.semester,
    status: table.filters.status,
  });

  if (!hasPermission(PERMISSIONS.SCHEDULING_READ)) return <AccessDenied />;

  if (error) {
    return <ErrorState title="Failed to load sections" onRetry={refetch} />;
  }

  const columns: Column<CourseSection>[] = [
    { key: "code", header: "Code", cell: (r) => <code className="text-xs">{r.code}</code>, sortValue: (r) => r.code },
    { key: "course", header: "Course", cell: (r) => r.course_name, sortValue: (r) => r.course_name.toLowerCase() },
    { key: "instructor", header: "Instructor", cell: (r) => r.instructor ?? "—", sortValue: (r) => r.instructor ?? "" },
    { key: "semester", header: "Semester", cell: (r) => r.semester, sortValue: (r) => r.semester },
    { key: "schedule", header: "Schedule", cell: (r) => r.schedule ?? "—" },
    { key: "room", header: "Room", cell: (r) => r.room ?? "—", sortValue: (r) => r.room ?? "" },
    {
      key: "capacity",
      header: "Capacity",
      cell: (r) => `${r.enrolled_count} / ${r.capacity}`,
      sortValue: (r) => r.enrolled_count,
    },
    { key: "status", header: "Status", cell: (r) => <StatusBadge status={r.status} />, sortValue: (r) => r.status },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title={t("nav.scheduling")}
        description={t("console.scheduling.description")}
        icon={Calendar}
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
        emptyTitle="No sections found"
      />
    </div>
  );
}
