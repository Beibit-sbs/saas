"use client";

import { useState } from "react";
import { PageHeader } from "@/shared/ui/page-header";
import { DataTable, Column } from "@/shared/ui/data-table";
import { FilterBar } from "@/shared/ui/filter-bar";
import { StatusBadge } from "@/shared/ui/status-badge";
import { ErrorState } from "@/shared/ui/error-state";
import { Button } from "@/shared/ui/button";
import { DrawerPanel } from "@/shared/ui/drawer-panel";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { PermissionGate } from "@/shared/ui/permission-gate";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useTableQueryState } from "@/shared/hooks/use-table-query-state";
import { useCreateSection, useSections } from "@/modules/scheduling/hooks";
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
  const [createOpen, setCreateOpen] = useState(false);
  const [code, setCode] = useState("");
  const [courseName, setCourseName] = useState("");
  const [instructor, setInstructor] = useState("");
  const [capacity, setCapacity] = useState("30");
  const [semester, setSemester] = useState("");
  const [scheduleValue, setScheduleValue] = useState("");
  const [room, setRoom] = useState("");
  const [tenantId, setTenantId] = useState("1");
  const { getHandlers } = useMutationFeedback();
  const table = useTableQueryState({ filterKeys: ["semester", "status"] as const, defaultPageSize: 20, defaultSort: { key: "semester", direction: "desc" } });

  const { data, isLoading, error, refetch } = useSections({
    page: table.page,
    page_size: table.pageSize,
    semester: table.filters.semester,
    status: table.filters.status,
  });
  const createSection = useCreateSection();
  const canCreateSection =
    code.trim().length > 0
    && courseName.trim().length > 0
    && semester.trim().length > 0
    && Number(capacity) >= 0
    && tenantId.trim().length > 0;

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
        actions={
          <PermissionGate permission={PERMISSIONS.SCHEDULING_WRITE}>
            <Button size="sm" onClick={() => setCreateOpen(true)}>
              Add section
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
        emptyTitle="No sections found"
      />

      <DrawerPanel
        open={createOpen}
        onClose={() => {
          setCreateOpen(false);
          setCode("");
          setCourseName("");
          setInstructor("");
          setCapacity("30");
          setSemester("");
          setScheduleValue("");
          setRoom("");
          setTenantId("1");
        }}
        title="Add section"
        description="Create a new course section."
      >
        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="section-code">Code</Label>
              <Input id="section-code" value={code} onChange={(e) => setCode(e.target.value)} placeholder="CS101-01" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="section-course-name">Course name</Label>
              <Input id="section-course-name" value={courseName} onChange={(e) => setCourseName(e.target.value)} placeholder="Intro to CS" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="section-instructor">Instructor</Label>
              <Input id="section-instructor" value={instructor} onChange={(e) => setInstructor(e.target.value)} placeholder="Dr. Smith" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="section-capacity">Capacity</Label>
              <Input id="section-capacity" value={capacity} onChange={(e) => setCapacity(e.target.value)} placeholder="30" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="section-semester">Semester</Label>
              <Input id="section-semester" value={semester} onChange={(e) => setSemester(e.target.value)} placeholder="2026-spring" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="section-room">Room</Label>
              <Input id="section-room" value={room} onChange={(e) => setRoom(e.target.value)} placeholder="Room 201" />
            </div>
            <div className="space-y-1.5 sm:col-span-2">
              <Label htmlFor="section-schedule">Schedule</Label>
              <Input id="section-schedule" value={scheduleValue} onChange={(e) => setScheduleValue(e.target.value)} placeholder="MWF 10:00" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="section-tenant-id">Tenant ID</Label>
              <Input id="section-tenant-id" value={tenantId} onChange={(e) => setTenantId(e.target.value)} placeholder="1" />
            </div>
          </div>

          <PermissionGate permission={PERMISSIONS.SCHEDULING_WRITE}>
            <Button
              disabled={!canCreateSection || createSection.isPending}
              onClick={() =>
                createSection.mutate(
                  {
                    code: code.trim(),
                    course_name: courseName.trim(),
                    instructor: instructor.trim() || undefined,
                    capacity: Number(capacity),
                    semester: semester.trim(),
                    schedule: scheduleValue.trim() || undefined,
                    room: room.trim() || undefined,
                    tenant_id: tenantId.trim(),
                  },
                  {
                    ...getHandlers({ successTitle: "Section created" }),
                    onSuccess: () => {
                      setCreateOpen(false);
                      setCode("");
                      setCourseName("");
                      setInstructor("");
                      setCapacity("30");
                      setSemester("");
                      setScheduleValue("");
                      setRoom("");
                      setTenantId("1");
                    },
                  },
                )
              }
            >
              Create section
            </Button>
          </PermissionGate>
        </div>
      </DrawerPanel>
    </div>
  );
}
