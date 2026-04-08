export interface ServiceAccount {
  account_id: string;
  name: string;
  permissions: string[];
  platform_global: boolean;
  revoked: boolean;
  tenant_id: number;
  created_at?: string;
}

export interface ServiceAccountsResponse {
  accounts: ServiceAccount[];
}

export interface CreateServiceAccountPayload {
  name: string;
  permissions: string[];
  platform_global?: boolean;
}

export interface IssueTokenPayload {
  secret: string;
}

export interface IssueTokenResponse {
  token: string;
}
