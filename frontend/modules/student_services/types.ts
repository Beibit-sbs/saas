export type StudentTicketPriority = "low" | "medium" | "high" | "urgent";

export type StudentTicketStatus = "open" | "in_progress" | "resolved" | "closed";

export interface StudentServiceTicket {
  id: number;
  tenant_id?: string | null;
  student_id: number;
  category: string;
  subject: string;
  description: string;
  priority: StudentTicketPriority;
  status: StudentTicketStatus;
  owner_id?: string | null;
  channel: string;
  resolution_notes?: string | null;
}

export interface StudentServiceTicketListResponse {
  items: StudentServiceTicket[];
}

export interface StudentServiceTicketItemResponse {
  item: StudentServiceTicket;
}

export interface StudentServiceTicketCreatePayload {
  student_id: number;
  category: string;
  subject: string;
  description: string;
  priority: StudentTicketPriority;
  owner_id?: string | null;
  channel?: string;
}

export interface StudentServiceTicketStatusUpdatePayload {
  status: StudentTicketStatus;
  resolution_notes?: string | null;
}
