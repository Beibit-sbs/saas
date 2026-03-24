"use client";

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

const FILTER_FIELDS = [
  { key: "search", label: "Search", type: "text" as const, placeholder: "Name or email…" },
  {
    key: "status",
    label: "Status",
    type: "select" as const,
    options: [
      { label: "Active", value: "active" },
      { label: "Inactive", value: "inactive" },
      { label: "Graduated", value: "graduated" },
      { label: "Suspended", value: "suspended" },
    ],
  },
];

export default function StudentsPage() {
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

  if (error) {
    return <ErrorState title="Failed to load students" onRetry={refetch} />;
  }

  const columns: Column<Student>[] = [
    { key: "number", header: "#", width: "100px", cell: (r) => <code className="text-xs">{r.student_number}</code>, sortValue: (r) => r.student_number },
    {
      key: "name",
      header: "Name",
      cell: (r) => (
        <span className="font-medium">
          {r.first_name} {r.last_name}
        </span>
      ),
      sortValue: (r) => `${r.first_name} ${r.last_name}`.toLowerCase(),
    },
    { key: "email", header: "Email", cell: (r) => r.email, sortValue: (r) => r.email.toLowerCase() },
    { key: "program", header: "Program", cell: (r) => r.program ?? "—", sortValue: (r) => r.program ?? "" },
    { key: "status", header: "Status", cell: (r) => <StatusBadge status={r.status} />, sortValue: (r) => r.status },
    { key: "created", header: "Enrolled", cell: (r) => formatDate(r.created_at), sortValue: (r) => r.created_at },
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
          View
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <PageHeader title="Students" description="Academic student records" icon={GraduationCap} />

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
        emptyTitle="No students found"
      />

      <DrawerPanel
        open={detail.isOpen}
        onClose={detail.close}
        title={selectedStudent ? `${selectedStudent.first_name} ${selectedStudent.last_name}` : "Student summary"}
        description={selectedStudent?.student_number ?? "Select a student from the table."}
      >
        {selectedStudent ? (
          <DetailList
            items={[
              { label: "Email", value: selectedStudent.email },
              { label: "Status", value: <StatusBadge status={selectedStudent.status} /> },
              { label: "Program", value: selectedStudent.program ?? "—" },
              { label: "Enrollment year", value: selectedStudent.enrollment_year ?? "—" },
              { label: "Tenant", value: selectedStudent.tenant_id },
              { label: "Created", value: formatDate(selectedStudent.created_at) },
            ]}
          />
        ) : (
          <ErrorState title="Student not found" message="The selected student is not present on this page of results." />
        )}
      </DrawerPanel>
    </div>
  );
}
