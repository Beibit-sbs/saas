"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/shared/ui/page-header";
import { DataTable, Column } from "@/shared/ui/data-table";
import { ErrorState } from "@/shared/ui/error-state";
import { Button } from "@/shared/ui/button";
import { DrawerPanel } from "@/shared/ui/drawer-panel";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { PermissionGate } from "@/shared/ui/permission-gate";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useDetailDrawer } from "@/shared/hooks/use-detail-drawer";
import {
  useOrgUnits,
  useCreateOrgUnit,
  useUpdateOrgUnit,
  useDeactivateOrgUnit,
} from "@/modules/org-units/hooks";
import { OrgUnit, OrgUnitType } from "@/modules/org-units/types";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useLanguage } from "@/app/components/LanguageProvider";
import { Building2 } from "lucide-react";

const ORG_UNIT_TYPES: OrgUnitType[] = [
  "university",
  "school",
  "faculty",
  "department",
  "umo",
  "registrar_office",
  "deans_office",
  "advisory_unit",
  "academic_committee",
  "academic_commission",
];

export default function OrgUnitsPage() {
  const { t } = useLanguage();
  const tAny = (key: string) => t(key as never);
  const detail = useDetailDrawer({ paramKey: "unit" });
  const { getHandlers } = useMutationFeedback();

  const [createOpen, setCreateOpen] = useState(false);
  const [newName, setNewName] = useState("");
  const [newCode, setNewCode] = useState("");
  const [newType, setNewType] = useState<OrgUnitType>("department");
  const [newParentId, setNewParentId] = useState("");

  const [editName, setEditName] = useState("");
  const [editCode, setEditCode] = useState("");
  const [editType, setEditType] = useState<OrgUnitType>("department");
  const [editParentId, setEditParentId] = useState("");

  const { data, isLoading, error, refetch } = useOrgUnits({ active_only: false });
  const createUnit = useCreateOrgUnit();
  const deactivateUnit = useDeactivateOrgUnit();

  const selectedUnit =
    data?.find((u) => u.id === Number(detail.selectedId)) ?? null;
  const updateUnit = useUpdateOrgUnit(selectedUnit?.id ?? 0);

  useEffect(() => {
    if (selectedUnit) {
      setEditName(selectedUnit.name);
      setEditCode(selectedUnit.code);
      setEditType(selectedUnit.unit_type);
      setEditParentId(selectedUnit.parent_unit_id?.toString() ?? "");
    }
  }, [selectedUnit]);

  const canCreate = newName.trim().length > 0 && newCode.trim().length > 0;

  if (error) {
    return <ErrorState title="Failed to load org units" onRetry={refetch} />;
  }

  const columns: Column<OrgUnit>[] = [
    {
      key: "name",
      header: tAny("orgUnitName"),
      cell: (r) => <span className="font-medium">{r.name}</span>,
      sortValue: (r) => r.name.toLowerCase(),
    },
    {
      key: "code",
      header: tAny("orgUnitCode"),
      cell: (r) => <code className="text-xs">{r.code}</code>,
      sortValue: (r) => r.code,
    },
    {
      key: "unit_type",
      header: tAny("orgUnitType"),
      cell: (r) => r.unit_type.replace(/_/g, " "),
      sortValue: (r) => r.unit_type,
    },
    {
      key: "active",
      header: tAny("orgUnitActive"),
      cell: (r) => (
        <span className={r.active ? "text-green-600" : "text-muted-foreground"}>
          {r.active ? "Yes" : "No"}
        </span>
      ),
      sortValue: (r) => (r.active ? 1 : 0),
    },
    {
      key: "actions",
      header: "",
      width: "80px",
      cell: (r) => (
        <PermissionGate permission={PERMISSIONS.ORG_UNITS_WRITE}>
          <Button
            variant="ghost"
            size="sm"
            onClick={(event) => {
              event.stopPropagation();
              detail.open(String(r.id));
            }}
          >
            Edit
          </Button>
        </PermissionGate>
      ),
    },
  ];

  return (
    <div className="space-y-4" data-testid="org-units-page">
      <PageHeader
        title={t("nav.orgUnits")}
        description={tAny("orgUnitsHelp")}
        icon={Building2}
        actions={
          <PermissionGate permission={PERMISSIONS.ORG_UNITS_WRITE}>
            <Button size="sm" onClick={() => setCreateOpen(true)}>
              {tAny("addOrgUnit")}
            </Button>
          </PermissionGate>
        }
      />

      <DataTable
        columns={columns}
        data={data ?? []}
        isLoading={isLoading}
        getRowKey={(r) => String(r.id)}
        onRowClick={(row) => detail.open(String(row.id))}
        emptyTitle={tAny("noOrgUnits")}
      />

      {/* Edit drawer */}
      <DrawerPanel
        open={detail.isOpen}
        onClose={detail.close}
        title={selectedUnit ? selectedUnit.name : "Edit unit"}
        description={selectedUnit?.code ?? ""}
      >
        {selectedUnit ? (
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="edit-name">{tAny("orgUnitName")}</Label>
              <Input
                id="edit-name"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="edit-code">{tAny("orgUnitCode")}</Label>
              <Input
                id="edit-code"
                value={editCode}
                onChange={(e) => setEditCode(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="edit-type">{tAny("orgUnitType")}</Label>
              <select
                id="edit-type"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={editType}
                onChange={(e) => setEditType(e.target.value as OrgUnitType)}
              >
                {ORG_UNIT_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t.replace(/_/g, " ")}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="edit-parent">{tAny("orgUnitParent")}</Label>
              <Input
                id="edit-parent"
                value={editParentId}
                onChange={(e) => setEditParentId(e.target.value)}
                placeholder="Leave blank for root"
              />
            </div>
            <PermissionGate permission={PERMISSIONS.ORG_UNITS_WRITE}>
              <div className="flex gap-2">
                <Button
                  disabled={!editName.trim() || updateUnit.isPending}
                  onClick={() =>
                    updateUnit.mutate(
                      {
                        name: editName.trim(),
                        code: editCode.trim(),
                        unit_type: editType,
                        parent_unit_id: editParentId
                          ? Number(editParentId)
                          : null,
                      },
                      {
                        ...getHandlers({ successTitle: tAny("orgUnitUpdated") }),
                        onSuccess: () => {
                          getHandlers({
                            successTitle: tAny("orgUnitUpdated"),
                          }).onSuccess(undefined);
                          detail.close();
                        },
                      },
                    )
                  }
                >
                  Save
                </Button>
                {selectedUnit.active && (
                  <Button
                    variant="destructive"
                    disabled={deactivateUnit.isPending}
                    onClick={() =>
                      deactivateUnit.mutate(selectedUnit.id, {
                        ...getHandlers({
                          successTitle: tAny("orgUnitDeactivated"),
                        }),
                        onSuccess: () => {
                          getHandlers({
                            successTitle: tAny("orgUnitDeactivated"),
                          }).onSuccess(undefined);
                          detail.close();
                        },
                      })
                    }
                  >
                    Deactivate
                  </Button>
                )}
              </div>
            </PermissionGate>
          </div>
        ) : (
          <ErrorState title="Unit not found" />
        )}
      </DrawerPanel>

      {/* Create drawer */}
      <DrawerPanel
        open={createOpen}
        onClose={() => {
          setCreateOpen(false);
          setNewName("");
          setNewCode("");
          setNewType("department");
          setNewParentId("");
        }}
        title={tAny("addOrgUnit")}
        description={tAny("orgUnitsHelp")}
      >
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="new-name">{tAny("orgUnitName")}</Label>
            <Input
              id="new-name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Faculty of Engineering"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="new-code">{tAny("orgUnitCode")}</Label>
            <Input
              id="new-code"
              value={newCode}
              onChange={(e) => setNewCode(e.target.value)}
              placeholder="ENG"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="new-type">{tAny("orgUnitType")}</Label>
            <select
              id="new-type"
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={newType}
              onChange={(e) => setNewType(e.target.value as OrgUnitType)}
            >
              {ORG_UNIT_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="new-parent">{tAny("orgUnitParent")}</Label>
            <Input
              id="new-parent"
              value={newParentId}
              onChange={(e) => setNewParentId(e.target.value)}
              placeholder="Leave blank for root"
            />
          </div>
          <PermissionGate permission={PERMISSIONS.ORG_UNITS_WRITE}>
            <Button
              disabled={!canCreate || createUnit.isPending}
              onClick={() =>
                createUnit.mutate(
                  {
                    name: newName.trim(),
                    code: newCode.trim(),
                    unit_type: newType,
                    parent_unit_id: newParentId ? Number(newParentId) : null,
                  },
                  {
                    ...getHandlers({ successTitle: tAny("orgUnitCreated") }),
                    onSuccess: () => {
                      getHandlers({
                        successTitle: tAny("orgUnitCreated"),
                      }).onSuccess(undefined);
                      setCreateOpen(false);
                      setNewName("");
                      setNewCode("");
                      setNewType("department");
                      setNewParentId("");
                    },
                  },
                )
              }
            >
              {tAny("addOrgUnit")}
            </Button>
          </PermissionGate>
        </div>
      </DrawerPanel>
    </div>
  );
}
