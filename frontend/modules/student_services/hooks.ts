import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPatch, apiPost } from "@/shared/api/client";
import type {
  StudentServiceTicketCreatePayload,
  StudentServiceTicketItemResponse,
  StudentServiceTicketListResponse,
  StudentTicketStatus,
  StudentServiceTicketStatusUpdatePayload,
} from "./types";

const BASE = "/api/admin/student-services/tickets";
const TICKETS_KEY = "student-service-tickets";

export function useStudentServiceTickets(status?: StudentTicketStatus, studentId?: number) {
  const params: Record<string, string | number> = {};
  if (status) params.status = status;
  if (studentId) params.student_id = studentId;

  return useQuery({
    queryKey: [TICKETS_KEY, status ?? "all", studentId ?? "all"],
    queryFn: () =>
      apiGet<StudentServiceTicketListResponse>(
        BASE,
        Object.keys(params).length > 0 ? params : undefined,
      ),
  });
}

export function useCreateStudentServiceTicket() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: StudentServiceTicketCreatePayload) =>
      apiPost<StudentServiceTicketItemResponse>(BASE, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [TICKETS_KEY] }),
  });
}

export function useUpdateStudentServiceTicketStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      ticketId,
      payload,
    }: {
      ticketId: number;
      payload: StudentServiceTicketStatusUpdatePayload;
    }) => apiPatch<StudentServiceTicketItemResponse>(`${BASE}/${ticketId}/status`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [TICKETS_KEY] }),
  });
}
