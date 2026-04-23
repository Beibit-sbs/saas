export type WorkOrderPriority = "low" | "medium" | "high" | "critical";
export type WorkOrderType = "repair" | "maintenance" | "installation" | "inspection";
export type WorkOrderStatus = "open" | "in_progress" | "on_hold" | "completed" | "cancelled";

export type MaintenanceRequestSeverity = "low" | "medium" | "high" | "critical";
export type MaintenanceRequestIssueType = "plumbing" | "electrical" | "hvac" | "structural" | "other";
export type MaintenanceRequestStatus = "pending" | "assigned" | "in_progress" | "resolved" | "closed";

export interface WorkOrder {
  id: number;
  tenant_id?: string | null;
  order_code: string;
  facility_code: string;
  title: string;
  work_type: WorkOrderType;
  priority: WorkOrderPriority;
  assigned_to?: string | null;
  status: WorkOrderStatus;
}

export interface WorkOrderListResponse {
  items: WorkOrder[];
}

export interface WorkOrderItemResponse {
  item: WorkOrder;
}

export interface WorkOrderCreatePayload {
  order_code: string;
  facility_code: string;
  title: string;
  work_type?: WorkOrderType;
  priority?: WorkOrderPriority;
  assigned_to?: string | null;
  status?: WorkOrderStatus;
}

export interface WorkOrderStatusUpdatePayload {
  status: WorkOrderStatus;
}

export interface MaintenanceRequest {
  id: number;
  tenant_id?: string | null;
  request_code: string;
  facility_code: string;
  issue_type: MaintenanceRequestIssueType;
  severity: MaintenanceRequestSeverity;
  notes?: string | null;
  status: MaintenanceRequestStatus;
}

export interface MaintenanceRequestListResponse {
  items: MaintenanceRequest[];
}

export interface MaintenanceRequestItemResponse {
  item: MaintenanceRequest;
}

export interface MaintenanceRequestCreatePayload {
  request_code: string;
  facility_code: string;
  issue_type?: MaintenanceRequestIssueType;
  severity?: MaintenanceRequestSeverity;
  notes?: string | null;
  status?: MaintenanceRequestStatus;
}

export interface MaintenanceRequestStatusUpdatePayload {
  status: MaintenanceRequestStatus;
}
