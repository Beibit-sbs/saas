import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiRequestError, apiGet, apiPost, apiPut } from "@/shared/api/client";
import type {
  ConvertAmountPayload,
  ConvertAmountResult,
  ExchangeRate,
  ExchangeRateUpsertPayload,
  FormatMoneyResult,
  TenantLocalePayload,
  TenantLocaleProfile,
} from "./types";

const ADMIN_BASE = "/api/admin/currency-localization";

export const TENANT_LOCALE_QUERY_KEY = "currency-localization-tenant-locale";

export function useTenantLocale(tenantId: number) {
  return useQuery({
    queryKey: [TENANT_LOCALE_QUERY_KEY, tenantId],
    enabled: tenantId > 0,
    queryFn: async () => {
      try {
        return await apiGet<TenantLocaleProfile>(`${ADMIN_BASE}/tenant-locale/${tenantId}`);
      } catch (error) {
        if (error instanceof ApiRequestError && error.status === 404) {
          return null;
        }
        throw error;
      }
    },
  });
}

export function useSetTenantLocale() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: TenantLocalePayload) =>
      apiPut<TenantLocaleProfile>(`${ADMIN_BASE}/tenant-locale`, payload),
    onSuccess: (data) => {
      queryClient.setQueryData([TENANT_LOCALE_QUERY_KEY, data.tenant_id], data);
    },
  });
}

export function useUpsertExchangeRate() {
  return useMutation({
    mutationFn: (payload: ExchangeRateUpsertPayload) =>
      apiPut<ExchangeRate>(`${ADMIN_BASE}/exchange-rates`, payload),
  });
}

export function useConvertAmount() {
  return useMutation({
    mutationFn: (payload: ConvertAmountPayload) =>
      apiPost<ConvertAmountResult>(`${ADMIN_BASE}/convert`, payload),
  });
}

export function useFormatMoneyPreview() {
  return useMutation({
    mutationFn: ({ amount, currency_code }: { amount: number; currency_code: string }) =>
      apiGet<FormatMoneyResult>(`${ADMIN_BASE}/format-money`, { amount, currency_code }),
  });
}