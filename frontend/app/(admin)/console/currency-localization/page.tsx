"use client";

import { useEffect, useState } from "react";
import { Globe2 } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { ErrorState } from "@/shared/ui/error-state";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { PERMISSIONS } from "@/shared/config/permissions";
import {
  useConvertAmount,
  useFormatMoneyPreview,
  useSetTenantLocale,
  useTenantLocale,
  useUpsertExchangeRate,
} from "@/modules/currency-localization/hooks";

export default function CurrencyLocalizationPage() {
  const { getHandlers } = useMutationFeedback();
  const [tenantId, setTenantId] = useState(1);
  const [currencyCode, setCurrencyCode] = useState("KZT");
  const [languageCode, setLanguageCode] = useState("ru");
  const [timezone, setTimezone] = useState("Asia/Almaty");
  const [baseCurrency, setBaseCurrency] = useState("USD");
  const [quoteCurrency, setQuoteCurrency] = useState("KZT");
  const [exchangeRate, setExchangeRate] = useState("500");
  const [convertAmount, setConvertAmountValue] = useState("10");
  const [fromCurrency, setFromCurrency] = useState("USD");
  const [toCurrency, setToCurrency] = useState("KZT");
  const [formatAmount, setFormatAmount] = useState("10");
  const [formatCurrencyCode, setFormatCurrencyCode] = useState("USD");

  const localeQuery = useTenantLocale(tenantId);
  const setTenantLocale = useSetTenantLocale();
  const upsertExchangeRate = useUpsertExchangeRate();
  const convertCurrency = useConvertAmount();
  const formatMoney = useFormatMoneyPreview();

  useEffect(() => {
    if (!localeQuery.data) return;

    setCurrencyCode(localeQuery.data.currency_code);
    setLanguageCode(localeQuery.data.language_code);
    setTimezone(localeQuery.data.timezone);
  }, [localeQuery.data]);

  if (localeQuery.error) {
    return (
      <ErrorState
        title="Currency localization data unavailable"
        message="Could not load tenant localization settings."
        onRetry={() => void localeQuery.refetch()}
      />
    );
  }

  return (
    <RequirePermission permission={PERMISSIONS.I18N_MANAGE}>
      <div className="space-y-6" data-testid="currency-localization-page">
        <PageHeader
          title="Currency Localization"
          description="Manage tenant locale defaults, exchange rates, conversion preview, and formatting."
          icon={Globe2}
        />

        <section className="rounded-lg border bg-card p-4 space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-1.5">
              <Label htmlFor="tenant-id">Tenant ID</Label>
              <Input
                id="tenant-id"
                type="number"
                min={1}
                value={tenantId}
                onChange={(event) => setTenantId(Number(event.target.value) || 0)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="currency-code">Preferred currency</Label>
              <Input
                id="currency-code"
                value={currencyCode}
                onChange={(event) => setCurrencyCode(event.target.value.toUpperCase())}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="language-code">Preferred language</Label>
              <Input
                id="language-code"
                value={languageCode}
                onChange={(event) => setLanguageCode(event.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="timezone">Timezone</Label>
              <Input
                id="timezone"
                value={timezone}
                onChange={(event) => setTimezone(event.target.value)}
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button
              type="button"
              disabled={tenantId <= 0 || setTenantLocale.isPending}
              onClick={() =>
                setTenantLocale.mutate(
                  {
                    tenant_id: tenantId,
                    currency_code: currencyCode,
                    language_code: languageCode,
                    timezone,
                  },
                  getHandlers({ successTitle: `Tenant ${tenantId} locale saved` }),
                )
              }
            >
              Save tenant locale
            </Button>
            <Button type="button" variant="outline" onClick={() => void localeQuery.refetch()}>
              Refresh locale
            </Button>
          </div>

          <div className="rounded-md border bg-muted/30 p-3 text-sm">
            {localeQuery.isLoading ? (
              <p>Loading tenant locale...</p>
            ) : localeQuery.data ? (
              <p>
                Active profile: {localeQuery.data.currency_code} / {localeQuery.data.language_code} / {localeQuery.data.timezone}
              </p>
            ) : (
              <p>No tenant locale profile configured yet.</p>
            )}
          </div>
        </section>

        <section className="rounded-lg border bg-card p-4 space-y-4">
          <div>
            <h2 className="text-sm font-semibold">Exchange rate management</h2>
            <p className="text-sm text-muted-foreground">
              Upsert tenant-scoped exchange rates for the existing backend localization service.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-4">
            <div className="space-y-1.5">
              <Label htmlFor="base-currency">Base currency</Label>
              <Input
                id="base-currency"
                value={baseCurrency}
                onChange={(event) => setBaseCurrency(event.target.value.toUpperCase())}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="quote-currency">Quote currency</Label>
              <Input
                id="quote-currency"
                value={quoteCurrency}
                onChange={(event) => setQuoteCurrency(event.target.value.toUpperCase())}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="exchange-rate">Rate</Label>
              <Input
                id="exchange-rate"
                type="number"
                min={0}
                step="0.0001"
                value={exchangeRate}
                onChange={(event) => setExchangeRate(event.target.value)}
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button
              type="button"
              disabled={tenantId <= 0 || upsertExchangeRate.isPending}
              onClick={() =>
                upsertExchangeRate.mutate(
                  {
                    tenant_id: tenantId,
                    base_currency: baseCurrency,
                    quote_currency: quoteCurrency,
                    rate: Number(exchangeRate),
                  },
                  getHandlers({ successTitle: `${baseCurrency}/${quoteCurrency} rate saved` }),
                )
              }
            >
              Save exchange rate
            </Button>
            {upsertExchangeRate.data ? (
              <p className="text-sm text-muted-foreground">
                Active rate: {upsertExchangeRate.data.base_currency}/{upsertExchangeRate.data.quote_currency} = {upsertExchangeRate.data.rate}
              </p>
            ) : null}
          </div>
        </section>

        <section className="rounded-lg border bg-card p-4 space-y-4">
          <div>
            <h2 className="text-sm font-semibold">Conversion preview</h2>
            <p className="text-sm text-muted-foreground">
              Run a conversion through the admin API and inspect the formatted result.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-1.5">
              <Label htmlFor="convert-amount">Amount</Label>
              <Input
                id="convert-amount"
                type="number"
                min={0}
                step="0.01"
                value={convertAmount}
                onChange={(event) => setConvertAmountValue(event.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="from-currency">From currency</Label>
              <Input
                id="from-currency"
                value={fromCurrency}
                onChange={(event) => setFromCurrency(event.target.value.toUpperCase())}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="to-currency">To currency</Label>
              <Input
                id="to-currency"
                value={toCurrency}
                onChange={(event) => setToCurrency(event.target.value.toUpperCase())}
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button
              type="button"
              disabled={tenantId <= 0 || convertCurrency.isPending}
              onClick={() =>
                convertCurrency.mutate(
                  {
                    tenant_id: tenantId,
                    amount: Number(convertAmount),
                    from_currency: fromCurrency,
                    to_currency: toCurrency,
                  },
                  getHandlers({ successTitle: `Converted ${fromCurrency} to ${toCurrency}` }),
                )
              }
            >
              Convert amount
            </Button>
            {convertCurrency.data ? (
              <p className="text-sm text-muted-foreground">
                Result: {convertCurrency.data.converted_amount} ({convertCurrency.data.formatted_converted_amount})
              </p>
            ) : null}
          </div>
        </section>

        <section className="rounded-lg border bg-card p-4 space-y-4">
          <div>
            <h2 className="text-sm font-semibold">Formatting preview</h2>
            <p className="text-sm text-muted-foreground">
              Preview raw money formatting for a single currency without conversion.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <div className="space-y-1.5">
              <Label htmlFor="format-amount">Preview amount</Label>
              <Input
                id="format-amount"
                type="number"
                min={0}
                step="0.01"
                value={formatAmount}
                onChange={(event) => setFormatAmount(event.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="preview-currency">Preview currency</Label>
              <Input
                id="preview-currency"
                value={formatCurrencyCode}
                onChange={(event) => setFormatCurrencyCode(event.target.value.toUpperCase())}
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button
              type="button"
              disabled={formatMoney.isPending}
              onClick={() =>
                formatMoney.mutate(
                  {
                    amount: Number(formatAmount),
                    currency_code: formatCurrencyCode,
                  },
                  getHandlers({ successTitle: `Formatted ${formatCurrencyCode} amount` }),
                )
              }
            >
              Format amount
            </Button>
            {formatMoney.data ? (
              <p className="text-sm text-muted-foreground">Preview: {formatMoney.data.formatted}</p>
            ) : null}
          </div>
        </section>
      </div>
    </RequirePermission>
  );
}