import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/shared/api/client";
import type {
  DeveloperApiLog,
  DeveloperApp,
  DeveloperAppCreateRequest,
  DeveloperAppSecret,
  DeveloperInstallation,
} from "./types";

export const DEVELOPER_APPS_KEY = "platform-developer-apps";
export const DEVELOPER_APP_INSTALLATIONS_KEY = "platform-developer-app-installations";
export const DEVELOPER_APP_LOGS_KEY = "platform-developer-app-logs";

export function useDeveloperApps() {
  return useQuery({
    queryKey: [DEVELOPER_APPS_KEY],
    queryFn: () => apiGet<DeveloperApp[]>("/api/bff/admin/platform/developer/apps"),
    staleTime: 30_000,
  });
}

export function useDeveloperAppInstallations(appId: number | null) {
  return useQuery({
    queryKey: [DEVELOPER_APP_INSTALLATIONS_KEY, appId],
    queryFn: () => apiGet<DeveloperInstallation[]>(`/api/bff/admin/platform/developer/apps/${appId}/installations`),
    enabled: appId !== null && appId > 0,
    staleTime: 15_000,
  });
}

export function useDeveloperAppLogs(appId: number | null) {
  return useQuery({
    queryKey: [DEVELOPER_APP_LOGS_KEY, appId],
    queryFn: () => apiGet<DeveloperApiLog[]>(`/api/bff/admin/platform/developer/apps/${appId}/logs`),
    enabled: appId !== null && appId > 0,
    staleTime: 15_000,
  });
}

export function useCreateDeveloperApp() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: DeveloperAppCreateRequest) =>
      apiPost<DeveloperAppSecret>("/api/bff/admin/platform/developer/apps", payload),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: [DEVELOPER_APPS_KEY] });
    },
  });
}