export type OrgUnitType =
  | "university"
  | "school"
  | "faculty"
  | "department"
  | "umo"
  | "registrar_office"
  | "deans_office"
  | "advisory_unit"
  | "academic_committee"
  | "academic_commission";

export interface OrgUnit {
  id: number;
  tenant_id: number;
  name: string;
  code: string;
  unit_type: OrgUnitType;
  parent_unit_id: number | null;
  active: boolean;
  head_person_id: number | null;
  email: string | null;
  phone: string | null;
  location: string | null;
  created_at: string;
  updated_at: string;
}

export interface OrgUnitTreeNode {
  id: number;
  name: string;
  code: string;
  unit_type: OrgUnitType;
  active: boolean;
  children: OrgUnitTreeNode[];
}

export interface CreateOrgUnitPayload {
  name: string;
  code: string;
  unit_type: OrgUnitType;
  parent_unit_id?: number | null;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
}

export interface UpdateOrgUnitPayload {
  name?: string;
  code?: string;
  unit_type?: OrgUnitType;
  parent_unit_id?: number | null;
  active?: boolean;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
}
