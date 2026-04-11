/** Map of role name -> list of permissions */
export type RolesMap = Record<string, string[]>;

export interface RolesResponse {
  roles: RolesMap;
}

export interface RoleAssignment {
  user_id: string;
  role: string;
  tenant_id?: number;
}

export interface AssignmentsResponse {
  assignments: RoleAssignment[];
}

export interface UpsertRolePayload {
  name: string;
  permissions: string[];
  tenant_id?: number;
}

export interface AssignRolePayload {
  user_id: string;
  role: string;
  tenant_id?: number;
}
