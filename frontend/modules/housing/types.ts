export type HousingRequestType = "assignment" | "transfer" | "maintenance" | "checkout";

export type HousingRequestStatus = "submitted" | "in_review" | "approved" | "rejected" | "completed";

export interface HousingRequest {
  id: number;
  tenant_id?: string | null;
  student_id: number;
  request_type: HousingRequestType;
  dormitory: string;
  room_preference?: string | null;
  status: HousingRequestStatus;
  manager_id?: string | null;
  notes?: string | null;
}

export interface HousingRequestListResponse {
  items: HousingRequest[];
}

export interface HousingRequestItemResponse {
  item: HousingRequest;
}

export interface HousingRequestCreatePayload {
  student_id: number;
  request_type: HousingRequestType;
  dormitory: string;
  room_preference?: string | null;
  manager_id?: string | null;
  notes?: string | null;
}

export interface HousingRequestStatusUpdatePayload {
  status: HousingRequestStatus;
  notes?: string | null;
}
