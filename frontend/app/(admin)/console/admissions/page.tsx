"use client";

import { useMemo, useState } from "react";
import { GraduationCap, ChevronRight } from "lucide-react";
import { PageHeader } from "@/shared/ui/page-header";
import { DataTable, type Column } from "@/shared/ui/data-table";
import { FilterBar } from "@/shared/ui/filter-bar";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { DrawerPanel } from "@/shared/ui/drawer-panel";
import { DetailList } from "@/shared/ui/detail-list";
import { ErrorState } from "@/shared/ui/error-state";
import { AccessDenied } from "@/shared/ui/permission-gate";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import { useTableQueryState } from "@/shared/hooks/use-table-query-state";
import { useDetailDrawer } from "@/shared/hooks/use-detail-drawer";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { PERMISSIONS } from "@/shared/config/permissions";
import { formatRelative } from "@/shared/utils/format";
import { cn } from "@/shared/utils/cn";
import { useLanguage } from "@/app/components/LanguageProvider";
import {
  useApplicants,
  useCreateApplicant,
  useApplications,
  useApplication,
  useApplicationDocuments,
  useSubmitApplication,
  useTransitionStage,
  useMakeDecision,
  useApplicationDecision,
} from "@/modules/platform/admissions/hooks";
import type {
  Applicant,
  Application,
  ApplicationStage,
  ApplicationConclusionType,
  CreateApplicantPayload,
} from "@/modules/platform/admissions/types";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const STAGES: ApplicationStage[] = [
  "new",
  "received",
  "under_review",
  "decision_pending",
  "concluded",
];

const STAGE_ORDER: Record<ApplicationStage, number> = {
  new: 0,
  received: 1,
  under_review: 2,
  decision_pending: 3,
  concluded: 4,
};

function StageBadge({ stage }: { stage: ApplicationStage }) {
  const { t } = useLanguage();
  const variantMap: Record<
    ApplicationStage,
    "default" | "warning" | "success" | "destructive"
  > = {
    new: "default",
    received: "default",
    under_review: "warning",
    decision_pending: "warning",
    concluded: "success",
  };
  return (
    <Badge variant={variantMap[stage]}>{t(`admissions.stage.${stage}`)}</Badge>
  );
}

function ConclusionBadge({ type }: { type: ApplicationConclusionType | null }) {
  const { t } = useLanguage();
  if (!type) return <span className="text-muted-foreground">—</span>;
  const variantMap: Record<
    ApplicationConclusionType,
    "success" | "destructive" | "warning" | "default"
  > = {
    accepted: "success",
    rejected: "destructive",
    waitlist: "warning",
    withdrawn: "default",
  };
  return (
    <Badge variant={variantMap[type]}>
      {t(`admissions.conclusion.${type}`)}
    </Badge>
  );
}

function DocumentStatusBadge({
  status,
}: {
  status: "received" | "verified" | "rejected";
}) {
  const { t } = useLanguage();
  const variantMap: Record<
    typeof status,
    "default" | "success" | "destructive"
  > = {
    received: "default",
    verified: "success",
    rejected: "destructive",
  };
  return (
    <Badge variant={variantMap[status]}>
      {t(`admissions.doc.status.${status}`)}
    </Badge>
  );
}

function StageProgress({ current }: { current: ApplicationStage }) {
  const { t } = useLanguage();
  const currentIdx = STAGE_ORDER[current];
  return (
    <div className="flex items-center gap-1 flex-wrap">
      {STAGES.map((stage, idx) => (
        <div key={stage} className="flex items-center gap-1">
          <span
            className={cn(
              "rounded px-2 py-0.5 text-xs font-medium",
              idx < currentIdx && "bg-muted text-muted-foreground",
              idx === currentIdx && "bg-primary text-primary-foreground",
              idx > currentIdx && "bg-muted/40 text-muted-foreground/50",
            )}
          >
            {t(`admissions.stage.${stage}`)}
          </span>
          {idx < STAGES.length - 1 && (
            <ChevronRight className="h-3 w-3 text-muted-foreground/50 shrink-0" />
          )}
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Applicants tab
// ---------------------------------------------------------------------------

function ApplicantsTab({ canWrite }: { canWrite: boolean }) {
  const { t } = useLanguage();
  const { getHandlers } = useMutationFeedback();

  const table = useTableQueryState({
    filterKeys: ["application_year"] as const,
    defaultPageSize: 20,
    defaultSort: { key: "updated_at", direction: "desc" },
  });
  const detail = useDetailDrawer({ paramKey: "applicant" });

  const listQuery = useApplicants({
    page: table.page,
    page_size: table.pageSize,
    application_year: table.filters.application_year
      ? Number(table.filters.application_year)
      : undefined,
  });

  const createMutation = useCreateApplicant();

  const [form, setForm] = useState<Partial<CreateApplicantPayload>>({
    status: "active",
    application_year: new Date().getFullYear(),
    metadata_json: {},
  });
  const [showCreate, setShowCreate] = useState(false);

  const rows = Array.isArray(listQuery.data?.items) ? listQuery.data.items : [];

  const selectedApplicant =
    rows.find((r) => String(r.id) === detail.selectedId) ?? null;

  const columns: Column<Applicant>[] = useMemo(
    () => [
      {
        key: "id",
        header: "ID",
        width: "80px",
        cell: (row) => <code className="text-xs">#{row.id}</code>,
        sortValue: (row) => row.id,
      },
      {
        key: "name",
        header: t("admissions.col.name"),
        cell: (row) => (
          <span className="font-medium">
            {row.first_name} {row.last_name}
          </span>
        ),
        sortValue: (row) => row.last_name,
      },
      {
        key: "email",
        header: t("admissions.col.email"),
        cell: (row) => <span className="text-sm">{row.email}</span>,
        sortValue: (row) => row.email,
      },
      {
        key: "program_id",
        header: t("admissions.col.program"),
        cell: (row) => (
          <span className="font-mono text-xs">P-{row.program_id}</span>
        ),
        sortValue: (row) => row.program_id,
      },
      {
        key: "year",
        header: t("admissions.col.year"),
        cell: (row) => String(row.application_year),
        sortValue: (row) => row.application_year,
      },
      {
        key: "status",
        header: t("admissions.col.status"),
        cell: (row) => (
          <Badge variant={row.status === "active" ? "success" : "default"}>
            {row.status}
          </Badge>
        ),
        sortValue: (row) => row.status,
      },
      {
        key: "updated_at",
        header: t("admissions.col.updated"),
        cell: (row) => formatRelative(row.updated_at),
        sortValue: (row) => row.updated_at,
      },
    ],
    [t],
  );

  return (
    <div className="space-y-4">
      {canWrite && (
        <div className="flex justify-end">
          <Button size="sm" onClick={() => setShowCreate(true)}>
            {t("admissions.action.createApplicant")}
          </Button>
        </div>
      )}

      <FilterBar
        fields={[
          {
            key: "application_year",
            label: t("admissions.filter.year"),
            type: "text" as const,
            placeholder: String(new Date().getFullYear()),
          },
        ]}
        values={table.filters}
        onChange={table.setFilter}
        onReset={table.resetFilters}
      />

      <DataTable
        columns={columns}
        data={rows}
        isLoading={listQuery.isLoading}
        getRowKey={(row) => String(row.id)}
        pagination={{
          page: table.page,
          pageSize: table.pageSize,
          total: listQuery.data?.total ?? 0,
        }}
        pageSizeOptions={[10, 20, 50]}
        onPageChange={table.setPage}
        onPageSizeChange={table.setPageSize}
        sort={table.sort}
        onSortChange={table.setSort}
        onRowClick={(row) => detail.open(String(row.id))}
        emptyTitle={t("admissions.empty.applicants")}
        emptyDescription={t("admissions.empty.noApplicantsYet")}
      />

      {/* Detail drawer */}
      <DrawerPanel
        open={detail.isOpen}
        onClose={detail.close}
        title={
          selectedApplicant
            ? `${selectedApplicant.first_name} ${selectedApplicant.last_name}`
            : t("admissions.drawer.applicant")
        }
        description={selectedApplicant?.email ?? ""}
        width="md"
      >
        {selectedApplicant && (
          <DetailList
            items={[
              { label: "ID", value: <code>#{selectedApplicant.id}</code> },
              {
                label: t("admissions.col.email"),
                value: selectedApplicant.email,
              },
              {
                label: t("admissions.col.program"),
                value: `P-${selectedApplicant.program_id}`,
              },
              {
                label: t("admissions.col.year"),
                value: String(selectedApplicant.application_year),
              },
              {
                label: t("admissions.col.status"),
                value: selectedApplicant.status,
              },
              {
                label: t("admissions.col.updated"),
                value: formatRelative(selectedApplicant.updated_at),
              },
              {
                label: t("admissions.col.createdBy"),
                value: selectedApplicant.created_by,
              },
            ]}
          />
        )}
      </DrawerPanel>

      {/* Create applicant drawer */}
      {canWrite && (
        <DrawerPanel
          open={showCreate}
          onClose={() => setShowCreate(false)}
          title={t("admissions.action.createApplicant")}
          description={t("admissions.createApplicant.description")}
          width="md"
        >
          <div className="space-y-4">
            {(["first_name", "last_name", "email"] as const).map((field) => (
              <div key={field} className="space-y-1.5">
                <Label>{t(`admissions.field.${field}`)}</Label>
                <Input
                  value={(form[field] as string) ?? ""}
                  onChange={(e) =>
                    setForm((prev) => ({ ...prev, [field]: e.target.value }))
                  }
                />
              </div>
            ))}
            <div className="space-y-1.5">
              <Label>{t("admissions.field.program_id")}</Label>
              <Input
                type="number"
                value={form.program_id ?? ""}
                onChange={(e) =>
                  setForm((prev) => ({
                    ...prev,
                    program_id: Number(e.target.value),
                  }))
                }
              />
            </div>
            <div className="space-y-1.5">
              <Label>{t("admissions.field.application_year")}</Label>
              <Input
                type="number"
                value={form.application_year ?? new Date().getFullYear()}
                onChange={(e) =>
                  setForm((prev) => ({
                    ...prev,
                    application_year: Number(e.target.value),
                  }))
                }
              />
            </div>
            <Button
              disabled={
                !form.email?.trim() ||
                !form.first_name?.trim() ||
                !form.last_name?.trim() ||
                !form.program_id ||
                createMutation.isPending
              }
              onClick={() => {
                if (
                  !form.email ||
                  !form.first_name ||
                  !form.last_name ||
                  !form.program_id
                )
                  return;
                createMutation.mutate(form as CreateApplicantPayload, {
                  ...getHandlers({
                    successTitle: t("admissions.action.createSuccess"),
                  }),
                  onSuccess: () => {
                    setShowCreate(false);
                    setForm({
                      status: "active",
                      application_year: new Date().getFullYear(),
                      metadata_json: {},
                    });
                  },
                });
              }}
            >
              {t("admissions.action.create")}
            </Button>
          </div>
        </DrawerPanel>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Applications tab
// ---------------------------------------------------------------------------

function ApplicationsTab({
  canWrite,
  canDecide,
}: {
  canWrite: boolean;
  canDecide: boolean;
}) {
  const { t } = useLanguage();
  const { getHandlers } = useMutationFeedback();

  const table = useTableQueryState({
    filterKeys: ["stage"] as const,
    defaultPageSize: 20,
    defaultSort: { key: "updated_at", direction: "desc" },
  });
  const detail = useDetailDrawer({ paramKey: "application" });

  const listQuery = useApplications({
    page: table.page,
    page_size: table.pageSize,
    stage: (table.filters.stage as ApplicationStage) || undefined,
  });

  const selectedId = detail.selectedId ? Number(detail.selectedId) : null;
  const appDetail = useApplication(selectedId);
  const selectedApp =
    appDetail.data ??
    listQuery.data?.items.find((r) => String(r.id) === detail.selectedId) ??
    null;

  const decisionQuery = useApplicationDecision(
    selectedApp?.stage === "decision_pending" ||
      selectedApp?.stage === "concluded"
      ? selectedId
      : null,
  );
  const documentsQuery = useApplicationDocuments(selectedId);

  const submitMutation = useSubmitApplication();
  const transitionMutation = useTransitionStage();
  const decisionMutation = useMakeDecision();

  const [toStage, setToStage] = useState<ApplicationStage>("received");
  const [transitionReason, setTransitionReason] = useState("");
  const [decisionType, setDecisionType] =
    useState<ApplicationConclusionType>("accepted");
  const [decisionRationale, setDecisionRationale] = useState("");
  const [decidedBy, setDecidedBy] = useState("");

  const rows = Array.isArray(listQuery.data?.items) ? listQuery.data.items : [];

  const columns: Column<Application>[] = useMemo(
    () => [
      {
        key: "id",
        header: "ID",
        width: "80px",
        cell: (row) => <code className="text-xs">#{row.id}</code>,
        sortValue: (row) => row.id,
      },
      {
        key: "applicant",
        header: t("admissions.col.applicant"),
        cell: (row) => (
          <span className="font-mono text-xs">A-{row.applicant_id}</span>
        ),
        sortValue: (row) => row.applicant_id,
      },
      {
        key: "program",
        header: t("admissions.col.program"),
        cell: (row) => (
          <span className="font-mono text-xs">P-{row.program_id}</span>
        ),
        sortValue: (row) => row.program_id,
      },
      {
        key: "stage",
        header: t("admissions.col.stage"),
        cell: (row) => <StageBadge stage={row.stage} />,
        sortValue: (row) => STAGE_ORDER[row.stage],
      },
      {
        key: "conclusion",
        header: t("admissions.col.conclusion"),
        cell: (row) => <ConclusionBadge type={row.conclusion_type} />,
        sortValue: (row) => row.conclusion_type ?? "",
      },
      {
        key: "updated_at",
        header: t("admissions.col.updated"),
        cell: (row) => formatRelative(row.updated_at),
        sortValue: (row) => row.updated_at,
      },
    ],
    [t],
  );

  return (
    <div className="space-y-4">
      <FilterBar
        fields={[
          {
            key: "stage",
            label: t("admissions.filter.stage"),
            type: "select" as const,
            options: STAGES.map((s) => ({
              label: t(`admissions.stage.${s}`),
              value: s,
            })),
          },
        ]}
        values={table.filters}
        onChange={table.setFilter}
        onReset={table.resetFilters}
      />

      <DataTable
        columns={columns}
        data={rows}
        isLoading={listQuery.isLoading}
        getRowKey={(row) => String(row.id)}
        pagination={{
          page: table.page,
          pageSize: table.pageSize,
          total: listQuery.data?.total ?? 0,
        }}
        pageSizeOptions={[10, 20, 50]}
        onPageChange={table.setPage}
        onPageSizeChange={table.setPageSize}
        sort={table.sort}
        onSortChange={table.setSort}
        onRowClick={(row) => detail.open(String(row.id))}
        emptyTitle={t("admissions.empty.applications")}
        emptyDescription={t("admissions.empty.noApplicationsYet")}
      />

      <DrawerPanel
        open={detail.isOpen}
        onClose={detail.close}
        title={
          selectedApp
            ? `${t("admissions.drawer.application")} #${selectedApp.id}`
            : t("admissions.drawer.application")
        }
        description={
          selectedApp ? t(`admissions.stage.${selectedApp.stage}`) : ""
        }
        width="lg"
      >
        {detail.isOpen && appDetail.isLoading ? (
          <p className="text-sm text-muted-foreground">
            {t("admissions.drawer.loading")}
          </p>
        ) : selectedApp ? (
          <div className="space-y-6">
            {/* Stage progress */}
            <div className="space-y-2">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                {t("admissions.field.stageProgress")}
              </p>
              <StageProgress current={selectedApp.stage} />
            </div>

            <DetailList
              items={[
                {
                  label: t("admissions.col.applicant"),
                  value: (
                    <span className="font-mono">
                      A-{selectedApp.applicant_id}
                    </span>
                  ),
                },
                {
                  label: t("admissions.col.program"),
                  value: (
                    <span className="font-mono">
                      P-{selectedApp.program_id}
                    </span>
                  ),
                },
                {
                  label: t("admissions.col.stage"),
                  value: <StageBadge stage={selectedApp.stage} />,
                },
                {
                  label: t("admissions.col.conclusion"),
                  value: <ConclusionBadge type={selectedApp.conclusion_type} />,
                },
                {
                  label: t("admissions.field.version"),
                  value: String(selectedApp.version),
                },
                {
                  label: t("admissions.col.updated"),
                  value: formatRelative(selectedApp.updated_at),
                },
              ]}
            />

            {/* Submit (new → received) */}
            {canWrite && selectedApp.stage === "new" && (
              <div className="rounded border p-4 space-y-3">
                <p className="text-sm font-medium">
                  {t("admissions.action.submit")}
                </p>
                <Button
                  size="sm"
                  disabled={submitMutation.isPending}
                  onClick={() =>
                    submitMutation.mutate(
                      {
                        id: selectedApp.id,
                        expectedVersion: selectedApp.version,
                      },
                      getHandlers({
                        successTitle: t("admissions.action.submitSuccess"),
                      }),
                    )
                  }
                >
                  {t("admissions.action.submit")}
                </Button>
              </div>
            )}

            {/* Stage transition */}
            {canWrite &&
              selectedApp.stage !== "concluded" &&
              selectedApp.stage !== "new" && (
                <div className="rounded border p-4 space-y-3">
                  <p className="text-sm font-medium">
                    {t("admissions.action.transition")}
                  </p>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label>{t("admissions.field.toStage")}</Label>
                      <Select
                        value={toStage}
                        onValueChange={(v) => setToStage(v as ApplicationStage)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {STAGES.filter(
                            (s) =>
                              STAGE_ORDER[s] > STAGE_ORDER[selectedApp.stage],
                          ).map((s) => (
                            <SelectItem key={s} value={s}>
                              {t(`admissions.stage.${s}`)}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1.5">
                      <Label>{t("admissions.field.reason")}</Label>
                      <Input
                        value={transitionReason}
                        onChange={(e) => setTransitionReason(e.target.value)}
                        placeholder={t("admissions.field.reasonPlaceholder")}
                      />
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={transitionMutation.isPending}
                    onClick={() =>
                      transitionMutation.mutate(
                        {
                          id: selectedApp.id,
                          data: {
                            to_stage: toStage,
                            reason: transitionReason || undefined,
                          },
                        },
                        getHandlers({
                          successTitle: t(
                            "admissions.action.transitionSuccess",
                          ),
                        }),
                      )
                    }
                  >
                    {t("admissions.action.transition")}
                  </Button>
                </div>
              )}

            {/* Decision */}
            {canDecide &&
              selectedApp.stage === "decision_pending" &&
              !decisionQuery.data && (
                <div className="rounded border p-4 space-y-3">
                  <p className="text-sm font-medium">
                    {t("admissions.action.decide")}
                  </p>
                  <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                    <div className="space-y-1.5">
                      <Label>{t("admissions.field.decisionType")}</Label>
                      <Select
                        value={decisionType}
                        onValueChange={(v) =>
                          setDecisionType(v as ApplicationConclusionType)
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {(
                            [
                              "accepted",
                              "rejected",
                              "waitlist",
                              "withdrawn",
                            ] as const
                          ).map((v) => (
                            <SelectItem key={v} value={v}>
                              {t(`admissions.conclusion.${v}`)}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1.5 md:col-span-2">
                      <Label>{t("admissions.field.decisionRationale")}</Label>
                      <Input
                        value={decisionRationale}
                        onChange={(e) => setDecisionRationale(e.target.value)}
                      />
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <Label>{t("admissions.field.decidedBy")}</Label>
                    <Input
                      value={decidedBy}
                      onChange={(e) => setDecidedBy(e.target.value)}
                      placeholder="registrar@example.com"
                    />
                  </div>
                  <Button
                    size="sm"
                    disabled={!decidedBy.trim() || decisionMutation.isPending}
                    onClick={() =>
                      decisionMutation.mutate(
                        {
                          id: selectedApp.id,
                          data: {
                            decision_type: decisionType,
                            decision_rationale: decisionRationale || undefined,
                            decided_by: decidedBy.trim(),
                            application_version: selectedApp.version,
                          },
                        },
                        getHandlers({
                          successTitle: t("admissions.action.decideSuccess"),
                        }),
                      )
                    }
                  >
                    {t("admissions.action.decide")}
                  </Button>
                </div>
              )}

            {/* Existing decision */}
            {decisionQuery.data && (
              <div className="rounded border bg-muted/30 p-4 space-y-2">
                <p className="text-sm font-medium">
                  {t("admissions.field.decision")}
                </p>
                <DetailList
                  items={[
                    {
                      label: t("admissions.col.conclusion"),
                      value: (
                        <ConclusionBadge
                          type={decisionQuery.data.decision_type}
                        />
                      ),
                    },
                    {
                      label: t("admissions.field.decisionRationale"),
                      value: decisionQuery.data.decision_rationale ?? "—",
                    },
                    {
                      label: t("admissions.field.decidedBy"),
                      value: decisionQuery.data.decided_by_id,
                    },
                    {
                      label: t("admissions.col.updated"),
                      value: formatRelative(decisionQuery.data.decided_at),
                    },
                  ]}
                />
              </div>
            )}

            <div className="rounded border p-4 space-y-3">
              <p className="text-sm font-medium">
                {t("admissions.field.documents")}
              </p>
              {documentsQuery.isLoading ? (
                <p className="text-sm text-muted-foreground">
                  {t("admissions.doc.loading")}
                </p>
              ) : documentsQuery.data?.items?.length ? (
                <div className="space-y-2">
                  {documentsQuery.data.items.map((doc) => (
                    <div
                      key={doc.id}
                      className="rounded border bg-muted/20 px-3 py-2 text-sm"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-1">
                          <p className="font-medium">{doc.file_name}</p>
                          <p className="text-xs text-muted-foreground">
                            {doc.document_type}
                            {doc.mime_type ? ` • ${doc.mime_type}` : ""}
                            {doc.file_size_bytes
                              ? ` • ${doc.file_size_bytes} B`
                              : ""}
                          </p>
                        </div>
                        <DocumentStatusBadge status={doc.status} />
                      </div>
                      <div className="mt-1 text-xs text-muted-foreground">
                        {t("admissions.col.updated")}:{" "}
                        {formatRelative(doc.created_at)}
                        {doc.verified_at
                          ? ` • ${t("admissions.doc.verifiedAt")}: ${formatRelative(doc.verified_at)}`
                          : ""}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  {t("admissions.doc.empty")}
                </p>
              )}
            </div>
          </div>
        ) : (
          <ErrorState title={t("admissions.drawer.notFound")} />
        )}
      </DrawerPanel>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

type AdmissionsTab = "applicants" | "applications";

export default function AdmissionsPage() {
  const { t } = useLanguage();
  const { hasPermission } = usePermissions();
  const [activeTab, setActiveTab] = useState<AdmissionsTab>("applicants");
  const canRead = hasPermission(PERMISSIONS.ADMISSIONS_READ);
  const canWrite = hasPermission(PERMISSIONS.ADMISSIONS_WRITE);
  const canDecide = hasPermission(PERMISSIONS.ADMISSIONS_DECIDE);

  if (!canRead) {
    return <AccessDenied />;
  }

  return (
    <div className="space-y-4">
      <PageHeader
        title={t("nav.admissions")}
        description={t("console.admissions.description")}
        icon={GraduationCap}
      />

      {/* Tab switcher */}
      <div className="flex gap-2 border-b pb-0">
        {(["applicants", "applications"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors",
              activeTab === tab
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            {t(`admissions.tab.${tab}`)}
          </button>
        ))}
      </div>

      {activeTab === "applicants" ? (
        <ApplicantsTab canWrite={canWrite} />
      ) : (
        <ApplicationsTab canWrite={canWrite} canDecide={canDecide} />
      )}
    </div>
  );
}
