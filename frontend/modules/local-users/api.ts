import { apiGet, apiPost, apiPatch, apiDelete } from "@/shared/api/client";
import type {
  LocalUsersResponse,
  CreateLocalUserPayload,
  UpdateLocalUserPayload,
  SetPasswordPayload,
} from "./types";

const BASE = "/api/admin/local-users";

export const localUsersApi = {
  list: (params?: { search?: string; role?: string; language?: string }) =>
    apiGet<LocalUsersResponse>(BASE, params),

  create: (payload: CreateLocalUserPayload) =>
    apiPost<{ user: { user_id: string } }>(BASE, payload),

  update: (userId: string, payload: UpdateLocalUserPayload) =>
    apiPatch<{ user: { user_id: string } }>(`${BASE}/${userId}`, payload),

  delete: (userId: string) =>
    apiDelete<{ status: string; user_id: string }>(`${BASE}/${userId}`),

  setPassword: (userId: string, payload: SetPasswordPayload) =>
    apiPost<{ status: string }>(`${BASE}/${userId}/password`, payload),
};
