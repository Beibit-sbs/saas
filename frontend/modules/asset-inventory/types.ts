export type AssetCategory = "equipment" | "furniture" | "it_hardware" | "vehicle" | "other";
export type AssetCondition = "new" | "good" | "fair" | "poor" | "condemned";
export type AssetStatus = "active" | "in_maintenance" | "decommissioned";

export type DepreciationMethod = "straight_line" | "declining_balance";
export type DepreciationStatus = "active" | "closed";

export interface AssetItem {
  id: number;
  tenant_id?: string | null;
  asset_code: string;
  name: string;
  category: AssetCategory;
  location: string;
  condition: AssetCondition;
  purchase_year: number;
  vendor?: string | null;
  status: AssetStatus;
}

export interface AssetListResponse {
  items: AssetItem[];
}

export interface AssetItemResponse {
  item: AssetItem;
}

export interface AssetItemCreatePayload {
  asset_code: string;
  name: string;
  category?: AssetCategory;
  location: string;
  condition?: AssetCondition;
  purchase_year: number;
  vendor?: string | null;
  status?: AssetStatus;
}

export interface AssetItemStatusUpdatePayload {
  status: AssetStatus;
}

export interface DepreciationRecord {
  id: number;
  tenant_id?: string | null;
  asset_code: string;
  depreciation_method: DepreciationMethod;
  original_value: number;
  current_value: number;
  depreciation_rate: number;
  status: DepreciationStatus;
}

export interface DepreciationListResponse {
  items: DepreciationRecord[];
}

export interface DepreciationItemResponse {
  item: DepreciationRecord;
}

export interface DepreciationRecordCreatePayload {
  asset_code: string;
  depreciation_method?: DepreciationMethod;
  original_value: number;
  current_value: number;
  depreciation_rate: number;
  status?: DepreciationStatus;
}
