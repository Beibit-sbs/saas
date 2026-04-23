import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPatch, apiPost } from "@/shared/api/client";
import type {
  MaintenanceRequestCreatePayload,
  MaintenanceRequestItemResponse,
  MaintenanceRequestListResponse,
  MaintenanceRequestStatus,
  MaintenanceRequestStatusUpdatePayload,
  WorkOrderCreatePayload,
  WorkOrderItemResponse,
  WorkOrderListResponse,
  WorkOrderPriority,
  WorkOrderStatus,
  WorkOrderStatusUpdatePayload,
  WorkOrderType,
} from "./types";

const BASE = "/api/admin/facilities";
const ORDERS_KEY = "facilities-work-orders";
const REQUESTS_KEY = "facilities-maintenance-requests";

export function useWorkOrders(filters?: {
  status?: WorkOrderStatus;
  priority?: WorkOrderPriority;
  work_type?: WorkOrderType;
}) {
  const params: Record<string, string> = {};
  if (filters?.status) params.status = filters.status;
  if (filters?.priority) params.priority = filters.priority;
  if (filters?.work_type) params.work_type = filters.work_type;

  return useQuery({
    queryKey: [ORDERS_KEY, filters?.status ?? "all", filters?.priority ?? "all"],
    queryFn: () =>
      apiGet<WorkOrderListResponse>(
        `${BASE}/work-orders`,
        Object.keys(params).length > 0 ? params : undefined,
      ),
  });
}

export function useCreateWorkOrder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: WorkOrderCreatePayload) =>
      apiPost<WorkOrderItemResponse>(`${BASE}/work-orders`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [ORDERS_KEY] }),
  });
}

export function useUpdateWorkOrderStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      orderId,
      payload,
    }: {
      orderId: number;
      payload: WorkOrderStatusUpdatePayload;
    }) => apiPatch<WorkOrderItemResponse>(`${BASE}/work-orders/${orderId}/status`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [ORDERS_KEY] }),
  });
}

export function useMaintenanceRequests(filters?: { status?: MaintenanceRequestStatus }) {
  return useQuery({
    queryKey: [REQUESTS_KEY, filters?.status ?? "all"],
    queryFn: () =>
      apiGet<MaintenanceRequestListResponse>(
        `${BASE}/maintenance-requests`,
        filters?.status ? { status: filters.status } : undefined,
      ),
  });
}

export function useCreateMaintenanceRequest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: MaintenanceRequestCreatePayload) =>
      apiPost<MaintenanceRequestItemResponse>(`${BASE}/maintenance-requests`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [REQUESTS_KEY] }),
  });
}

export function useUpdateMaintenanceRequestStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      reqId,
      payload,
    }: {
      reqId: number;
      payload: MaintenanceRequestStatusUpdatePayload;
    }) => apiPatch<MaintenanceRequestItemResponse>(`${BASE}/maintenance-requests/${reqId}/status`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [REQUESTS_KEY] }),
  });
}
