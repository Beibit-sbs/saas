"use client";

import { useMemo, useState } from "react";
import { Wallet } from "lucide-react";
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
  useCostCenters,
  useCreateCostCenter,
  useCreateExpenseRecord,
  useExpenseBrainContext,
  useExpenseRecords,
} from "@/modules/expense_controls/hooks";
import type {
  CostCenter,
  CostCenterCreatePayload,
  ExpenseRecord,
  ExpenseRecordCreatePayload,
} from "@/modules/expense_controls/types";

interface CostCenterFormState {
  name: string;
  code: string;
  department_id: string;
  budget_limit: string;
  currency: string;
}

interface ExpenseFormState {
  cost_center_id: string;
  category: string;
  amount: string;
  currency: string;
  status: string;
  description: string;
}

const EMPTY_CC_FORM: CostCenterFormState = {
  name: "",
  code: "",
  department_id: "",
  budget_limit: "",
  currency: "USD",
};

const EMPTY_EXPENSE_FORM: ExpenseFormState = {
  cost_center_id: "",
  category: "",
  amount: "",
  currency: "USD",
  status: "pending",
  description: "",
};

const STATUS_COLOR: Record<string, string> = {
  pending: "bg-amber-100 text-amber-700",
  approved: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
  paid: "bg-blue-100 text-blue-700",
};

export default function ExpenseControlsPage() {
  const { getHandlers } = useMutationFeedback();
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [selectedCostCenter, setSelectedCostCenter] = useState<string>("all");
  const [costCenterForm, setCostCenterForm] = useState<CostCenterFormState>(EMPTY_CC_FORM);
  const [expenseForm, setExpenseForm] = useState<ExpenseFormState>(EMPTY_EXPENSE_FORM);

  const { data: brainContext } = useExpenseBrainContext();
  const {
    data: costCentersData,
    isLoading: isCostCentersLoading,
    error: costCentersError,
    refetch: refetchCostCenters,
  } = useCostCenters();
  const {
    data: expensesData,
    isLoading: isExpensesLoading,
    error: expensesError,
    refetch: refetchExpenses,
  } = useExpenseRecords({
    status: selectedStatus !== "all" ? selectedStatus : undefined,
    cost_center_id: selectedCostCenter !== "all" ? Number(selectedCostCenter) : undefined,
  });

  const createCostCenter = useCreateCostCenter();
  const createExpenseRecord = useCreateExpenseRecord();

  const isSubmitting = createCostCenter.isPending || createExpenseRecord.isPending;

  const canCreateCostCenter = useMemo(() => {
    const budget = Number(costCenterForm.budget_limit);
    return (
      costCenterForm.name.trim().length > 0
      && costCenterForm.code.trim().length > 0
      && costCenterForm.currency.trim().length > 0
      && Number.isFinite(budget)
      && budget > 0
    );
  }, [costCenterForm]);

  const canCreateExpense = useMemo(() => {
    const amount = Number(expenseForm.amount);
    return (
      expenseForm.cost_center_id.trim().length > 0
      && expenseForm.category.trim().length > 0
      && expenseForm.currency.trim().length > 0
      && Number.isFinite(amount)
      && amount > 0
    );
  }, [expenseForm]);

  const costCenters = costCentersData?.records ?? [];
  const expenses = expensesData?.records ?? [];

  const costCenterColumns: Column<CostCenter>[] = [
    {
      key: "code",
      header: "Code",
      cell: (row) => <span className="font-mono text-xs">{row.code}</span>,
      sortValue: (row) => row.code,
    },
    {
      key: "name",
      header: "Name",
      cell: (row) => <span className="font-medium">{row.name}</span>,
      sortValue: (row) => row.name.toLowerCase(),
    },
    {
      key: "department_id",
      header: "Department",
      cell: (row) => row.department_id || "-",
      sortValue: (row) => row.department_id || "",
    },
    {
      key: "budget_limit",
      header: "Budget Limit",
      cell: (row) => `${row.currency} ${row.budget_limit.toLocaleString()}`,
      sortValue: (row) => row.budget_limit,
    },
    {
      key: "active",
      header: "State",
      cell: (row) => (
        <Badge className={row.active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-700"}>
          {row.active ? "active" : "inactive"}
        </Badge>
      ),
      sortValue: (row) => (row.active ? 1 : 0),
    },
  ];

  const expenseColumns: Column<ExpenseRecord>[] = [
    {
      key: "id",
      header: "ID",
      cell: (row) => <span className="font-mono text-xs">#{row.id}</span>,
      sortValue: (row) => row.id,
    },
    {
      key: "cost_center_id",
      header: "Cost Center",
      cell: (row) => {
        const center = costCenters.find((c) => c.id === row.cost_center_id);
        return center ? `${center.code} (${center.name})` : String(row.cost_center_id);
      },
      sortValue: (row) => row.cost_center_id,
    },
    {
      key: "category",
      header: "Category",
      cell: (row) => row.category,
      sortValue: (row) => row.category.toLowerCase(),
    },
    {
      key: "amount",
      header: "Amount",
      cell: (row) => `${row.currency} ${row.amount.toLocaleString()}`,
      sortValue: (row) => row.amount,
    },
    {
      key: "status",
      header: "Status",
      cell: (row) => (
        <Badge className={STATUS_COLOR[row.status] ?? "bg-gray-100 text-gray-700"}>{row.status}</Badge>
      ),
      sortValue: (row) => row.status,
    },
    {
      key: "description",
      header: "Description",
      cell: (row) => row.description || "-",
      sortValue: (row) => row.description || "",
    },
  ];

  if (costCentersError && expensesError) {
    return (
      <ErrorState
        title="Failed to load expense controls data"
        onRetry={() => {
          refetchCostCenters();
          refetchExpenses();
        }}
      />
    );
  }

  return (
    <RequirePermission permission={PERMISSIONS.FINANCE_READ}>
      <div className="space-y-8" data-testid="expense-controls-page">
        <PageHeader
          title="Expense Controls"
          description="Track cost centers, expenses, and budget-risk signals for finance operations."
          icon={Wallet}
        />

        <div className="grid gap-3 md:grid-cols-5">
          <div className="rounded-lg border p-3 text-center">
            <p className="text-2xl font-bold">{brainContext?.total_cost_centers ?? 0}</p>
            <p className="text-xs text-muted-foreground">Cost Centers</p>
          </div>
          <div className="rounded-lg border p-3 text-center">
            <p className="text-2xl font-bold">{brainContext?.total_expenses ?? 0}</p>
            <p className="text-xs text-muted-foreground">Total Expenses</p>
          </div>
          <div className="rounded-lg border p-3 text-center">
            <p className="text-2xl font-bold text-amber-600">{brainContext?.pending_expenses ?? 0}</p>
            <p className="text-xs text-muted-foreground">Pending</p>
          </div>
          <div className="rounded-lg border p-3 text-center">
            <p className="text-2xl font-bold text-green-600">{brainContext?.approved_expenses ?? 0}</p>
            <p className="text-xs text-muted-foreground">Approved</p>
          </div>
          <div className="rounded-lg border p-3 text-center">
            <p className="text-2xl font-bold text-red-600">{brainContext?.budget_exceeded_alerts ?? 0}</p>
            <p className="text-xs text-muted-foreground">Budget Alerts</p>
          </div>
        </div>

        <RequirePermission permission={PERMISSIONS.FINANCE_WRITE}>
          <div className="grid gap-6 md:grid-cols-2">
            <div className="space-y-3 rounded-lg border p-4">
              <h3 className="font-semibold">Create Cost Center</h3>
              <div className="space-y-1">
                <Label htmlFor="cc-name">Name</Label>
                <Input
                  id="cc-name"
                  value={costCenterForm.name}
                  onChange={(e) => setCostCenterForm((p) => ({ ...p, name: e.target.value }))}
                  placeholder="Operations Center"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="cc-code">Code</Label>
                <Input
                  id="cc-code"
                  value={costCenterForm.code}
                  onChange={(e) => setCostCenterForm((p) => ({ ...p, code: e.target.value }))}
                  placeholder="CC-OPS"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="cc-department">Department ID</Label>
                <Input
                  id="cc-department"
                  value={costCenterForm.department_id}
                  onChange={(e) =>
                    setCostCenterForm((p) => ({ ...p, department_id: e.target.value }))
                  }
                  placeholder="DEPT-OPS"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label htmlFor="cc-budget">Budget Limit</Label>
                  <Input
                    id="cc-budget"
                    type="number"
                    min="0"
                    value={costCenterForm.budget_limit}
                    onChange={(e) =>
                      setCostCenterForm((p) => ({ ...p, budget_limit: e.target.value }))
                    }
                    placeholder="50000"
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="cc-currency">Currency</Label>
                  <Input
                    id="cc-currency"
                    value={costCenterForm.currency}
                    onChange={(e) => setCostCenterForm((p) => ({ ...p, currency: e.target.value }))}
                    placeholder="USD"
                  />
                </div>
              </div>
              <Button
                disabled={!canCreateCostCenter || isSubmitting}
                onClick={() => {
                  const payload: CostCenterCreatePayload = {
                    name: costCenterForm.name.trim(),
                    code: costCenterForm.code.trim(),
                    department_id: costCenterForm.department_id.trim() || undefined,
                    budget_limit: Number(costCenterForm.budget_limit),
                    currency: costCenterForm.currency.trim() || "USD",
                    active: true,
                  };

                  createCostCenter.mutate(
                    payload,
                    (() => {
                      const handlers = getHandlers({ successTitle: "Cost center created" });
                      return {
                        ...handlers,
                        onSuccess: (result: unknown) => {
                          handlers.onSuccess(result);
                          setCostCenterForm(EMPTY_CC_FORM);
                        },
                      };
                    })(),
                  );
                }}
              >
                Create Cost Center
              </Button>
            </div>

            <div className="space-y-3 rounded-lg border p-4">
              <h3 className="font-semibold">Create Expense Record</h3>
              <div className="space-y-1">
                <Label htmlFor="expense-center">Cost Center</Label>
                <select
                  id="expense-center"
                  className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                  value={expenseForm.cost_center_id}
                  onChange={(e) => setExpenseForm((p) => ({ ...p, cost_center_id: e.target.value }))}
                >
                  <option value="">Select cost center</option>
                  {costCenters.map((center) => (
                    <option key={center.id} value={String(center.id)}>
                      {center.code} - {center.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1">
                <Label htmlFor="expense-category">Category</Label>
                <Input
                  id="expense-category"
                  value={expenseForm.category}
                  onChange={(e) => setExpenseForm((p) => ({ ...p, category: e.target.value }))}
                  placeholder="operations"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <Label htmlFor="expense-amount">Amount</Label>
                  <Input
                    id="expense-amount"
                    type="number"
                    min="0"
                    value={expenseForm.amount}
                    onChange={(e) => setExpenseForm((p) => ({ ...p, amount: e.target.value }))}
                    placeholder="1200"
                  />
                </div>
                <div className="space-y-1">
                  <Label htmlFor="expense-currency">Currency</Label>
                  <Input
                    id="expense-currency"
                    value={expenseForm.currency}
                    onChange={(e) => setExpenseForm((p) => ({ ...p, currency: e.target.value }))}
                    placeholder="USD"
                  />
                </div>
              </div>
              <div className="space-y-1">
                <Label htmlFor="expense-status">Status</Label>
                <select
                  id="expense-status"
                  className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                  value={expenseForm.status}
                  onChange={(e) => setExpenseForm((p) => ({ ...p, status: e.target.value }))}
                >
                  <option value="pending">pending</option>
                  <option value="approved">approved</option>
                  <option value="rejected">rejected</option>
                  <option value="paid">paid</option>
                </select>
              </div>
              <div className="space-y-1">
                <Label htmlFor="expense-description">Description</Label>
                <Input
                  id="expense-description"
                  value={expenseForm.description}
                  onChange={(e) => setExpenseForm((p) => ({ ...p, description: e.target.value }))}
                  placeholder="Quarterly cloud services"
                />
              </div>
              <Button
                disabled={!canCreateExpense || isSubmitting}
                onClick={() => {
                  const payload: ExpenseRecordCreatePayload = {
                    cost_center_id: Number(expenseForm.cost_center_id),
                    category: expenseForm.category.trim(),
                    amount: Number(expenseForm.amount),
                    currency: expenseForm.currency.trim() || "USD",
                    status: expenseForm.status,
                    description: expenseForm.description.trim() || undefined,
                  };

                  createExpenseRecord.mutate(
                    payload,
                    (() => {
                      const handlers = getHandlers({ successTitle: "Expense record created" });
                      return {
                        ...handlers,
                        onSuccess: (result: unknown) => {
                          handlers.onSuccess(result);
                          setExpenseForm(EMPTY_EXPENSE_FORM);
                        },
                      };
                    })(),
                  );
                }}
              >
                Create Expense
              </Button>
            </div>
          </div>
        </RequirePermission>

        <div className="space-y-3 rounded-lg border p-4">
          <h3 className="font-semibold">Expense Filters</h3>
          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-1">
              <Label htmlFor="status-filter">Status</Label>
              <select
                id="status-filter"
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
              >
                <option value="all">all</option>
                <option value="pending">pending</option>
                <option value="approved">approved</option>
                <option value="rejected">rejected</option>
                <option value="paid">paid</option>
              </select>
            </div>
            <div className="space-y-1">
              <Label htmlFor="cost-center-filter">Cost Center</Label>
              <select
                id="cost-center-filter"
                className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                value={selectedCostCenter}
                onChange={(e) => setSelectedCostCenter(e.target.value)}
              >
                <option value="all">all</option>
                {costCenters.map((center) => (
                  <option key={center.id} value={String(center.id)}>
                    {center.code} - {center.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="font-semibold">Cost Centers</h3>
          <DataTable
            columns={costCenterColumns}
            data={costCenters}
            isLoading={isCostCentersLoading}
            getRowKey={(row) => String(row.id)}
            emptyTitle="No cost centers yet"
            emptyDescription="Create at least one cost center to start tracking expenses."
          />
        </div>

        <div className="space-y-4">
          <h3 className="font-semibold">Expense Records</h3>
          <DataTable
            columns={expenseColumns}
            data={expenses}
            isLoading={isExpensesLoading}
            getRowKey={(row) => String(row.id)}
            emptyTitle="No expense records found"
            emptyDescription="Try changing filters or create a new expense record."
          />
        </div>
      </div>
    </RequirePermission>
  );
}
