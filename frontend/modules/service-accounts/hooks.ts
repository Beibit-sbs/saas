import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/shared/api/client";
import type {
  ServiceAccountsResponse,
  CreateServiceAccountPayload,
  IssueTokenPayload,
  IssueTokenResponse,
} from "./types";

const BASE = "/api/admin/service-accounts";

export const SERVICE_ACCOUNTS_KEY = "service-accounts";

export function useServiceAccounts() {
  return useQuery({
    queryKey: [SERVICE_ACCOUNTS_KEY],
    queryFn: () => apiGet<ServiceAccountsResponse>(BASE),
  });
}

export function useCreateServiceAccount() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateServiceAccountPayload) =>
      apiPost<{ account: { account_id: string } }>(BASE, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: [SERVICE_ACCOUNTS_KEY] }),
  });
}

export function useIssueServiceToken(accountId: string) {
  return useMutation({
    mutationFn: (payload: IssueTokenPayload) =>
      apiPost<IssueTokenResponse>(`${BASE}/${accountId}/token`, payload),
  });
}

export function useRevokeServiceAccount() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (accountId: string) =>
      apiPost<{ revoked: boolean; account_id: string }>(
        `${BASE}/${accountId}/revoke`,
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: [SERVICE_ACCOUNTS_KEY] }),
  });
}
