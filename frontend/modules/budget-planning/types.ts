/**
 * Budget Planning & Controls Types
 * Defines interfaces for budget entities, variance analysis, and fiscal controls
 */

export enum BudgetStatus {
  DRAFT = 'draft',
  SUBMITTED = 'submitted',
  APPROVED = 'approved',
  ACTIVE = 'active',
  CLOSED = 'closed',
  ARCHIVED = 'archived',
}

export enum VarianceType {
  FAVORABLE = 'favorable',
  UNFAVORABLE = 'unfavorable',
  NEUTRAL = 'neutral',
}

export enum BudgetCategory {
  PERSONNEL = 'personnel',
  OPERATIONS = 'operations',
  CAPITAL = 'capital',
  SUPPLIES = 'supplies',
  TRAVEL = 'travel',
  TECHNOLOGY = 'technology',
  RESEARCH = 'research',
  OTHER = 'other',
}

export interface FiscalYear {
  fiscal_year_id: string;
  year: number;
  start_date: string;
  end_date: string;
  is_active: boolean;
  created_at: string;
}

export interface CostCenter {
  cost_center_id: string;
  cost_center_code: string;
  name: string;
  department_id: string;
  manager_id: string;
  budget_limit?: number;
  created_at: string;
}

export interface BudgetMetadata {
  budget_id: string;
  fiscal_year_id: string;
  cost_center_id: string;
  category: BudgetCategory;
  status: BudgetStatus;
  created_by: string;
  created_at: string;
  updated_at: string;
  submitted_at?: string;
  approved_at?: string;
  approved_by?: string;
}

export interface BudgetLine {
  line_id: string;
  budget_id: string;
  line_number: number;
  description: string;
  budgeted_amount: number;
  spent_amount: number;
  committed_amount: number;
  available_amount: number;
  category?: string;
  created_at: string;
}

export interface BudgetAllocation {
  allocation_id: string;
  budget_id: string;
  cost_center_id: string;
  allocated_amount: number;
  percentage: number;
  created_at: string;
}

export interface Expense {
  expense_id: string;
  budget_id: string;
  cost_center_id: string;
  date: string;
  description: string;
  amount: number;
  category: BudgetCategory;
  vendor?: string;
  receipt_reference?: string;
  status: 'pending' | 'approved' | 'rejected' | 'posted';
  created_by: string;
  created_at: string;
}

export interface VarianceAnalysis {
  variance_id: string;
  budget_id: string;
  line_id?: string;
  budgeted_amount: number;
  actual_amount: number;
  variance_amount: number;
  variance_percentage: number;
  variance_type: VarianceType;
  analysis_date: string;
  notes?: string;
  created_at: string;
}

export interface BudgetSummary {
  budget_id: string;
  fiscal_year: number;
  cost_center_name: string;
  total_budgeted: number;
  total_spent: number;
  total_committed: number;
  total_available: number;
  spend_percentage: number;
  forecast_variance?: number;
  status: BudgetStatus;
  updated_at: string;
}

export interface BudgetDashboardSummary {
  total_budgets: number;
  status_breakdown: {
    draft: number;
    submitted: number;
    approved: number;
    active: number;
    closed: number;
  };
  total_allocated: number;
  total_spent: number;
  total_available: number;
  spend_percentage: number;
  variance_count: number;
  unfavorable_variances: number;
  last_updated: string;
}

export interface BudgetListItem {
  budget_id: string;
  fiscal_year: number;
  cost_center_name: string;
  category: BudgetCategory;
  total_budgeted: number;
  total_spent: number;
  spend_percentage: number;
  status: BudgetStatus;
  updated_at: string;
}

export interface BudgetCreatePayload {
  fiscal_year_id: string;
  cost_center_id: string;
  category: BudgetCategory;
  total_amount: number;
}

export interface BudgetUpdatePayload {
  total_amount?: number;
  status?: BudgetStatus;
}

export interface BudgetLineCreatePayload {
  budget_id: string;
  description: string;
  budgeted_amount: number;
  category?: string;
}

export interface ExpenseCreatePayload {
  budget_id: string;
  cost_center_id: string;
  date: string;
  description: string;
  amount: number;
  category: BudgetCategory;
  vendor?: string;
  receipt_reference?: string;
}

export interface VarianceThreshold {
  threshold_id: string;
  percentage: number;
  alert_level: 'warning' | 'critical';
}

export interface BudgetApprovalRequest {
  request_id: string;
  budget_id: string;
  submitted_by: string;
  submitted_at: string;
  approver_id: string;
  status: 'pending' | 'approved' | 'rejected';
  approved_at?: string;
  rejection_reason?: string;
}
