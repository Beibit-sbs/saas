"use client";

import { useState } from "react";
import { PageHeader } from "@/shared/ui/page-header";
import { DataTable, Column } from "@/shared/ui/data-table";
import { FilterBar } from "@/shared/ui/filter-bar";
import { ErrorState } from "@/shared/ui/error-state";
import { Button } from "@/shared/ui/button";
import { DrawerPanel } from "@/shared/ui/drawer-panel";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { PermissionGate, RequirePermission } from "@/shared/ui/permission-gate";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useTableQueryState } from "@/shared/hooks/use-table-query-state";
import {
  useRbacRoles,
  useRbacAssignments,
  useUpsertRole,
  useAssignRole,
  useRevokeAssignment,
} from "@/modules/rbac/hooks";
import { RoleAssignment } from "@/modules/rbac/types";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useLanguage } from "@/app/components/LanguageProvider";
import { ShieldCheck } from "lucide-react";

const ASSIGNMENT_FILTER_FIELDS = [
  {
    key: "user_id",
    label: "User ID",
    type: "text" as const,
    placeholder: "Filter by user ID…",
  },
  {
    key: "role",
    label: "Role",
    type: "text" as const,
    placeholder: "Filter by role…",
  },
];

export default function RbacPage() {
  const { t } = useLanguage();
  const tAny = (key: string) => t(key as never);
  const { getHandlers } = useMutationFeedback();

  // Role upsert state
  const [roleOpen, setRoleOpen] = useState(false);
  const [roleName, setRoleName] = useState("");
  const [rolePerms, setRolePerms] = useState("");

  // Assign state
  const [assignOpen, setAssignOpen] = useState(false);
  const [assignUserId, setAssignUserId] = useState("");
  const [assignRole, setAssignRole] = useState("");

  // Assignments filter
  const table = useTableQueryState({
    filterKeys: ["user_id", "role"] as const,
  });

  const rolesResult = useRbacRoles();
  const assignmentsResult = useRbacAssignments({
    user_id: table.filters.user_id,
    role: table.filters.role,
  });

  const upsertRole = useUpsertRole();
  const assignRoleMutation = useAssignRole();
  const revokeAssignment = useRevokeAssignment();

  const rolesMap = rolesResult.data?.roles ?? {};
  const roleRows = Object.entries(rolesMap).map(([name, perms]) => ({
    name,
    perms,
  }));

  const assignmentColumns: Column<RoleAssignment>[] = [
    {
      key: "user_id",
      header: tAny("userId"),
      cell: (r) => <code className="text-xs">{r.user_id}</code>,
      sortValue: (r) => r.user_id,
    },
    {
      key: "role",
      header: tAny("rbacRole"),
      cell: (r) => r.role,
      sortValue: (r) => r.role,
    },
    {
      key: "actions",
      header: "",
      width: "90px",
      cell: (r) => (
        <PermissionGate permission={PERMISSIONS.ROLES_MANAGE}>
          <Button
            variant="ghost"
            size="sm"
            onClick={(event) => {
              event.stopPropagation();
              revokeAssignment.mutate(
                { userId: r.user_id, role: r.role },
                getHandlers({ successTitle: tAny("rbacRevoked") }),
              );
            }}
          >
            {tAny("rbacRevoke")}
          </Button>
        </PermissionGate>
      ),
    },
  ];

  if (rolesResult.error && assignmentsResult.error) {
    return (
      <ErrorState
        title="Failed to load RBAC data"
        onRetry={() => {
          rolesResult.refetch();
          assignmentsResult.refetch();
        }}
      />
    );
  }

  return (
    <RequirePermission permission={PERMISSIONS.ROLES_MANAGE}>
    <div className="space-y-6" data-testid="rbac-page">
      <PageHeader
        title={t("nav.rbac")}
        description={tAny("rbacRolesTitle")}
        icon={ShieldCheck}
        actions={
          <PermissionGate permission={PERMISSIONS.ROLES_MANAGE}>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setRoleName("");
                  setRolePerms("");
                  setRoleOpen(true);
                }}
              >
                {tAny("rbacSaveRole")}
              </Button>
              <Button
                size="sm"
                onClick={() => {
                  setAssignUserId("");
                  setAssignRole("");
                  setAssignOpen(true);
                }}
              >
                {tAny("rbacAssign")}
              </Button>
            </div>
          </PermissionGate>
        }
      />

      {/* Roles table */}
      <section className="space-y-2">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          {tAny("rbacRolesTitle")}
        </h2>
        <DataTable
          columns={[
            {
              key: "name",
              header: tAny("rbacRoleName"),
              cell: (r: { name: string; perms: string[] }) => (
                <span className="font-medium">{r.name}</span>
              ),
              sortValue: (r: { name: string; perms: string[] }) => r.name,
            },
            {
              key: "perms",
              header: tAny("rbacPerms"),
              cell: (r: { name: string; perms: string[] }) => (
                <span className="text-xs text-muted-foreground">
                  {r.perms.join(", ") || "—"}
                </span>
              ),
              sortValue: (r: { name: string; perms: string[] }) =>
                r.perms.join(","),
            },
            {
              key: "edit",
              header: "",
              width: "80px",
              cell: (r: { name: string; perms: string[] }) => (
                <PermissionGate permission={PERMISSIONS.ROLES_MANAGE}>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(event) => {
                      event.stopPropagation();
                      setRoleName(r.name);
                      setRolePerms(r.perms.join(","));
                      setRoleOpen(true);
                    }}
                  >
                    Edit
                  </Button>
                </PermissionGate>
              ),
            },
          ]}
          data={roleRows}
          isLoading={rolesResult.isLoading}
          getRowKey={(r) => r.name}
          emptyTitle={tAny("rbacNoRoles")}
        />
      </section>

      {/* Assignments table */}
      <section className="space-y-2">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          {tAny("rbacAssignTitle")}
        </h2>
        <FilterBar
          fields={ASSIGNMENT_FILTER_FIELDS}
          values={table.filters}
          onChange={table.setFilter}
          onReset={table.resetFilters}
        />
        <DataTable
          columns={assignmentColumns}
          data={assignmentsResult.data?.assignments ?? []}
          isLoading={assignmentsResult.isLoading}
          getRowKey={(r) => `${r.user_id}:${r.role}`}
          emptyTitle={tAny("rbacNoAssignments")}
        />
      </section>

      {/* Upsert role drawer */}
      <DrawerPanel
        open={roleOpen}
        onClose={() => setRoleOpen(false)}
        title={tAny("rbacSaveRole")}
        description={tAny("rbacRolesHelp")}
      >
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="role-name">{tAny("rbacRoleName")}</Label>
            <Input
              id="role-name"
              value={roleName}
              onChange={(e) => setRoleName(e.target.value)}
              placeholder="registrar"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="role-perms">{tAny("rbacPerms")}</Label>
            <Input
              id="role-perms"
              value={rolePerms}
              onChange={(e) => setRolePerms(e.target.value)}
              placeholder={tAny("rbacPermissions")}
            />
          </div>
          <PermissionGate permission={PERMISSIONS.ROLES_MANAGE}>
            <Button
              disabled={roleName.trim().length < 2 || upsertRole.isPending}
              onClick={() =>
                upsertRole.mutate(
                  {
                    name: roleName.trim(),
                    permissions: rolePerms
                      .split(",")
                      .map((p) => p.trim())
                      .filter(Boolean),
                  },
                  {
                    ...getHandlers({ successTitle: tAny("rbacRoleSaved") }),
                    onSuccess: () => {
                      getHandlers({ successTitle: tAny("rbacRoleSaved") }).onSuccess(undefined);
                      setRoleOpen(false);
                    },
                  },
                )
              }
            >
              {tAny("rbacSaveRole")}
            </Button>
          </PermissionGate>
        </div>
      </DrawerPanel>

      {/* Assign role drawer */}
      <DrawerPanel
        open={assignOpen}
        onClose={() => setAssignOpen(false)}
        title={tAny("rbacAssignTitle")}
        description={tAny("rbacAssignHelp")}
      >
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="assign-user-id">{tAny("userId")}</Label>
            <Input
              id="assign-user-id"
              value={assignUserId}
              onChange={(e) => setAssignUserId(e.target.value)}
              placeholder="user-uuid"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="assign-role">{tAny("rbacRole")}</Label>
            <Input
              id="assign-role"
              value={assignRole}
              onChange={(e) => setAssignRole(e.target.value)}
              placeholder="registrar"
            />
          </div>
          <PermissionGate permission={PERMISSIONS.ROLES_MANAGE}>
            <Button
              disabled={
                !assignUserId.trim() ||
                assignRole.trim().length < 2 ||
                assignRoleMutation.isPending
              }
              onClick={() =>
                assignRoleMutation.mutate(
                  { user_id: assignUserId.trim(), role: assignRole.trim() },
                  {
                    ...getHandlers({ successTitle: tAny("rbacAssigned") }),
                    onSuccess: () => {
                      getHandlers({ successTitle: tAny("rbacAssigned") }).onSuccess(undefined);
                      setAssignOpen(false);
                    },
                  },
                )
              }
            >
              {tAny("rbacAssign")}
            </Button>
          </PermissionGate>
        </div>
      </DrawerPanel>
    </div>
    </RequirePermission>
  );
}
