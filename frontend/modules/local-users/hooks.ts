import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { localUsersApi } from "./api";
import type {
  CreateLocalUserPayload,
  UpdateLocalUserPayload,
  SetPasswordPayload,
} from "./types";

export const LOCAL_USERS_KEY = "local-users";

export function useLocalUsers(params?: {
  search?: string;
  role?: string;
  language?: string;
}) {
  return useQuery({
    queryKey: [LOCAL_USERS_KEY, params],
    queryFn: () => localUsersApi.list(params),
  });
}

export function useCreateLocalUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateLocalUserPayload) =>
      localUsersApi.create(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [LOCAL_USERS_KEY] }),
  });
}

export function useUpdateLocalUser(userId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateLocalUserPayload) =>
      localUsersApi.update(userId, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [LOCAL_USERS_KEY] }),
  });
}

export function useDeleteLocalUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) => localUsersApi.delete(userId),
    onSuccess: () => qc.invalidateQueries({ queryKey: [LOCAL_USERS_KEY] }),
  });
}

export function useSetLocalUserPassword(userId: string) {
  return useMutation({
    mutationFn: (payload: SetPasswordPayload) =>
      localUsersApi.setPassword(userId, payload),
  });
}
