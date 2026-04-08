export interface Tenant {
  id: string;
  slug: string;
  display_name: string;
  plan: string;
  status: "active" | "inactive" | "suspended" | "trial" | "archived";
  max_students: number;
  current_students: number;
  created_at: string;
  updated_at: string;
}

export interface CreateTenantPayload {
  slug: string;
  display_name: string;
  plan: string;
  max_students: number;
}

export interface UpdateTenantPayload {
  display_name?: string;
  plan?: string;
  status?: Tenant["status"];
  max_students?: number;
}
