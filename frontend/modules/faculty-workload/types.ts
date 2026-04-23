/**
 * Faculty Workload Planning Module — TypeScript Types
 * Defines all data models for workload calculations, capacity management, and alerts
 */

export interface FacultyWorkloadData {
  faculty_id: string;
  faculty_name: string;
  department: string;
  term_id: string;
  primary_credit_hours: number;
  assistant_credit_hours: number;
  total_credit_hours: number;
  max_credit_hours: number;
  fte_ratio: number;
  utilization_pct: number;
  underload_alert: boolean;
  max_credit_exceeded: boolean;
  overload_threshold: boolean;
  updated_at: string;
}

export interface FacultyCapacityPayload {
  max_credit_hours: number;
  fte_ratio: number;
}

export interface FacultyCapacityReadSchema {
  faculty_id: string;
  max_credit_hours: number;
  fte_ratio: number;
  updated_at: string;
}

export interface WorkloadAlert {
  faculty_id: string;
  faculty_name: string;
  department: string;
  term_id: string;
  alert_type: 'underload' | 'overload' | 'max_credit_exceeded';
  total_credit_hours: number;
  threshold_value: number;
  severity: 'low' | 'medium' | 'high';
  created_at: string;
}

export interface DepartmentWorkloadSummary {
  department: string;
  term_id: string;
  total_faculty: number;
  average_utilization_pct: number;
  underload_count: number;
  overload_count: number;
  max_credit_exceeded_count: number;
  fairness_score: number;
  last_updated: string;
}

export interface WorkloadMetrics {
  term_id: string;
  total_faculty: number;
  average_utilization_pct: number;
  median_utilization_pct: number;
  min_utilization_pct: number;
  max_utilization_pct: number;
  utilization_std_dev: number;
  alert_count_by_type: {
    underload: number;
    overload: number;
    max_credit_exceeded: number;
  };
  departments: DepartmentWorkloadSummary[];
}
