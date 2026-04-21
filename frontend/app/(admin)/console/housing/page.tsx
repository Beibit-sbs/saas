"use client";

import { useMemo, useState } from "react";
import { Home } from "lucide-react";
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
  useCreateHousingRequest,
  useHousingRequests,
  useUpdateHousingRequestStatus,
} from "@/modules/housing/hooks";
import type { HousingRequest } from "@/modules/housing/types";

interface HousingFormState {
  student_id: string;
  request_type: string;
  dormitory: string;
  room_preference: string;
  manager_id: string;
  notes: string;
}

const EMPTY_FORM: HousingFormState = {
  student_id: "",
  request_type: "assignment",
  dormitory: "",
  room_preference: "",
  manager_id: "",
  notes: "",
};

const STATUS_COLORS: Record<string, string> = {
  submitted: "bg-blue-100 text-blue-700",
  in_review: "bg-amber-100 text-amber-700",
  approved: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
  completed: "bg-gray-100 text-gray-700",
};

export default function HousingPage() {
  const { getHandlers } = useMutationFeedback();
  const [form, setForm] = useState<HousingFormState>(EMPTY_FORM);

  const { data, isLoading, error, refetch } = useHousingRequests();
  const createRequest = useCreateHousingRequest();
  const updateStatus = useUpdateHousingRequestStatus();

  const isSubmitting = createRequest.isPending || updateStatus.isPending;
  const canCreate = useMemo(() => {
    const studentId = Number(form.student_id);
    return Number.isInteger(studentId) && studentId > 0 && form.dormitory.trim().length > 0;
  }, [form]);

  if (error) {
    return <ErrorState title="Failed to load housing requests" onRetry={refetch} />;
  }

  const columns: Column<HousingRequest>[] = [
    {
      key: "student_id",
      header: "Student ID",
      cell: (row) => <span className="font-medium">{row.student_id}</span>,
      sortValue: (row) => row.student_id,
    },
    {
      key: "request_type",
      header: "Type",
      cell: (row) => row.request_type,
      sortValue: (row) => row.request_type,
    },
    {
      key: "dormitory",
      header: "Dormitory",
      cell: (row) => row.dormitory,
      sortValue: (row) => row.dormitory.toLowerCase(),
    },
    {
      key: "room_preference",
      header: "Room",
      cell: (row) => row.room_preference ?? "—",
      sortValue: (row) => row.room_preference ?? "",
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
      width: "170px",
      cell: (row) => (
        <Button
          variant="outline"
          size="sm"
          disabled={isSubmitting || (row.status !== "submitted" && row.status !== "in_review")}
          onClick={(event) => {
            event.stopPropagation();
            updateStatus.mutate(
              { requestId: row.id, payload: { status: "approved" } },
              getHandlers({ successTitle: "Request approved" }),
            );
          }}
        >
          Approve
        </Button>
      ),
    },
  ];

  return (
    <RequirePermission permission={PERMISSIONS.HOUSING_READ}>
      <div className="space-y-4" data-testid="housing-page">
        <PageHeader
          title="Dormitory & Housing"
          description="Track housing applications, transfers, and dorm operations."
          icon={Home}
        />

        <div className="grid gap-3 rounded-lg border p-4 md:grid-cols-3">
          <div className="space-y-1">
            <Label htmlFor="student-id">Student ID</Label>
            <Input
              id="student-id"
              value={form.student_id}
              onChange={(e) => setForm((prev) => ({ ...prev, student_id: e.target.value }))}
              placeholder="410"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="request-type">Request type</Label>
            <Input
              id="request-type"
              value={form.request_type}
              onChange={(e) => setForm((prev) => ({ ...prev, request_type: e.target.value }))}
              placeholder="assignment"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="dormitory">Dormitory</Label>
            <Input
              id="dormitory"
              value={form.dormitory}
              onChange={(e) => setForm((prev) => ({ ...prev, dormitory: e.target.value }))}
              placeholder="North Hall"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="room-preference">Room preference</Label>
            <Input
              id="room-preference"
              value={form.room_preference}
              onChange={(e) => setForm((prev) => ({ ...prev, room_preference: e.target.value }))}
              placeholder="double"
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="manager-id">Manager ID</Label>
            <Input
              id="manager-id"
              value={form.manager_id}
              onChange={(e) => setForm((prev) => ({ ...prev, manager_id: e.target.value }))}
              placeholder="HSG-1"
            />
          </div>
          <div className="space-y-1 md:col-span-3">
            <Label htmlFor="notes">Notes</Label>
            <Input
              id="notes"
              value={form.notes}
              onChange={(e) => setForm((prev) => ({ ...prev, notes: e.target.value }))}
              placeholder="Needs quiet floor"
            />
          </div>

          <div className="md:col-span-3">
            <Button
              size="sm"
              data-testid="create-housing-btn"
              disabled={!canCreate || isSubmitting}
              onClick={() => {
                createRequest.mutate(
                  {
                    student_id: Number(form.student_id),
                    request_type: form.request_type.trim() as HousingRequest["request_type"],
                    dormitory: form.dormitory.trim(),
                    room_preference: form.room_preference.trim() || undefined,
                    manager_id: form.manager_id.trim() || undefined,
                    notes: form.notes.trim() || undefined,
                  },
                  {
                    ...getHandlers({ successTitle: "Housing request created" }),
                    onSuccess: () => {
                      getHandlers({ successTitle: "Housing request created" }).onSuccess(undefined);
                      setForm(EMPTY_FORM);
                    },
                  },
                );
              }}
            >
              Create request
            </Button>
          </div>
        </div>

        <DataTable
          columns={columns}
          data={data?.items ?? []}
          isLoading={isLoading}
          getRowKey={(row) => String(row.id)}
          emptyTitle="No housing requests found."
        />
      </div>
    </RequirePermission>
  );
}
