export interface ExchangeRate {
  rate_id: number;
  tenant_id: number;
  base_currency: string;
  quote_currency: string;
  rate: number;
  active: boolean;
}

export interface ExchangeRateUpsertPayload {
  tenant_id: number;
  base_currency: string;
  quote_currency: string;
  rate: number;
}

export interface ConvertAmountPayload {
  tenant_id: number;
  amount: number;
  from_currency: string;
  to_currency: string;
}

export interface ConvertAmountResult {
  tenant_id: number;
  from_currency: string;
  to_currency: string;
  amount: number;
  converted_amount: number;
  formatted_converted_amount: string;
}

export interface TenantLocaleProfile {
  profile_id: number;
  tenant_id: number;
  currency_code: string;
  language_code: string;
  timezone: string;
}

export interface TenantLocalePayload {
  tenant_id: number;
  currency_code: string;
  language_code: string;
  timezone: string;
}

export interface FormatMoneyResult {
  amount: number;
  currency_code: string;
  formatted: string;
}