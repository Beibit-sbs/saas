import { useMutation, useQuery } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/shared/api/client";
import type { LdapStatusResponse, LdapTestPayload, LdapTestResponse } from "./types";

const BASE = "/api/admin/ldap";
export const LDAP_STATUS_KEY = "ldap-status";

export function useLdapStatus() {
  return useQuery({
    queryKey: [LDAP_STATUS_KEY],
    queryFn: () => apiGet<LdapStatusResponse>(`${BASE}/status`),
  });
}

export function useTestLdapConnection() {
  return useMutation({
    mutationFn: (payload: LdapTestPayload) =>
      apiPost<LdapTestResponse>(`${BASE}/test-connection`, payload),
  });
}
