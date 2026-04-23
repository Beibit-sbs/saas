/**
 * Contracts & Legal Repository Types
 * Defines interfaces for contract registry, workflow status, and legal search
 */

export enum ContractStatus {
  DRAFT = 'draft',
  IN_REVIEW = 'in_review',
  APPROVED = 'approved',
  ACTIVE = 'active',
  EXPIRING = 'expiring',
  EXPIRED = 'expired',
  TERMINATED = 'terminated',
}

export enum ContractType {
  VENDOR = 'vendor',
  SERVICE = 'service',
  EMPLOYMENT = 'employment',
  PARTNERSHIP = 'partnership',
  LEASE = 'lease',
  GRANT = 'grant',
  OTHER = 'other',
}

export enum RiskLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

export interface ContractParty {
  party_id: string;
  legal_name: string;
  registration_number?: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
}

export interface ContractMetadata {
  contract_id: string;
  contract_number: string;
  title: string;
  type: ContractType;
  status: ContractStatus;
  owner_id: string;
  owner_name: string;
  department_id: string;
  department_name: string;
  start_date: string;
  end_date: string;
  value_amount?: number;
  currency?: string;
  risk_level: RiskLevel;
  created_at: string;
  updated_at: string;
}

export interface ContractClause {
  clause_id: string;
  contract_id: string;
  section: string;
  title: string;
  content: string;
  mandatory: boolean;
}

export interface ContractVersion {
  version_id: string;
  contract_id: string;
  version_number: number;
  change_summary: string;
  created_by: string;
  created_at: string;
}

export interface ContractWorkflowStep {
  step_id: string;
  contract_id: string;
  sequence: number;
  role: string;
  approver_id?: string;
  status: 'pending' | 'approved' | 'rejected' | 'skipped';
  decided_at?: string;
  comment?: string;
}

export interface ContractAuditEntry {
  audit_id: string;
  contract_id: string;
  action: string;
  actor_id: string;
  actor_name: string;
  from_status?: ContractStatus;
  to_status?: ContractStatus;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface ContractDashboardSummary {
  total_contracts: number;
  status_breakdown: {
    draft: number;
    in_review: number;
    approved: number;
    active: number;
    expiring: number;
    expired: number;
    terminated: number;
  };
  expiring_30_days: number;
  high_risk_count: number;
  total_active_value: number;
  last_updated: string;
}

export interface ContractListItem {
  contract_id: string;
  contract_number: string;
  title: string;
  type: ContractType;
  status: ContractStatus;
  owner_name: string;
  counterparty: string;
  end_date: string;
  risk_level: RiskLevel;
  updated_at: string;
}

export interface ContractSearchResult {
  contract_id: string;
  contract_number: string;
  title: string;
  matched_fields: string[];
  snippet?: string;
  score: number;
}

export interface ContractCreatePayload {
  title: string;
  type: ContractType;
  department_id: string;
  owner_id: string;
  start_date: string;
  end_date: string;
  value_amount?: number;
  currency?: string;
  risk_level: RiskLevel;
  party: ContractParty;
}

export interface ContractUpdatePayload {
  title?: string;
  status?: ContractStatus;
  end_date?: string;
  value_amount?: number;
  risk_level?: RiskLevel;
}

export interface ContractStatusUpdatePayload {
  status: ContractStatus;
  comment?: string;
}
