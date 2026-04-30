"use client";

import { useMemo, useState } from "react";
import { Wrench } from "lucide-react";
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
  useCreateMaintenanceRequest,
  useCreateWorkOrder,
  useMaintenanceRequests,
  useUpdateMaintenanceRequestStatus,
  useUpdateWorkOrderStatus,
  useWorkOrders,
} from "@/modules/facilities-work-orders/hooks";
import type {
  MaintenanceRequest,
  MaintenanceRequestStatus,
  WorkOrder,
  WorkOrderStatus,
} from "@/modules/facilities-work-orders/types";

interface OrderFormState {
  order_code: string;
  facility_code: string;
  title: string;
}

interface RequestFormState {
  request_code: string;
  facility_code: string;
}

const EMPTY_ORDER: OrderFormState = { order_code: "", facility_code: "", title: "" };
const EMPTY_REQUEST: RequestFormState = { request_code: "", facility_code: "" };

const ORDER_STATUS_COLORS: Record<WorkOrderStatus, string> = {
  open: "bg-yellow-100 text-yellow-700",
  in_progress: "bg-blue-100 text-blue-700",
  on_hold: "bg-orange-100 text-orange-700",
  completed: "bg-green-100 text-green-700",
  cancelled: "bg-gray-100 text-gray-700",
};

const REQUEST_STATUS_COLORS: Record<MaintenanceRequestStatus, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  assigned: "bg-blue-100 text-blue-700",
  in_progress: "bg-indigo-100 text-indigo-700",
  resolved: "bg-green-100 text-green-700",
  closed: "bg-gray-100 text-gray-700",
};

const NEXT_ORDER_STATUS: Record<WorkOrderStatus, WorkOrderStatus[]> = {
  open: ["in_progress", "cancelled"],
  in_progress: ["on_hold", "completed", "cancelled"],
  on_hold: ["in_progress", "cancelled"],
  completed: [],
  cancelled: [],
};

const NEXT_REQUEST_STATUS: Record<MaintenanceRequestStatus, MaintenanceRequestStatus[]> = {
  pending: ["assigned"],
  assigned: ["in_progress"],
  in_progress: ["resolved"],
  resolved: ["closed"],
  closed: [],
};

export default function FacilitiesWorkOrdersPage() {
  const { getHandlers } = useMutationFeedback();
  const [orderForm, setOrderForm] = useState<OrderFormState>(EMPTY_ORDER);
  const [requestForm, setRequestForm] = useState<RequestFormState>(EMPTY_REQUEST);

  const orders = useWorkOrders();
  const requests = useMaintenanceRequests();
  const createOrder = useCreateWorkOrder();
  const createRequest = useCreateMaintenanceRequest();
  const updateOrderStatus = useUpdateWorkOrderStatus();
  const updateRequestStatus = useUpdateMaintenanceRequestStatus();

  const error = orders.error ?? requests.error;
  const refetch = () => {
    orders.refetch();
    requests.refetch();
  };

  const isSubmitting =
    createOrder.isPending ||
    createRequest.isPending ||
    updateOrderStatus.isPending ||
    updateRequestStatus.isPending;

  const canCreateOrder = useMemo(
    () =>
      orderForm.order_code.trim().length > 0 &&
      orderForm.facility_code.trim().length > 0 &&
      orderForm.title.trim().length > 0,
    [orderForm],
  );

  const canCreateRequest = useMemo(
    () =>
      requestForm.request_code.trim().length > 0 &&
      requestForm.facility_code.trim().length > 0,
    [requestForm],
  );

  if (error) {
    return <ErrorState title="Failed to load facilities data" onRetry={refetch} />;
  }

  const orderColumns: Column<WorkOrder>[] = [
    {
      key: "order_code",
      header: "Order Code",
      cell: (row) => <span className="font-mono text-xs">{row.order_code}</span>,
      sortValue: (row) => row.order_code,
    },
    {
      key: "facility_code",
      header: "Facility",
      cell: (row) => row.facility_code,
      sortValue: (row) => row.facility_code,
    },
    {
      key: "title",
      header: "Title",
      cell: (row) => <span className="font-medium">{row.title}</span>,
      sortValue: (row) => row.title.toLowerCase(),
    },
    {
      key: "work_type",
      header: "Type",
      cell: (row) => row.work_type,
      sortValue: (row) => row.work_type,
    },
    {
      key: "priority",
      header: "Priority",
      cell: (row) => (
        <Badge
          className={
            row.priority === "critical"
              ? "bg-red-100 text-red-700"
              : row.priority === "high"
                ? "bg-orange-100 text-orange-700"
                : row.priority === "medium"
                  ? "bg-yellow-100 text-yellow-700"
                  : "bg-gray-100 text-gray-700"
          }
        >
          {row.priority}
        </Badge>
      ),
      sortValue: (row) => row.priority,
    },
    {
      key: "status",
      header: "Status",
      cell: (row) => (
        <Badge className={ORDER_STATUS_COLORS[row.status]}>{row.status}</Badge>
      ),
      sortValue: (row) => row.status,
    },
    {
      key: "actions",
      header: "Actions",
      cell: (row) => {
        const nexts = NEXT_ORDER_STATUS[row.status] ?? [];
        if (nexts.length === 0) return null;
        return (
          <div className="flex gap-1 flex-wrap">
            {nexts.map((next) => (
              <Button
                key={next}
                variant="outline"
                size="sm"
                disabled={isSubmitting}
                onClick={() =>
                  updateOrderStatus.mutate(
                    { orderId: row.id, payload: { status: next } },
                    getHandlers({ successTitle: `Order moved to ${next}` }),
                  )
                }
              >
                → {next}
              </Button>
            ))}
          </div>
        );
      },
    },
  ];

  const requestColumns: Column<MaintenanceRequest>[] = [
    {
      key: "request_code",
      header: "Request Code",
      cell: (row) => <span className="font-mono text-xs">{row.request_code}</span>,
      sortValue: (row) => row.request_code,
    },
    {
      key: "facility_code",
      header: "Facility",
      cell: (row) => row.facility_code,
      sortValue: (row) => row.facility_code,
    },
    {
      key: "issue_type",
      header: "Issue Type",
      cell: (row) => row.issue_type,
      sortValue: (row) => row.issue_type,
    },
    {
      key: "severity",
      header: "Severity",
      cell: (row) => (
        <Badge
          className={
            row.severity === "critical"
              ? "bg-red-100 text-red-700"
              : row.severity === "high"
                ? "bg-orange-100 text-orange-700"
                : "bg-gray-100 text-gray-700"
          }
        >
          {row.severity}
        </Badge>
      ),
      sortValue: (row) => row.severity,
    },
    {
      key: "status",
      header: "Status",
      cell: (row) => (
        <Badge className={REQUEST_STATUS_COLORS[row.status]}>{row.status}</Badge>
      ),
      sortValue: (row) => row.status,
    },
    {
      key: "actions",
      header: "Actions",
      cell: (row) => {
        const nexts = NEXT_REQUEST_STATUS[row.status] ?? [];
        if (nexts.length === 0) return null;
        return (
          <div className="flex gap-1 flex-wrap">
            {nexts.map((next) => (
              <Button
                key={next}
                variant="outline"
                size="sm"
                disabled={isSubmitting}
                onClick={() =>
                  updateRequestStatus.mutate(
                    { reqId: row.id, payload: { status: next } },
                    getHandlers({ successTitle: `Request moved to ${next}` }),
                  )
                }
              >
                → {next}
              </Button>
            ))}
          </div>
        );
      },
    },
  ];

  return (
    <RequirePermission permission={PERMISSIONS.FACILITIES_READ}>
      <div className="space-y-8">
        <PageHeader
          title="Facilities & Work Orders"
          description="Manage work orders and maintenance requests for campus facilities"
          icon={Wrench}
        />

        <RequirePermission permission={PERMISSIONS.FACILITIES_WRITE}>
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-lg font-semibold mb-4">Create Work Order</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label htmlFor="order_code">Order Code</Label>
                <Input
                  id="order_code"
                  placeholder="WO-2026-001"
                  value={orderForm.order_code}
                  onChange={(e) => setOrderForm((f) => ({ ...f, order_code: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="order_facility">Facility Code</Label>
                <Input
                  id="order_facility"
                  placeholder="FAC-001"
                  value={orderForm.facility_code}
                  onChange={(e) => setOrderForm((f) => ({ ...f, facility_code: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="order_title">Title</Label>
                <Input
                  id="order_title"
                  placeholder="Repair HVAC unit"
                  value={orderForm.title}
                  onChange={(e) => setOrderForm((f) => ({ ...f, title: e.target.value }))}
                />
              </div>
            </div>
            <Button
              className="mt-4"
              disabled={!canCreateOrder || isSubmitting}
              onClick={() => {
                if (!canCreateOrder) return;
                createOrder.mutate(
                  {
                    order_code: orderForm.order_code.trim(),
                    facility_code: orderForm.facility_code.trim(),
                    title: orderForm.title.trim(),
                    work_type: "repair",
                    priority: "medium",
                    status: "open",
                  },
                  {
                    ...getHandlers({ successTitle: "Work order created" }),
                    onSuccess: (...args) => {
                      setOrderForm(EMPTY_ORDER);
                      getHandlers({ successTitle: "Work order created" }).onSuccess?.(args[0]);
                    },
                  },
                );
              }}
            >
              {createOrder.isPending ? "Creating..." : "Create Work Order"}
            </Button>
          </div>
        </RequirePermission>

        <DataTable
          columns={orderColumns}
          data={orders.data?.items ?? []}
          isLoading={orders.isLoading}
          getRowKey={(row) => String(row.id)}
          emptyTitle="No work orders found"
          emptyDescription="Create your first work order above."
        />

        <RequirePermission permission={PERMISSIONS.FACILITIES_WRITE}>
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-lg font-semibold mb-4">Submit Maintenance Request</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="request_code">Request Code</Label>
                <Input
                  id="request_code"
                  placeholder="MR-2026-001"
                  value={requestForm.request_code}
                  onChange={(e) => setRequestForm((f) => ({ ...f, request_code: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="req_facility">Facility Code</Label>
                <Input
                  id="req_facility"
                  placeholder="FAC-002"
                  value={requestForm.facility_code}
                  onChange={(e) => setRequestForm((f) => ({ ...f, facility_code: e.target.value }))}
                />
              </div>
            </div>
            <Button
              className="mt-4"
              disabled={!canCreateRequest || isSubmitting}
              onClick={() => {
                if (!canCreateRequest) return;
                createRequest.mutate(
                  {
                    request_code: requestForm.request_code.trim(),
                    facility_code: requestForm.facility_code.trim(),
                    issue_type: "other",
                    severity: "medium",
                    status: "pending",
                  },
                  {
                    ...getHandlers({ successTitle: "Maintenance request submitted" }),
                    onSuccess: (...args) => {
                      setRequestForm(EMPTY_REQUEST);
                      getHandlers({ successTitle: "Maintenance request submitted" }).onSuccess?.(args[0]);
                    },
                  },
                );
              }}
            >
              {createRequest.isPending ? "Submitting..." : "Submit Request"}
            </Button>
          </div>
        </RequirePermission>

        <DataTable
          columns={requestColumns}
          data={requests.data?.items ?? []}
          isLoading={requests.isLoading}
          getRowKey={(row) => String(row.id)}
          emptyTitle="No maintenance requests found"
          emptyDescription="Submit your first maintenance request above."
        />
      </div>
    </RequirePermission>
  );
}
