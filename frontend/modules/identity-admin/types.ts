export interface IdentityProvider {
  provider: string;
  type: string;
  enabled: boolean;
}

export interface DirectoryProvider {
  id: number;
  name: string;
  type: string;
  is_enabled: boolean;
}

export interface IdentityMapping {
  id: number;
  provider_id: number;
  external_group: string;
  platform_role: string;
}

export interface IdentityProvidersResponse {
  providers: IdentityProvider[];
}

export interface DirectoryProvidersResponse {
  providers: DirectoryProvider[];
}

export interface IdentityMappingsResponse {
  mappings: IdentityMapping[];
}

export interface CreateIdentityMappingPayload {
  provider_id: number;
  external_group: string;
  platform_role: string;
}
