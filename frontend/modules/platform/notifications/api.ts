import { apiGet, apiPost } from "@/shared/api/client";
import type { PaginatedResponse } from "@/shared/api/types";
import type { Notification, NotificationDispatchPayload } from "./types";

const BASE = "/api/v1/admin/notifications";

export const notificationsApi = {
  list: (params?: { page?: number; page_size?: number; read?: boolean }) =>
    apiGet<PaginatedResponse<Notification>>(BASE, params),

  markRead: (id: string) => apiPost<Notification>(`${BASE}/${id}/read`, {}),

  markAllRead: () => apiPost<void>(`${BASE}/mark-all-read`, {}),

  dispatch: (payload: NotificationDispatchPayload) => apiPost<unknown>(BASE, payload),
};
