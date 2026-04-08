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
import { PermissionGate } from "@/shared/ui/permission-gate";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import { useDetailDrawer } from "@/shared/hooks/use-detail-drawer";
import { useTableQueryState } from "@/shared/hooks/use-table-query-state";
import {
  useLocalUsers,
  useCreateLocalUser,
  useUpdateLocalUser,
  useDeleteLocalUser,
  useSetLocalUserPassword,
} from "@/modules/local-users/hooks";
import { LocalUser } from "@/modules/local-users/types";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useLanguage } from "@/app/components/LanguageProvider";
import { Users } from "lucide-react";

const FILTER_FIELDS = [
  { key: "search", label: "Search", type: "text" as const, placeholder: "Login or name…" },
  { key: "role", label: "Role", type: "text" as const, placeholder: "Filter by role…" },
];

export default function LocalUsersPage() {
  const { t } = useLanguage();
  const tAny = (key: string) => t(key as never);
  const table = useTableQueryState({ filterKeys: ["search", "role"] as const });
  const detail = useDetailDrawer({ paramKey: "user" });
  const { getHandlers } = useMutationFeedback();

  const [createOpen, setCreateOpen] = useState(false);
  const [newLogin, setNewLogin] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newDisplayName, setNewDisplayName] = useState("");
  const [newRoles, setNewRoles] = useState("student");
  const [newLanguage, setNewLanguage] = useState("ru");

  const [editDisplayName, setEditDisplayName] = useState("");
  const [editRoles, setEditRoles] = useState("");
  const [editLanguage, setEditLanguage] = useState("");
  const [newUserPassword, setNewUserPassword] = useState("");
  const [pwOpen, setPwOpen] = useState(false);

  const { data, isLoading, error, refetch } = useLocalUsers({
    search: table.filters.search,
    role: table.filters.role,
  });

  const createUser = useCreateLocalUser();
  const deleteUser = useDeleteLocalUser();

  const selectedUser =
    data?.users.find((u) => u.user_id === detail.selectedId) ?? null;
  const updateUser = useUpdateLocalUser(selectedUser?.user_id ?? "");
  const setPassword = useSetLocalUserPassword(selectedUser?.user_id ?? "");

  const canCreate =
    newLogin.trim().length >= 3 &&
    newPassword.trim().length >= 6 &&
    newDisplayName.trim().length > 0;

  if (error) {
    return <ErrorState title="Failed to load local users" onRetry={refetch} />;
  }

  const columns: Column<LocalUser>[] = [
    {
      key: "login",
      header: "Login",
      cell: (r) => <code className="text-xs">{r.login}</code>,
      sortValue: (r) => r.login,
    },
    {
      key: "display_name",
      header: tAny("localEditDisplayName"),
      cell: (r) => r.display_name,
      sortValue: (r) => r.display_name.toLowerCase(),
    },
    {
      key: "roles",
      header: tAny("roles"),
      cell: (r) => r.roles.join(", "),
      sortValue: (r) => r.roles.join(","),
    },
    {
      key: "language",
      header: "Language",
      cell: (r) => r.default_language,
      sortValue: (r) => r.default_language,
    },
    {
      key: "actions",
      header: "",
      width: "80px",
      cell: (r) => (
        <PermissionGate permission={PERMISSIONS.LOCAL_USERS_MANAGE}>
          <Button
            variant="ghost"
            size="sm"
            onClick={(event) => {
              event.stopPropagation();
              setEditDisplayName(r.display_name);
              setEditRoles(r.roles.join(","));
              setEditLanguage(r.default_language);
              detail.open(r.user_id);
            }}
          >
            Edit
          </Button>
        </PermissionGate>
      ),
    },
  ];

  return (
    <div className="space-y-4" data-testid="local-users-page">
      <PageHeader
        title={t("nav.localUsers")}
        description={tAny("localUsersHelp")}
        icon={Users}
        actions={
          <PermissionGate permission={PERMISSIONS.LOCAL_USERS_MANAGE}>
            <Button size="sm" onClick={() => setCreateOpen(true)}>
              {tAny("addLocalUser")}
            </Button>
          </PermissionGate>
        }
      />

      <FilterBar
        fields={FILTER_FIELDS}
        values={table.filters}
        onChange={table.setFilter}
        onReset={table.resetFilters}
      />

      <DataTable
        columns={columns}
        data={data?.users ?? []}
        isLoading={isLoading}
        getRowKey={(r) => r.user_id}
        onRowClick={(row) => {
          setEditDisplayName(row.display_name);
          setEditRoles(row.roles.join(","));
          setEditLanguage(row.default_language);
          detail.open(row.user_id);
        }}
        emptyTitle={tAny("noLocalUsers")}
      />

      {/* Edit drawer */}
      <DrawerPanel
        open={detail.isOpen}
        onClose={detail.close}
        title={selectedUser ? selectedUser.display_name : "Edit user"}
        description={selectedUser?.login ?? ""}
      >
        {selectedUser ? (
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="edit-display-name">{tAny("localEditDisplayName")}</Label>
              <Input
                id="edit-display-name"
                value={editDisplayName}
                onChange={(e) => setEditDisplayName(e.target.value)}
                placeholder={tAny("displayNamePlaceholder")}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="edit-roles">{tAny("roles")}</Label>
              <Input
                id="edit-roles"
                value={editRoles}
                onChange={(e) => setEditRoles(e.target.value)}
                placeholder={tAny("rolesPlaceholder")}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="edit-language">Language</Label>
              <Input
                id="edit-language"
                value={editLanguage}
                onChange={(e) => setEditLanguage(e.target.value)}
                placeholder="ru"
              />
            </div>
            <PermissionGate permission={PERMISSIONS.LOCAL_USERS_MANAGE}>
              <div className="flex gap-2">
                <Button
                  disabled={!editDisplayName.trim() || updateUser.isPending}
                  onClick={() =>
                    updateUser.mutate(
                      {
                        display_name: editDisplayName.trim(),
                        roles: editRoles
                          .split(",")
                          .map((r) => r.trim())
                          .filter(Boolean),
                        language: editLanguage.trim() || undefined,
                      },
                      {
                        ...getHandlers({ successTitle: tAny("localUserUpdated") }),
                        onSuccess: () => {
                          getHandlers({ successTitle: tAny("localUserUpdated") }).onSuccess(undefined);
                          detail.close();
                        },
                      },
                    )
                  }
                >
                  Save
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setNewUserPassword("");
                    setPwOpen(true);
                  }}
                >
                  {tAny("localPasswordAction")}
                </Button>
                <Button
                  variant="destructive"
                  disabled={deleteUser.isPending}
                  onClick={() =>
                    deleteUser.mutate(selectedUser.user_id, {
                      ...getHandlers({ successTitle: tAny("localUserDeleted") }),
                      onSuccess: () => {
                        getHandlers({ successTitle: tAny("localUserDeleted") }).onSuccess(undefined);
                        detail.close();
                      },
                    })
                  }
                >
                  {tAny("localDelete")}
                </Button>
              </div>
            </PermissionGate>
          </div>
        ) : (
          <ErrorState title="User not found" />
        )}
      </DrawerPanel>

      {/* Set password drawer */}
      <DrawerPanel
        open={pwOpen}
        onClose={() => setPwOpen(false)}
        title={tAny("localPasswordAction")}
        description={selectedUser?.login ?? ""}
      >
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="new-user-password">New password</Label>
            <Input
              id="new-user-password"
              type="password"
              value={newUserPassword}
              onChange={(e) => setNewUserPassword(e.target.value)}
              placeholder="Min 6 characters"
            />
          </div>
          <PermissionGate permission={PERMISSIONS.LOCAL_USERS_MANAGE}>
            <Button
              disabled={newUserPassword.length < 6 || setPassword.isPending}
              onClick={() =>
                setPassword.mutate(
                  { password: newUserPassword },
                  {
                    ...getHandlers({ successTitle: tAny("localPasswordUpdated") }),
                    onSuccess: () => {
                      getHandlers({ successTitle: tAny("localPasswordUpdated") }).onSuccess(undefined);
                      setPwOpen(false);
                    },
                  },
                )
              }
            >
              {tAny("localPasswordAction")}
            </Button>
          </PermissionGate>
        </div>
      </DrawerPanel>

      {/* Create drawer */}
      <DrawerPanel
        open={createOpen}
        onClose={() => {
          setCreateOpen(false);
          setNewLogin("");
          setNewPassword("");
          setNewDisplayName("");
          setNewRoles("student");
          setNewLanguage("ru");
        }}
        title={tAny("addLocalUser")}
        description={tAny("localUsersHelp")}
      >
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="new-login">Login</Label>
            <Input
              id="new-login"
              value={newLogin}
              onChange={(e) => setNewLogin(e.target.value)}
              placeholder={tAny("loginPlaceholder")}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="new-password">Password</Label>
            <Input
              id="new-password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Min 6 characters"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="new-display-name">{tAny("localEditDisplayName")}</Label>
            <Input
              id="new-display-name"
              value={newDisplayName}
              onChange={(e) => setNewDisplayName(e.target.value)}
              placeholder={tAny("displayNamePlaceholder")}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="new-roles">{tAny("roles")}</Label>
            <Input
              id="new-roles"
              value={newRoles}
              onChange={(e) => setNewRoles(e.target.value)}
              placeholder={tAny("rolesPlaceholder")}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="new-language">Language</Label>
            <Input
              id="new-language"
              value={newLanguage}
              onChange={(e) => setNewLanguage(e.target.value)}
              placeholder="ru"
            />
          </div>
          <PermissionGate permission={PERMISSIONS.LOCAL_USERS_MANAGE}>
            <Button
              disabled={!canCreate || createUser.isPending}
              onClick={() =>
                createUser.mutate(
                  {
                    login: newLogin.trim(),
                    password: newPassword,
                    display_name: newDisplayName.trim(),
                    roles: newRoles
                      .split(",")
                      .map((r) => r.trim())
                      .filter(Boolean),
                    default_language: newLanguage.trim() || "ru",
                  },
                  {
                    ...getHandlers({ successTitle: tAny("localUserCreated") }),
                    onSuccess: () => {
                      getHandlers({ successTitle: tAny("localUserCreated") }).onSuccess(undefined);
                      setCreateOpen(false);
                      setNewLogin("");
                      setNewPassword("");
                      setNewDisplayName("");
                      setNewRoles("student");
                      setNewLanguage("ru");
                    },
                  },
                )
              }
            >
              {tAny("addLocalUser")}
            </Button>
          </PermissionGate>
        </div>
      </DrawerPanel>
    </div>
  );
}
