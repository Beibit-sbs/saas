export interface DeveloperApp {
  id: number;
  name: string;
  app_key: string;
  description: string;
  owner_email: string;
  status: "active" | "inactive";
  webhook_url?: string | null;
  scopes: string[];
  created_at: string;
  updated_at: string;
}

export interface DeveloperAppSecret extends DeveloperApp {
  app_secret: string;
}

export interface DeveloperInstallation {
  id: number;
  app_id: number;
  tenant_id: number;
  status: "active" | "disabled";
  installed_by: string;
  created_at: string;
}

export interface DeveloperApiLog {
  id: number;
  app_id: number;
  tenant_id: number;
  endpoint: string;
  status_code: number;
  latency_ms: number;
  created_at: string;
}

export interface DeveloperAppCreateRequest {
  name: string;
  description: string;
  owner_email: string;
  scopes: string[];
  webhook_url?: string;
}