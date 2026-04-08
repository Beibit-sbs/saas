export interface LdapStatus {
  enabled: boolean;
  host?: string | null;
  port?: number | null;
  base_dn?: string | null;
  bind_dn?: string | null;
  user_filter?: string | null;
  group_attribute?: string | null;
  display_name_attribute?: string | null;
  login_attribute?: string | null;
  timeout_seconds?: number | null;
  role_map?: Record<string, string> | null;
  default_role?: string | null;
}

export interface LdapStatusResponse {
  ldap: LdapStatus;
}

export interface LdapTestPayload {
  username?: string;
  password?: string;
}

export interface LdapTestResult {
  status?: string;
  message?: string;
  [key: string]: unknown;
}

export interface LdapTestResponse {
  result: LdapTestResult;
}
