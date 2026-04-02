"use client";

import { useState } from "react";
import { Network, Building2, Users, TrendingUp, AlertTriangle } from "lucide-react";

import { PERMISSIONS } from "@/shared/config/permissions";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { ErrorState } from "@/shared/ui/error-state";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import {
  useInstitutions,
  useInstitutionOverview,
} from "@/modules/platform/federation/use-federation";
import type { Institution } from "@/modules/platform/federation/types";
import { useLanguage } from "@/app/components/LanguageProvider";

function KpiCard({ title, value, icon: Icon }: { title: string; value: number; icon: React.ElementType }) {
  return (
    <div className="rounded-lg border bg-card p-4 flex items-center gap-4">
      <div className="rounded-full bg-muted p-2">
        <Icon className="h-5 w-5 text-muted-foreground" />
      </div>
      <div>
        <p className="text-xs text-muted-foreground">{title}</p>
        <p className="text-2xl font-semibold">{value.toLocaleString()}</p>
      </div>
    </div>
  );
}

function InstitutionOverviewPanel({ institution }: { institution: Institution }) {
  const overview = useInstitutionOverview(institution.id);

  if (overview.isError) {
    return (
      <ErrorState title="Failed to load overview" message="Could not retrieve institution overview." />
    );
  }

  if (!overview.data) {
    return <p className="text-sm text-muted-foreground">Loading overview…</p>;
  }

  const data = overview.data;

  return (
    <div className="space-y-4" data-testid={`institution-overview-${institution.id}`}>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <KpiCard title="Total Students" value={data.students_total} icon={Users} />
        <KpiCard title="Total Enrollments" value={data.enrollments_total} icon={TrendingUp} />
        <KpiCard
          title="Automation Failures"
          value={Number(data.automation_health?.automation_failures_total ?? 0)}
          icon={AlertTriangle}
        />
        <KpiCard title="Universities" value={data.tenant_count} icon={Building2} />
      </div>

      {data.kpi_cards.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground font-medium">All KPI Metrics</p>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {data.kpi_cards.map((card) => (
              <div
                key={card.metric_key}
                className="rounded border p-3"
                data-testid={`kpi-card-${card.metric_key}`}
              >
                <p className="text-xs text-muted-foreground">{card.title}</p>
                <p className="text-lg font-semibold">{card.value.toLocaleString()}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function InstitutionRow({
  institution,
  isSelected,
  onSelect,
}: {
  institution: Institution;
  isSelected: boolean;
  onSelect: () => void;
}) {
  return (
    <div
      className={`rounded-lg border p-4 cursor-pointer transition-colors ${
        isSelected ? "border-primary bg-primary/5" : "hover:bg-muted/50"
      }`}
      onClick={onSelect}
      data-testid={`institution-row-${institution.id}`}
    >
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <p className="font-medium text-sm">{institution.name}</p>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>{institution.code}</span>
            <span>·</span>
            <span>{institution.country}</span>
            <span>·</span>
            <span className="capitalize">{institution.type}</span>
          </div>
        </div>
        <Badge variant={institution.status === "active" ? "default" : "secondary"}>
          {institution.status}
        </Badge>
      </div>
    </div>
  );
}

export default function FederationPage() {
  const { t } = useLanguage();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const institutions = useInstitutions();

  const selectedInstitution =
    selectedId !== null
      ? (institutions.data ?? []).find((i) => i.id === selectedId) ?? null
      : null;

  return (
    <RequirePermission
      permission={PERMISSIONS.FEDERATION_READ}
      message="You need Federation read permission to access this panel."
    >
      <div className="space-y-6" data-testid="federation-page">
        <PageHeader
          title={t("nav.federation")}
          description={t("console.federation.description")}
          icon={Network}
        />

        {institutions.isError && (
          <ErrorState
            title="Failed to load institutions"
            message="Could not retrieve institution list."
          />
        )}

        {institutions.isLoading && (
          <p className="text-sm text-muted-foreground">Loading institutions…</p>
        )}

        {institutions.data && (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            {/* Institution list */}
            <div className="space-y-2 lg:col-span-1" data-testid="institution-list">
              {institutions.data.length === 0 ? (
                <p className="text-sm text-muted-foreground">No institutions registered yet.</p>
              ) : (
                institutions.data.map((inst) => (
                  <InstitutionRow
                    key={inst.id}
                    institution={inst}
                    isSelected={selectedId === inst.id}
                    onSelect={() => setSelectedId(selectedId === inst.id ? null : inst.id)}
                  />
                ))
              )}
            </div>

            {/* Overview panel */}
            <div className="lg:col-span-2">
              {selectedInstitution ? (
                <div className="rounded-lg border bg-card p-4 space-y-4">
                  <div className="flex items-center gap-2">
                    <Building2 className="h-4 w-4 text-muted-foreground" />
                    <p className="font-medium">{selectedInstitution.name}</p>
                  </div>
                  <InstitutionOverviewPanel institution={selectedInstitution} />
                </div>
              ) : (
                <div className="rounded-lg border bg-muted/20 p-8 text-center">
                  <Network className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                  <p className="text-sm text-muted-foreground">
                    Select an institution to view its overview.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </RequirePermission>
  );
}
