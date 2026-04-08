"use client";

import { useState } from "react";
import { Network, Building2, Users, TrendingUp, AlertTriangle } from "lucide-react";

import { PERMISSIONS } from "@/shared/config/permissions";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { ErrorState } from "@/shared/ui/error-state";
import { PageHeader } from "@/shared/ui/page-header";
import { PermissionGate, RequirePermission } from "@/shared/ui/permission-gate";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import {
  useInstitutions,
  useCreateInstitution,
  useInstitutionOverview,
  useLinkTenant,
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
  const [newName, setNewName] = useState("");
  const [newCode, setNewCode] = useState("");
  const [newCountry, setNewCountry] = useState("");
  const [newType, setNewType] = useState("university");
  const [linkTenantId, setLinkTenantId] = useState("");
  const [linkRole, setLinkRole] = useState("institution_admin");
  const { getHandlers } = useMutationFeedback();
  const institutions = useInstitutions();
  const createInstitution = useCreateInstitution();
  const linkTenant = useLinkTenant(selectedId ?? 0);

  const selectedInstitution =
    selectedId !== null
      ? (institutions.data ?? []).find((i) => i.id === selectedId) ?? null
      : null;

  const canCreateInstitution =
    newName.trim().length > 0 && newCode.trim().length > 0 && newCountry.trim().length > 0;
  const canLinkTenant = selectedId !== null && Number(linkTenantId) > 0;

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
          actions={
            <PermissionGate permission={PERMISSIONS.FEDERATION_WRITE}>
              <Button
                size="sm"
                disabled={createInstitution.isPending || !canCreateInstitution}
                onClick={() =>
                  createInstitution.mutate(
                    {
                      name: newName.trim(),
                      code: newCode.trim(),
                      country: newCountry.trim(),
                      type: newType.trim() || "university",
                    },
                    {
                      ...getHandlers({ successTitle: "Institution created" }),
                      onSuccess: () => {
                        setNewName("");
                        setNewCode("");
                        setNewCountry("");
                        setNewType("university");
                      },
                    },
                  )
                }
              >
                Create institution
              </Button>
            </PermissionGate>
          }
        />

        <PermissionGate permission={PERMISSIONS.FEDERATION_WRITE}>
          <div className="rounded-lg border bg-card p-4 space-y-3" data-testid="federation-create-panel">
            <p className="text-sm font-medium">New institution</p>
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
              <div className="space-y-1.5">
                <Label htmlFor="federation-name">Name</Label>
                <Input id="federation-name" value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Northwind University" />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="federation-code">Code</Label>
                <Input id="federation-code" value={newCode} onChange={(e) => setNewCode(e.target.value)} placeholder="NORTHWIND" />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="federation-country">Country</Label>
                <Input id="federation-country" value={newCountry} onChange={(e) => setNewCountry(e.target.value)} placeholder="Kazakhstan" />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="federation-type">Type</Label>
                <Input id="federation-type" value={newType} onChange={(e) => setNewType(e.target.value)} placeholder="university" />
              </div>
            </div>
          </div>
        </PermissionGate>

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

                  <PermissionGate permission={PERMISSIONS.FEDERATION_WRITE}>
                    <div className="rounded border p-3 space-y-3" data-testid="federation-link-panel">
                      <p className="text-sm font-medium">Link tenant</p>
                      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                        <div className="space-y-1.5">
                          <Label htmlFor="federation-link-tenant-id">Tenant ID</Label>
                          <Input
                            id="federation-link-tenant-id"
                            value={linkTenantId}
                            onChange={(event) => setLinkTenantId(event.target.value)}
                            placeholder="2"
                          />
                        </div>
                        <div className="space-y-1.5">
                          <Label htmlFor="federation-link-role">Role</Label>
                          <Input
                            id="federation-link-role"
                            value={linkRole}
                            onChange={(event) => setLinkRole(event.target.value)}
                            placeholder="institution_admin"
                          />
                        </div>
                        <div className="flex items-end">
                          <Button
                            className="w-full"
                            disabled={!canLinkTenant || linkTenant.isPending}
                            onClick={() =>
                              linkTenant.mutate(
                                {
                                  tenant_id: Number(linkTenantId),
                                  role: linkRole.trim() || "institution_admin",
                                },
                                {
                                  ...getHandlers({ successTitle: "Tenant linked" }),
                                  onSuccess: () => {
                                    setLinkTenantId("");
                                    setLinkRole("institution_admin");
                                  },
                                },
                              )
                            }
                          >
                            Link tenant
                          </Button>
                        </div>
                      </div>
                    </div>
                  </PermissionGate>
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
