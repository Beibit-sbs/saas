"use client";

import { useMemo, useState } from "react";
import { LifeBuoy } from "lucide-react";
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
  useCreateStudentServiceTicket,
  useStudentServiceTickets,
  useUpdateStudentServiceTicketStatus,
} from "@/modules/student_services/hooks";
import type { StudentServiceTicket } from "@/modules/student_services/types";

interface TicketFormState {
  student_id: string;
  category: string;
  subject: string;
  description: string;
  priority: string;
  owner_id: string;
}

const EMPTY_FORM: TicketFormState = {
  student_id: "",
  category: "registrar",
  subject: "",
  description: "",
  priority: "medium",
  owner_id: "",
};

const STATUS_COLORS: Record<string, string> = {
  open: "bg-blue-100 text-blue-700",
  in_progress: "bg-amber-100 text-amber-700",
  resolved: "bg-green-100 text-green-700",
  closed: "bg-gray-100 text-gray-700",
};

export default function StudentServicesPage() {
  const { getHandlers } = useMutationFeedback();
  const [form, setForm] = useState<TicketFormState>(EMPTY_FORM);

  const { data, isLoading, error, refetch } = useStudentServiceTickets();
  const createTicket = useCreateStudentServiceTicket();
  const updateStatus = useUpdateStudentServiceTicketStatus();

  const isSubmitting = createTicket.isPending || updateStatus.isPending;
  const canCreate = useMemo(() => {
    const studentId = Number(form.student_id);
    return (
      Number.isInteger(studentId) &&
      studentId > 0 &&
      form.subject.trim().length > 0 &&
      form.description.trim().length > 0
    );
  }, [form]);

  if (error) {
    return <ErrorState title="Failed to load student service tickets" onRetry={refetch} />;
  }

  const columns: Column<StudentServiceTicket>[] = [
    {
      key: "student_id",
      header: "Student ID",
      cell: (row) => <span className="font-medium">{row.student_id}</span>,
      sortValue: (row) => row.student_id,
    },
    {
      key: "category",
      header: "Category",
      cell: (row) => row.category,
      sortValue: (row) => row.category.toLowerCase(),
    },
    {
      key: "subject",
      header: "Subject",
      cell: (row) => row.subject,
      sortValue: (row) => row.subject.toLowerCase(),
    },
    {
      key: "priority",
      header: "Priority",
      cell: (row) => row.priority,
      sortValue: (row) => row.priority,
    },
    {
      key: "status",
      header: "Status",
      cell: (row) => <Badge className={STATUS_COLORS[row.status] ?? ""}>{row.status}</Badge>,
      sortValue: (row) => row.status,
    },
    {
      key: "actions",
      header: "",
      width: "140px",
      cell: (row) => (
        <Button
          variant="outline"
          size="sm"
          disabled={isSubmitting || (row.status !== "open" && row.status !== "in_progress")}
          onClick={(event) => {
            event.stopPropagation();
            updateStatus.mutate(
              { ticketId: row.id, payload: { status: "resolved" } },
              getHandlers({ successTitle: "Ticket resolved" }),
            );
          }}
        >
          Resolve
        </Button>
      ),
    },
  ];

  return (
    <RequirePermission permission={PERMISSIONS.STUDENT_SERVICES_READ}>
      <div className="space-y-4" data-testid="student-services-page">
        <PageHeader
          title="Student Services"
          description="Track student service requests across registrar, finance, and campus operations."
          icon={LifeBuoy}
        />

        <div className="grid gap-3 rounded-lg border p-4 md:grid-cols-3">
          <div className="space-y-1">
            <Label htmlFor="student-id">Student ID</Label>
            <Input
              id="student-id"
              value={form.student_id}
              onChange={(e) => setForm((prev) => ({ ...prev, student_id: e.target.value }))}
              placeholder="101"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="category">Category</Label>
            <Input
              id="category"
              value={form.category}
              onChange={(e) => setForm((prev) => ({ ...prev, category: e.target.value }))}
              placeholder="registrar"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="priority">Priority</Label>
            <Input
              id="priority"
              value={form.priority}
              onChange={(e) => setForm((prev) => ({ ...prev, priority: e.target.value }))}
              placeholder="medium"
            />
          </div>
          <div className="space-y-1 md:col-span-3">
            <Label htmlFor="subject">Subject</Label>
            <Input
              id="subject"
              value={form.subject}
              onChange={(e) => setForm((prev) => ({ ...prev, subject: e.target.value }))}
              placeholder="Need enrollment certificate"
            />
          </div>
          <div className="space-y-1 md:col-span-3">
            <Label htmlFor="description">Description</Label>
            <Input
              id="description"
              value={form.description}
              onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))}
              placeholder="Student requested certificate for visa office"
            />
          </div>
          <div className="space-y-1 md:col-span-3">
            <Label htmlFor="owner-id">Owner ID</Label>
            <Input
              id="owner-id"
              value={form.owner_id}
              onChange={(e) => setForm((prev) => ({ ...prev, owner_id: e.target.value }))}
              placeholder="STAFF-42"
            />
          </div>

          <div className="md:col-span-3">
            <Button
              size="sm"
              data-testid="create-ticket-btn"
              disabled={!canCreate || isSubmitting}
              onClick={() => {
                createTicket.mutate(
                  {
                    student_id: Number(form.student_id),
                    category: form.category.trim(),
                    subject: form.subject.trim(),
                    description: form.description.trim(),
                    priority: form.priority.trim() as StudentServiceTicket["priority"],
                    owner_id: form.owner_id.trim() || undefined,
                    channel: "portal",
                  },
                  {
                    ...getHandlers({ successTitle: "Ticket created" }),
                    onSuccess: () => {
                      getHandlers({ successTitle: "Ticket created" }).onSuccess(undefined);
                      setForm(EMPTY_FORM);
                    },
                  },
                );
              }}
            >
              Create ticket
            </Button>
          </div>
        </div>

        <DataTable
          columns={columns}
          data={data?.items ?? []}
          isLoading={isLoading}
          getRowKey={(row) => String(row.id)}
          emptyTitle="No service tickets found."
        />
      </div>
    </RequirePermission>
  );
}
