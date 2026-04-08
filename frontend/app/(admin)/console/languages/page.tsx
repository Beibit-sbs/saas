"use client";

import { useMemo, useState } from "react";
import { Languages } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { DataTable, type Column } from "@/shared/ui/data-table";
import { ErrorState } from "@/shared/ui/error-state";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { PageHeader } from "@/shared/ui/page-header";
import { PermissionGate } from "@/shared/ui/permission-gate";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useLanguage } from "@/app/components/LanguageProvider";
import { PERMISSIONS } from "@/shared/config/permissions";
import {
  useAddLanguage,
  useAdminLanguages,
  useDeleteLanguage,
  useLanguageCatalog,
  useSetDefaultLanguage,
  useToggleLanguage,
} from "@/modules/i18n-admin/hooks";
import type { AdminLanguage } from "@/modules/i18n-admin/types";

function LanguageRowActions({ row }: { row: AdminLanguage }) {
  const { t } = useLanguage();
  const tAny = (key: string) => t(key as never);
  const { getHandlers } = useMutationFeedback();
  const toggleLanguage = useToggleLanguage(row.code);
  const deleteLanguage = useDeleteLanguage();

  return (
    <PermissionGate permission={PERMISSIONS.I18N_MANAGE}>
      <div className="flex gap-1">
        <Button
          variant="outline"
          size="sm"
          disabled={toggleLanguage.isPending}
          onClick={() =>
            toggleLanguage.mutate(
              { enabled: !row.enabled },
              getHandlers({
                successTitle: row.enabled
                  ? tAny("languageDisabledMsg").replace("{code}", row.code)
                  : tAny("languageEnabledMsg").replace("{code}", row.code),
              }),
            )
          }
        >
          {row.enabled ? tAny("disable") : tAny("enable")}
        </Button>
        <Button
          variant="destructive"
          size="sm"
          disabled={deleteLanguage.isPending}
          onClick={() =>
            deleteLanguage.mutate(
              row.code,
              getHandlers({
                successTitle: tAny("languageDeletedMsg").replace("{code}", row.code),
              }),
            )
          }
        >
          {tAny("delete")}
        </Button>
      </div>
    </PermissionGate>
  );
}

export default function LanguagesPage() {
  const { t } = useLanguage();
  const tAny = (key: string) => t(key as never);
  const { getHandlers } = useMutationFeedback();

  const [newCode, setNewCode] = useState("");
  const [defaultCode, setDefaultCode] = useState("");

  const adminLanguagesQuery = useAdminLanguages();
  const catalogQuery = useLanguageCatalog();
  const addLanguage = useAddLanguage();
  const setDefaultLanguage = useSetDefaultLanguage();

  const adminData = adminLanguagesQuery.data;
  const options = useMemo(() => {
    const catalog = catalogQuery.data?.languages ?? [];
    if (catalog.length > 0) return catalog;
    return (adminData?.languages ?? []).map((l) => ({
      code: l.code,
      name: l.name,
      native_name: l.native_name ?? undefined,
    }));
  }, [catalogQuery.data?.languages, adminData?.languages]);

  if (adminLanguagesQuery.error) {
    return <ErrorState title="Failed to load languages" onRetry={adminLanguagesQuery.refetch} />;
  }

  const columns: Column<AdminLanguage>[] = [
    {
      key: "code",
      header: "Code",
      cell: (r) => r.code,
      sortValue: (r) => r.code,
    },
    {
      key: "name",
      header: tAny("language"),
      cell: (r) => r.name,
      sortValue: (r) => r.name,
    },
    {
      key: "native_name",
      header: tAny("nativeName"),
      cell: (r) => r.native_name ?? "-",
      sortValue: (r) => r.native_name ?? "",
    },
    {
      key: "enabled",
      header: tAny("status"),
      cell: (r) => (r.enabled ? tAny("enabled") : tAny("disabled")),
      sortValue: (r) => (r.enabled ? "1" : "0"),
    },
    {
      key: "actions",
      header: "",
      width: "170px",
      cell: (r) => <LanguageRowActions row={r} />,
    },
  ];

  const selectedCatalogItem = options.find((item) => item.code === newCode);

  return (
    <div className="space-y-6" data-testid="languages-page">
      <PageHeader
        title={t("nav.languages")}
        description={tAny("langHelp")}
        icon={Languages}
      />

      <section className="rounded-lg border bg-card p-4 space-y-3">
        <h2 className="text-sm font-semibold">{tAny("catalogTitle")}</h2>
        <p className="text-sm text-muted-foreground">{tAny("catalogHelp")}</p>
        <div className="grid gap-3 md:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="new-language-code">{tAny("selectedLanguage")}</Label>
            <select
              id="new-language-code"
              className="h-9 rounded-md border px-3 text-sm"
              value={newCode}
              onChange={(e) => setNewCode(e.target.value)}
            >
              <option value="">{tAny("noLanguageSelected")}</option>
              {options.map((item) => (
                <option key={item.code} value={item.code}>
                  {item.code} - {item.name}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="default-language">{tAny("setDefaultLanguage")}</Label>
            <select
              id="default-language"
              className="h-9 rounded-md border px-3 text-sm"
              value={defaultCode || adminData?.default_language || ""}
              onChange={(e) => setDefaultCode(e.target.value)}
            >
              {(adminData?.languages ?? []).map((item) => (
                <option key={item.code} value={item.code}>
                  {item.code} - {item.name}
                </option>
              ))}
            </select>
          </div>
        </div>
        <PermissionGate permission={PERMISSIONS.I18N_MANAGE}>
          <div className="flex flex-wrap gap-2">
            <Button
              disabled={
                addLanguage.isPending ||
                !selectedCatalogItem ||
                (adminData?.languages ?? []).some((l) => l.code === selectedCatalogItem.code)
              }
              onClick={() => {
                if (!selectedCatalogItem) return;
                addLanguage.mutate(
                  {
                    code: selectedCatalogItem.code,
                    name: selectedCatalogItem.name,
                    native_name: selectedCatalogItem.native_name ?? undefined,
                  },
                  getHandlers({ successTitle: tAny("languageAdded") }),
                );
              }}
            >
              {tAny("addLanguage")}
            </Button>
            <Button
              variant="outline"
              disabled={setDefaultLanguage.isPending || !(defaultCode || adminData?.default_language)}
              onClick={() =>
                setDefaultLanguage.mutate(
                  { code: defaultCode || adminData?.default_language || "" },
                  getHandlers({
                    successTitle: tAny("defaultLanguageUpdatedMsg").replace(
                      "{code}",
                      defaultCode || adminData?.default_language || "",
                    ),
                  }),
                )
              }
            >
              {tAny("setDefaultLanguage")}
            </Button>
          </div>
        </PermissionGate>
      </section>

      <section className="rounded-lg border bg-card p-4 space-y-3">
        <h2 className="text-sm font-semibold">{tAny("systemLanguages")}</h2>
        <DataTable
          columns={columns}
          data={adminData?.languages ?? []}
          isLoading={adminLanguagesQuery.isLoading || catalogQuery.isLoading}
          getRowKey={(r) => r.code}
          emptyTitle={tAny("noCatalogResults")}
        />
      </section>
    </div>
  );
}
