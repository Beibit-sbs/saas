"use client";

import { useMemo, useState } from "react";
import { Package } from "lucide-react";
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
import { Wave1KpiBar } from "@/modules/platform/kpi/wave1-kpi-bar";
import {
  useAssetItems,
  useCreateAssetItem,
  useCreateDepreciationRecord,
  useDepreciationRecords,
  useUpdateAssetItemStatus,
} from "@/modules/asset-inventory/hooks";
import type {
  AssetItem,
  AssetStatus,
  DepreciationRecord,
} from "@/modules/asset-inventory/types";

interface AssetFormState {
  asset_code: string;
  name: string;
  location: string;
  purchase_year: string;
}

interface DeprFormState {
  asset_code: string;
  original_value: string;
  current_value: string;
  depreciation_rate: string;
}

const EMPTY_ASSET: AssetFormState = { asset_code: "", name: "", location: "", purchase_year: "" };
const EMPTY_DEPR: DeprFormState = { asset_code: "", original_value: "", current_value: "", depreciation_rate: "" };

const ASSET_STATUS_COLORS: Record<AssetStatus, string> = {
  active: "bg-green-100 text-green-700",
  in_maintenance: "bg-amber-100 text-amber-700",
  decommissioned: "bg-gray-100 text-gray-700",
};

const NEXT_ASSET_STATUS: Record<AssetStatus, AssetStatus[]> = {
  active: ["in_maintenance", "decommissioned"],
  in_maintenance: ["active", "decommissioned"],
  decommissioned: [],
};

export default function AssetInventoryPage() {
  const { getHandlers } = useMutationFeedback();
  const [assetForm, setAssetForm] = useState<AssetFormState>(EMPTY_ASSET);
  const [deprForm, setDeprForm] = useState<DeprFormState>(EMPTY_DEPR);

  const assets = useAssetItems();
  const depreciation = useDepreciationRecords();
  const createAsset = useCreateAssetItem();
  const createDepr = useCreateDepreciationRecord();
  const updateAssetStatus = useUpdateAssetItemStatus();

  const error = assets.error ?? depreciation.error;
  const refetch = () => {
    assets.refetch();
    depreciation.refetch();
  };

  const isSubmitting =
    createAsset.isPending || createDepr.isPending || updateAssetStatus.isPending;

  const canCreateAsset = useMemo(() => {
    const year = Number(assetForm.purchase_year);
    return (
      assetForm.asset_code.trim().length > 0 &&
      assetForm.name.trim().length > 0 &&
      assetForm.location.trim().length > 0 &&
      !Number.isNaN(year) &&
      year >= 2000
    );
  }, [assetForm]);

  const canCreateDepr = useMemo(() => {
    const orig = Number(deprForm.original_value);
    const curr = Number(deprForm.current_value);
    const rate = Number(deprForm.depreciation_rate);
    return (
      deprForm.asset_code.trim().length > 0 &&
      !Number.isNaN(orig) &&
      orig >= 0 &&
      !Number.isNaN(curr) &&
      curr >= 0 &&
      !Number.isNaN(rate) &&
      rate >= 0 &&
      rate <= 1
    );
  }, [deprForm]);

  if (error) {
    return <ErrorState title="Failed to load asset inventory data" onRetry={refetch} />;
  }

  const assetColumns: Column<AssetItem>[] = [
    {
      key: "asset_code",
      header: "Asset Code",
      cell: (row) => <span className="font-mono text-xs">{row.asset_code}</span>,
      sortValue: (row) => row.asset_code,
    },
    {
      key: "name",
      header: "Name",
      cell: (row) => <span className="font-medium">{row.name}</span>,
      sortValue: (row) => row.name.toLowerCase(),
    },
    {
      key: "category",
      header: "Category",
      cell: (row) => row.category,
      sortValue: (row) => row.category,
    },
    {
      key: "location",
      header: "Location",
      cell: (row) => row.location,
      sortValue: (row) => row.location.toLowerCase(),
    },
    {
      key: "condition",
      header: "Condition",
      cell: (row) => (
        <Badge
          className={
            row.condition === "condemned" || row.condition === "poor"
              ? "bg-red-100 text-red-700"
              : row.condition === "fair"
                ? "bg-yellow-100 text-yellow-700"
                : "bg-green-100 text-green-700"
          }
        >
          {row.condition}
        </Badge>
      ),
      sortValue: (row) => row.condition,
    },
    {
      key: "status",
      header: "Status",
      cell: (row) => (
        <Badge className={ASSET_STATUS_COLORS[row.status]}>{row.status}</Badge>
      ),
      sortValue: (row) => row.status,
    },
    {
      key: "actions",
      header: "Actions",
      cell: (row) => {
        const nexts = NEXT_ASSET_STATUS[row.status] ?? [];
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
                  updateAssetStatus.mutate(
                    { assetId: row.id, payload: { status: next } },
                    getHandlers({ successTitle: `Asset moved to ${next}` }),
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

  const deprColumns: Column<DepreciationRecord>[] = [
    {
      key: "asset_code",
      header: "Asset Code",
      cell: (row) => <span className="font-mono text-xs">{row.asset_code}</span>,
      sortValue: (row) => row.asset_code,
    },
    {
      key: "depreciation_method",
      header: "Method",
      cell: (row) => row.depreciation_method,
      sortValue: (row) => row.depreciation_method,
    },
    {
      key: "original_value",
      header: "Original Value",
      cell: (row) => `$${row.original_value.toLocaleString()}`,
      sortValue: (row) => row.original_value,
    },
    {
      key: "current_value",
      header: "Current Value",
      cell: (row) => `$${row.current_value.toLocaleString()}`,
      sortValue: (row) => row.current_value,
    },
    {
      key: "depreciation_rate",
      header: "Rate",
      cell: (row) => `${(row.depreciation_rate * 100).toFixed(0)}%`,
      sortValue: (row) => row.depreciation_rate,
    },
    {
      key: "status",
      header: "Status",
      cell: (row) => (
        <Badge className={row.status === "active" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-700"}>
          {row.status}
        </Badge>
      ),
      sortValue: (row) => row.status,
    },
  ];

  return (
    <RequirePermission permission={PERMISSIONS.ASSET_INVENTORY_READ}>
      <div className="space-y-8">
        <PageHeader
          title="Asset Inventory"
          description="Track campus assets, inventory management, and depreciation lifecycle"
          icon={Package}
        />

        <Wave1KpiBar
          metricKeys={["po_delivery_completion_rate","delivered_po_asset_conversion_rate","asset_conversion_gap_count","inventory_low_stock_items_count","critical_supply_risk_count","reorder_recommendations_count","supply_risk_actions_count"]}
          labels={{
            po_delivery_completion_rate: "PO Delivery Rate (%)",
            delivered_po_asset_conversion_rate: "Asset Conversion Rate (%)",
            asset_conversion_gap_count: "Conversion Gap",
            inventory_low_stock_items_count: "Low Stock Items",
            critical_supply_risk_count: "Critical Supply Risk",
            reorder_recommendations_count: "Reorder Needed",
            supply_risk_actions_count: "Supply Risk Actions",
          }}
        />

        <RequirePermission permission={PERMISSIONS.ASSET_INVENTORY_WRITE}>
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-lg font-semibold mb-4">Register Asset</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <Label htmlFor="asset_code">Asset Code</Label>
                <Input
                  id="asset_code"
                  placeholder="ASSET-2026-001"
                  value={assetForm.asset_code}
                  onChange={(e) => setAssetForm((f) => ({ ...f, asset_code: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="asset_name">Name</Label>
                <Input
                  id="asset_name"
                  placeholder="Laptop Dell XPS"
                  value={assetForm.name}
                  onChange={(e) => setAssetForm((f) => ({ ...f, name: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="asset_location">Location</Label>
                <Input
                  id="asset_location"
                  placeholder="Building A, Room 101"
                  value={assetForm.location}
                  onChange={(e) => setAssetForm((f) => ({ ...f, location: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="purchase_year">Purchase Year</Label>
                <Input
                  id="purchase_year"
                  type="number"
                  min="2000"
                  max="2100"
                  placeholder="2024"
                  value={assetForm.purchase_year}
                  onChange={(e) => setAssetForm((f) => ({ ...f, purchase_year: e.target.value }))}
                />
              </div>
            </div>
            <Button
              className="mt-4"
              disabled={!canCreateAsset || isSubmitting}
              onClick={() => {
                if (!canCreateAsset) return;
                createAsset.mutate(
                  {
                    asset_code: assetForm.asset_code.trim(),
                    name: assetForm.name.trim(),
                    location: assetForm.location.trim(),
                    purchase_year: Number(assetForm.purchase_year),
                    category: "equipment",
                    condition: "good",
                    status: "active",
                  },
                  {
                    ...getHandlers({ successTitle: "Asset registered" }),
                    onSuccess: (...args) => {
                      setAssetForm(EMPTY_ASSET);
                      getHandlers({ successTitle: "Asset registered" }).onSuccess?.(args[0]);
                    },
                  },
                );
              }}
            >
              {createAsset.isPending ? "Registering..." : "Register Asset"}
            </Button>
          </div>
        </RequirePermission>

        <DataTable
          columns={assetColumns}
          data={assets.data?.items ?? []}
          isLoading={assets.isLoading}
          getRowKey={(row) => String(row.id)}
          emptyTitle="No assets found"
          emptyDescription="Register your first asset above."
        />

        <RequirePermission permission={PERMISSIONS.ASSET_INVENTORY_WRITE}>
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-lg font-semibold mb-4">Add Depreciation Record</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <Label htmlFor="depr_asset_code">Asset Code</Label>
                <Input
                  id="depr_asset_code"
                  placeholder="ASSET-2026-001"
                  value={deprForm.asset_code}
                  onChange={(e) => setDeprForm((f) => ({ ...f, asset_code: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="original_value">Original Value ($)</Label>
                <Input
                  id="original_value"
                  type="number"
                  min="0"
                  step="0.01"
                  value={deprForm.original_value}
                  onChange={(e) => setDeprForm((f) => ({ ...f, original_value: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="current_value">Current Value ($)</Label>
                <Input
                  id="current_value"
                  type="number"
                  min="0"
                  step="0.01"
                  value={deprForm.current_value}
                  onChange={(e) => setDeprForm((f) => ({ ...f, current_value: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="depreciation_rate">Rate (0–1)</Label>
                <Input
                  id="depreciation_rate"
                  type="number"
                  min="0"
                  max="1"
                  step="0.01"
                  value={deprForm.depreciation_rate}
                  onChange={(e) => setDeprForm((f) => ({ ...f, depreciation_rate: e.target.value }))}
                />
              </div>
            </div>
            <Button
              className="mt-4"
              disabled={!canCreateDepr || isSubmitting}
              onClick={() => {
                if (!canCreateDepr) return;
                createDepr.mutate(
                  {
                    asset_code: deprForm.asset_code.trim(),
                    depreciation_method: "straight_line",
                    original_value: Number(deprForm.original_value),
                    current_value: Number(deprForm.current_value),
                    depreciation_rate: Number(deprForm.depreciation_rate),
                    status: "active",
                  },
                  {
                    ...getHandlers({ successTitle: "Depreciation record added" }),
                    onSuccess: (...args) => {
                      setDeprForm(EMPTY_DEPR);
                      getHandlers({ successTitle: "Depreciation record added" }).onSuccess?.(args[0]);
                    },
                  },
                );
              }}
            >
              {createDepr.isPending ? "Adding..." : "Add Record"}
            </Button>
          </div>
        </RequirePermission>

        <DataTable
          columns={deprColumns}
          data={depreciation.data?.items ?? []}
          isLoading={depreciation.isLoading}
          getRowKey={(row) => String(row.id)}
          emptyTitle="No depreciation records found"
          emptyDescription="Add your first depreciation record above."
        />
      </div>
    </RequirePermission>
  );
}
