"use client";

import { use } from "react";
import Link from "next/link";
import { PageHeader } from "@/shared/ui/page-header";
import { StatusBadge } from "@/shared/ui/status-badge";
import { DataTable, Column } from "@/shared/ui/data-table";
import { Button } from "@/shared/ui/button";
import { Skeleton } from "@/shared/ui/skeleton";
import { ErrorState } from "@/shared/ui/error-state";
import { useStudent } from "@/modules/students/hooks";
import { useEnrollments } from "@/modules/enrollments/hooks";
import { Enrollment } from "@/modules/enrollments/types";
import { formatDate } from "@/shared/utils/format";
import { GraduationCap, ChevronLeft, FileText } from "lucide-react";

const enrollmentColumns: Column<Enrollment>[] = [
  { key: "section", header: "Section", cell: (r) => <code className="text-xs">{r.section_code}</code> },
  { key: "course", header: "Course", cell: (r) => r.course_name },
  { key: "status", header: "Status", cell: (r) => <StatusBadge status={r.status} /> },
  { key: "enrolled", header: "Enrolled", cell: (r) => formatDate(r.enrolled_at) },
];

export default function StudentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: student, isLoading, error, refetch } = useStudent(id);
  const { data: enrollmentsData, isLoading: enrollmentsLoading } = useEnrollments({ student_id: id });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-16 rounded-lg" />
        <Skeleton className="h-40 rounded-lg" />
      </div>
    );
  }
  if (error || !student) return <ErrorState title="Student not found" onRetry={refetch} />;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/console/students">
          <Button variant="ghost" size="sm">
            <ChevronLeft className="h-4 w-4" />
          </Button>
        </Link>
        <PageHeader
          title={`${student.first_name} ${student.last_name}`}
          description={student.email}
          icon={GraduationCap}
          actions={
            <Link href={`/console/students/${id}/transcript`}>
              <Button variant="outline" size="sm">
                <FileText className="h-4 w-4 mr-1" />
                Transcript
              </Button>
            </Link>
          }
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { label: "Student #", value: student.student_number },
          { label: "Program", value: student.program ?? "—" },
          { label: "Status", value: <StatusBadge status={student.status} /> },
          { label: "Enrolled Year", value: student.enrollment_year ?? "—" },
          { label: "University", value: student.tenant_id },
          { label: "Created", value: formatDate(student.created_at) },
        ].map((item) => (
          <div key={item.label} className="rounded-lg border bg-card p-4">
            <p className="text-xs text-muted-foreground mb-1">{item.label}</p>
            <div className="font-medium text-sm">{item.value}</div>
          </div>
        ))}
      </div>

      <div className="space-y-2">
        <h2 className="text-sm font-medium">Enrollments</h2>
        <DataTable
          columns={enrollmentColumns}
          data={enrollmentsData?.items ?? []}
          isLoading={enrollmentsLoading}
          getRowKey={(r) => r.id}
          emptyTitle="No enrollments"
        />
      </div>
    </div>
  );
}
