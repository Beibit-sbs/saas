import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/shared/api/client";
import type {
  CreateProfilePersonPayload,
  ProfileDepartmentsResponse,
  ProfilePeopleResponse,
} from "./types";

const BASE = "/api/admin/profiles";
export const PROFILE_PEOPLE_KEY = "profile-people";
export const PROFILE_DEPARTMENTS_KEY = "profile-departments";

export function useProfilePeople(params?: {
  status?: string;
  page?: number;
  page_size?: number;
}) {
  const qs = new URLSearchParams();
  if (params?.status) qs.set("status", params.status);
  if (params?.page) qs.set("page", String(params.page));
  if (params?.page_size) qs.set("page_size", String(params.page_size));
  const suffix = qs.toString() ? `?${qs.toString()}` : "";

  return useQuery({
    queryKey: [PROFILE_PEOPLE_KEY, params],
    queryFn: () => apiGet<ProfilePeopleResponse>(`${BASE}/people${suffix}`),
  });
}

export function useProfileDepartments(params?: {
  page?: number;
  page_size?: number;
}) {
  const qs = new URLSearchParams();
  if (params?.page) qs.set("page", String(params.page));
  if (params?.page_size) qs.set("page_size", String(params.page_size));
  const suffix = qs.toString() ? `?${qs.toString()}` : "";

  return useQuery({
    queryKey: [PROFILE_DEPARTMENTS_KEY, params],
    queryFn: () =>
      apiGet<ProfileDepartmentsResponse>(`${BASE}/departments${suffix}`),
  });
}

export function useCreateProfilePerson() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateProfilePersonPayload) =>
      apiPost(`${BASE}/people`, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [PROFILE_PEOPLE_KEY] }),
  });
}
