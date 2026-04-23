"use client";

import { useMemo, useState } from "react";
import { UsersRound } from "lucide-react";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { DataTable, type Column } from "@/shared/ui/data-table";
import { ErrorState } from "@/shared/ui/error-state";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { PERMISSIONS } from "@/shared/config/permissions";
import { useMutationFeedback } from "@/shared/hooks/use-mutation-feedback";
import {
  useCreateHrEmployee,
  useCreatePayrollCycle,
  useHrEmployees,
  usePayrollCycles,
  useUpdateHrEmployeeStatus,
  useUpdatePayrollCycleStatus,
} from "@/modules/hr-payroll/hooks";
import type {
  HrEmployee,
  HrEmployeeStatus,
  PayrollCycle,
  PayrollCycleStatus,
} from "@/modules/hr-payroll/types";

interface EmployeeFormState {
  employee_code: string;
  full_name: string;
  department_id: string;
  role_title: string;
}

interface CycleFormState {
  cycle_code: string;
  period_label: string;
  total_gross: string;
  total_net: string;
  employee_count: string;
}

const EMPTY_EMPLOYEE: EmployeeFormState = {
  employee_code: "",
  full_name: "",
  department_id: "",
  role_title: "",
};

const EMPTY_CYCLE: CycleFormState = {
  cycle_code: "",
  period_label: "",
  total_gross: "",
  total_net: "",
  employee_count: "",
};

const EMPLOYEE_COLORS: Record<HrEmployeeStatus, string> = {
  active: "bg-green-100 text-green-700",
  on_leave: "bg-amber-100 text-amber-700",
  onboarding: "bg-blue-100 text-blue-700",
  offboarding: "bg-orange-100 text-orange-700",
  terminated: "bg-gray-100 text-gray-700",
};

const CYCLE_COLORS: Record<PayrollCycleStatus, string> = {
  pending: "bg-amber-100 text-amber-700",
  processing: "bg-blue-100 text-blue-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

const NEXT_EMPLOYEE: Record<HrEmployeeStatus, HrEmployeeStatus[]> = {
  onboarding: ["active", "terminated"],
  active: ["on_leave", "offboarding", "terminated"],
  on_leave: ["active", "terminated"],
  offboarding: ["terminated"],
  terminated: [],
};

const NEXT_CYCLE: Record<PayrollCycleStatus, PayrollCycleStatus[]> = {
  pending: ["processing", "failed"],
  processing: ["completed", "failed"],
  completed: [],
  failed: ["processing"],
};

export default function HrPayrollPage() {
  const { getHandlers } = useMutationFeedback();
  const [employeeForm, setEmployeeForm] = useState<EmployeeFormState>(EMPTY_EMPLOYEE);
  const [cycleForm, setCycleForm] = useState<CycleFormState>(EMPTY_CYCLE);

  const employees = useHrEmployees();
  const cycles = usePayrollCycles();
  const createEmployee = useCreateHrEmployee();
  const createCycle = useCreatePayrollCycle();
  const updateEmployeeStatus = useUpdateHrEmployeeStatus();
  const updateCycleStatus = useUpdatePayrollCycleStatus();

  const error = employees.error ?? cycles.error;
  const refetch = () => {
    employees.refetch();
    cycles.refetch();
  };

  const isSubmitting = createEmployee.isPending
    || createCycle.isPending
    || updateEmployeeStatus.isPending
    || updateCycleStatus.isPending;

  const canCreateEmployee = useMemo(
    () =>
      employeeForm.employee_code.trim().length > 0
      && employeeForm.full_name.trim().length > 0
      && employeeForm.department_id.trim().length > 0
      && employeeForm.role_title.trim().length > 0,
    [employeeForm],
  );

  const canCreateCycle = useMemo(() => {
    const gross = Number(cycleForm.total_gross);
    const net = Number(cycleForm.total_net);
    const count = Number(cycleForm.employee_count);
    return (
      cycleForm.cycle_code.trim().length > 0
      && cycleForm.period_label.trim().length > 0
      && !Number.isNaN(gross)
      && gross >= 0
      && !Number.isNaN(net)
      && net >= 0
      && !Number.isNaN(count)
      && count >= 1
    );
  }, [cycleForm]);

  if (error) {
    return <ErrorState title="Failed to load HR/Payroll data" onRetry={refetch} />;
  }

  const employeeColumns: Column<HrEmployee>[] = [
    {
      key: "employee_code",
      header: "Employee Code",
      cell: (row) => <span className="font-mono text-xs">{row.employee_code}</span>,
      sortValue: (row) => row.employee_code,
    },
    {
      key: "full_name",
      header: "Name",
      cell: (row) => <span className="font-medium">{row.full_name}</span>,
      sortValue: (row) => row.full_name.toLowerCase(),
    },
    {
      key: "department_id",
      header: "Department",
      cell: (row) => row.department_id,
      sortValue: (row) => row.department_id,
    },
    {
      key: "role_title",
      header: "Role",
      cell: (row) => row.role_title,
      sortValue: (row) => row.role_title.toLowerCase(),
    },
    {
      key: "status",
      header: "Status",
      cell: (row) => <Badge className={EMPLOYEE_COLORS[row.status]}>{row.status}</Badge>,
      sortValue: (row) => row.status,
    },
    {
      key: "actions",
      header: "Actions",
      cell: (row) => {
        const nexts = NEXT_EMPLOYEE[row.status] ?? [];
        if (nexts.length === 0) return null;
        return (
          <div className="flex gap-1 flex-wrap">
            {nexts.map((next) => (
              <Button
                key={next}
                variant="outline"
                size="sm"
                disabled={isSubmitting}
                onClick={() =>
                  updateEmployeeStatus.mutate(
                    { employeeId: row.id, payload: { status: next } },
                    getHandlers(`Employee moved to ${next}`),
                  )
                }
              >
                → {next}
              </Button>
            ))}
          </div>
        );
      },
    },
  ];

  const cycleColumns: Column<PayrollCycle>[] = [
    {
      key: "cycle_code",
      header: "Cycle Code",
      cell: (row) => <span className="font-mono text-xs">{row.cycle_code}</span>,
      sortValue: (row) => row.cycle_code,
    },
    {
      key: "period_label",
      header: "Period",
      cell: (row) => row.period_label,
      sortValue: (row) => row.period_label,
    },
    {
      key: "employee_count",
      header: "Employees",
      cell: (row) => row.employee_count,
      sortValue: (row) => row.employee_count,
    },
    {
      key: "total_gross",
      header: "Gross",
      cell: (row) => `$${row.total_gross.toLocaleString()}`,
      sortValue: (row) => row.total_gross,
    },
    {
      key: "total_net",
      header: "Net",
      cell: (row) => `$${row.total_net.toLocaleString()}`,
      sortValue: (row) => row.total_net,
    },
    {
      key: "status",
      header: "Status",
      cell: (row) => <Badge className={CYCLE_COLORS[row.status]}>{row.status}</Badge>,
      sortValue: (row) => row.status,
    },
    {
      key: "actions",
      header: "Actions",
      cell: (row) => {
        const nexts = NEXT_CYCLE[row.status] ?? [];
        if (nexts.length === 0) return null;
        return (
          <div className="flex gap-1 flex-wrap">
            {nexts.map((next) => (
              <Button
                key={next}
                variant="outline"
                size="sm"
                disabled={isSubmitting}
                onClick={() =>
                  updateCycleStatus.mutate(
                    { cycleId: row.id, payload: { status: next } },
                    getHandlers(`Cycle moved to ${next}`),
                  )
                }
              >
                → {next}
              </Button>
            ))}
          </div>
        );
      },
    },
  ];

  const submitEmployee = () => {
    if (!canCreateEmployee) return;

    createEmployee.mutate(
      {
        employee_code: employeeForm.employee_code.trim(),
        full_name: employeeForm.full_name.trim(),
        department_id: employeeForm.department_id.trim(),
        role_title: employeeForm.role_title.trim(),
        status: "onboarding",
      },
      {
        ...getHandlers("Employee record created"),
        onSuccess: (...args) => {
          setEmployeeForm(EMPTY_EMPLOYEE);
          getHandlers("Employee record created").onSuccess?.(...args);
        },
      },
    );
  };

  const submitCycle = () => {
    if (!canCreateCycle) return;

    createCycle.mutate(
      {
        cycle_code: cycleForm.cycle_code.trim(),
        period_label: cycleForm.period_label.trim(),
        total_gross: Number(cycleForm.total_gross),
        total_net: Number(cycleForm.total_net),
        employee_count: Number(cycleForm.employee_count),
        status: "pending",
      },
      {
        ...getHandlers("Payroll cycle created"),
        onSuccess: (...args) => {
          setCycleForm(EMPTY_CYCLE);
          getHandlers("Payroll cycle created").onSuccess?.(...args);
        },
      },
    );
  };

  return (
    <RequirePermission permission={PERMISSIONS.HR_READ}>
      <div className="space-y-8">
        <PageHeader
          title="HR & Payroll"
          subtitle="Manage employee lifecycle and payroll cycle execution"
          icon={UsersRound}
        />

        <RequirePermission permission={PERMISSIONS.HR_WRITE}>
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-lg font-semibold mb-4">Add Employee</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <Label htmlFor="employee_code">Employee Code</Label>
                <Input
                  id="employee_code"
                  placeholder="EMP-1001"
                  value={employeeForm.employee_code}
                  onChange={(e) =>
                    setEmployeeForm((f) => ({ ...f, employee_code: e.target.value }))
                  }
                />
              </div>
              <div>
                <Label htmlFor="full_name">Full Name</Label>
                <Input
                  id="full_name"
                  placeholder="John Smith"
                  value={employeeForm.full_name}
                  onChange={(e) => setEmployeeForm((f) => ({ ...f, full_name: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="department_id">Department</Label>
                <Input
                  id="department_id"
                  placeholder="DEPT-HR"
                  value={employeeForm.department_id}
                  onChange={(e) =>
                    setEmployeeForm((f) => ({ ...f, department_id: e.target.value }))
                  }
                />
              </div>
              <div>
                <Label htmlFor="role_title">Role</Label>
                <Input
                  id="role_title"
                  placeholder="HR Partner"
                  value={employeeForm.role_title}
                  onChange={(e) => setEmployeeForm((f) => ({ ...f, role_title: e.target.value }))}
                />
              </div>
            </div>
            <Button className="mt-4" disabled={!canCreateEmployee || isSubmitting} onClick={submitEmployee}>
              {createEmployee.isPending ? "Creating..." : "Create Employee"}
            </Button>
          </div>

          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-lg font-semibold mb-4">Add Payroll Cycle</h2>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <div>
                <Label htmlFor="cycle_code">Cycle Code</Label>
                <Input
                  id="cycle_code"
                  placeholder="PAY-2026-05"
                  value={cycleForm.cycle_code}
                  onChange={(e) => setCycleForm((f) => ({ ...f, cycle_code: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="period_label">Period</Label>
                <Input
                  id="period_label"
                  placeholder="May 2026"
                  value={cycleForm.period_label}
                  onChange={(e) => setCycleForm((f) => ({ ...f, period_label: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="total_gross">Gross Amount</Label>
                <Input
                  id="total_gross"
                  type="number"
                  min="0"
                  value={cycleForm.total_gross}
                  onChange={(e) => setCycleForm((f) => ({ ...f, total_gross: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="total_net">Net Amount</Label>
                <Input
                  id="total_net"
                  type="number"
                  min="0"
                  value={cycleForm.total_net}
                  onChange={(e) => setCycleForm((f) => ({ ...f, total_net: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="employee_count">Employee Count</Label>
                <Input
                  id="employee_count"
                  type="number"
                  min="1"
                  value={cycleForm.employee_count}
                  onChange={(e) =>
                    setCycleForm((f) => ({ ...f, employee_count: e.target.value }))
                  }
                />
              </div>
            </div>
            <Button className="mt-4" disabled={!canCreateCycle || isSubmitting} onClick={submitCycle}>
              {createCycle.isPending ? "Creating..." : "Create Payroll Cycle"}
            </Button>
          </div>
        </RequirePermission>

        <DataTable
          columns={employeeColumns}
          data={employees.data?.items ?? []}
          isLoading={employees.isLoading}
          getRowKey={(row) => String(row.id)}
          emptyTitle="No employee records found"
          emptyDescription="Create your first employee above."
        />

        <DataTable
          columns={cycleColumns}
          data={cycles.data?.items ?? []}
          isLoading={cycles.isLoading}
          getRowKey={(row) => String(row.id)}
          emptyTitle="No payroll cycles found"
          emptyDescription="Create your first cycle above."
        />
      </div>
    </RequirePermission>
  );
}
