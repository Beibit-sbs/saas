"use client";

import { useState } from "react";
import { ContactRound, Plus } from "lucide-react";
import { useLanguage } from "@/app/components/LanguageProvider";
import { AccessDenied, PermissionGate } from "@/shared/ui/permission-gate";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { PERMISSIONS } from "@/shared/config/permissions";
import { PageHeader } from "@/shared/ui/page-header";
import { ErrorState } from "@/shared/ui/error-state";
import { DataTable, type Column } from "@/shared/ui/data-table";
import { Label } from "@/shared/ui/label";
import { Input } from "@/shared/ui/input";
import { Button } from "@/shared/ui/button";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import {
  useCreateProfilePerson,
  useProfileDepartments,
  useProfilePeople,
} from "@/modules/profiles-admin/hooks";
import type {
  ProfileDepartment,
  ProfilePerson,
} from "@/modules/profiles-admin/types";

export default function ProfilesPage() {
  const { t } = useLanguage();
  const tAny = (key: string) => t(key as never);
  const { hasPermission } = usePermissions();
  const { getHandlers } = useMutationFeedback();

  const [email, setEmail] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");

  const peopleQuery = useProfilePeople({ page: 1, page_size: 20 });
  const departmentsQuery = useProfileDepartments({ page: 1, page_size: 20 });
  const createPerson = useCreateProfilePerson();

  if (!hasPermission(PERMISSIONS.PROFILES_READ)) return <AccessDenied />;

  if (peopleQuery.error || departmentsQuery.error) {
    return (
      <ErrorState
        title="Failed to load profiles data"
        onRetry={() => {
          peopleQuery.refetch();
          departmentsQuery.refetch();
        }}
      />
    );
  }

  const peopleColumns: Column<ProfilePerson>[] = [
    {
      key: "name",
      header: tAny("identityProvider"),
      cell: (row) => `${row.first_name} ${row.last_name}`,
      sortValue: (row) => `${row.first_name} ${row.last_name}`,
    },
    {
      key: "email",
      header: tAny("profileEmail"),
      cell: (row) => row.email,
      sortValue: (row) => row.email,
    },
    {
      key: "status",
      header: tAny("profileStatus"),
      cell: (row) => row.status,
      sortValue: (row) => row.status,
    },
  ];

  const departmentsColumns: Column<ProfileDepartment>[] = [
    {
      key: "code",
      header: "Code",
      cell: (row) => row.code,
      sortValue: (row) => row.code,
    },
    {
      key: "name",
      header: tAny("profilesDepartments"),
      cell: (row) => row.name,
      sortValue: (row) => row.name,
    },
    {
      key: "unit_type",
      header: tAny("profileUnitType"),
      cell: (row) => row.unit_type,
      sortValue: (row) => row.unit_type,
    },
    {
      key: "status",
      header: tAny("profileStatus"),
      cell: (row) => row.status,
      sortValue: (row) => row.status,
    },
  ];

  const canCreate =
    email.trim().length > 0 &&
    firstName.trim().length > 0 &&
    lastName.trim().length > 0;

  return (
    <div className="space-y-6" data-testid="profiles-page">
      <PageHeader
        title={t("nav.profiles")}
        description={tAny("profilesHelp")}
        icon={ContactRound}
      />

      <section className="rounded-lg border bg-card p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold">{tAny("profilesPeople")}</h2>
          <PermissionGate permission={PERMISSIONS.PROFILES_WRITE}>
            <Button
              size="sm"
              disabled={!canCreate || createPerson.isPending}
              onClick={() =>
                createPerson.mutate(
                  {
                    email: email.trim(),
                    first_name: firstName.trim(),
                    last_name: lastName.trim(),
                    status: "active",
                  },
                  {
                    ...getHandlers({
                      successTitle: tAny("profilePersonCreated"),
                    }),
                    onSuccess: () => {
                      getHandlers({
                        successTitle: tAny("profilePersonCreated"),
                      }).onSuccess(undefined);
                      setEmail("");
                      setFirstName("");
                      setLastName("");
                    },
                  },
                )
              }
            >
              <Plus className="h-4 w-4 mr-1" />
              {tAny("add")}
            </Button>
          </PermissionGate>
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <div className="space-y-1.5">
            <Label htmlFor="profile-first-name">
              {tAny("profileFirstName")}
            </Label>
            <Input
              id="profile-first-name"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              placeholder="Aigerim"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="profile-last-name">{tAny("profileLastName")}</Label>
            <Input
              id="profile-last-name"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              placeholder="Sadykova"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="profile-email">{tAny("profileEmail")}</Label>
            <Input
              id="profile-email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="aigerim.sadykova@university.edu"
            />
          </div>
        </div>

        <DataTable
          columns={peopleColumns}
          data={peopleQuery.data?.items ?? []}
          isLoading={peopleQuery.isLoading}
          getRowKey={(row) => String(row.id)}
          emptyTitle={tAny("profileNoPeople")}
        />
      </section>

      <section className="rounded-lg border bg-card p-4 space-y-3">
        <h2 className="text-sm font-semibold">{tAny("profilesDepartments")}</h2>
        <DataTable
          columns={departmentsColumns}
          data={departmentsQuery.data?.items ?? []}
          isLoading={departmentsQuery.isLoading}
          getRowKey={(row) => String(row.id)}
          emptyTitle={tAny("profileNoDepartments")}
        />
      </section>
    </div>
  );
}
