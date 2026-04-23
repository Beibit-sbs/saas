/**
 * Teaching Quality Analytics Module — TypeScript Types
 * Defines data models for teaching performance KPIs and quality metrics
 */

export interface TeachingQualityKPI {
  faculty_id: string;
  faculty_name: string;
  department: string;
  term_id: string;
  student_satisfaction_score: number; // 1-5
  course_completion_rate_pct: number;
  student_learning_gain_pct: number;
  peer_review_score: number; // 1-5
  instructional_innovation_score: number; // 1-5
  overall_quality_score: number; // 1-5 weighted average
  trend_direction: 'improving' | 'stable' | 'declining';
  last_updated: string;
}

export interface QualityMetricPayload {
  metric_type: 'satisfaction' | 'completion' | 'learning_gain' | 'peer_review' | 'innovation';
  value: number;
  measurement_period: string;
}

export interface QualityDashboardSummary {
  department: string;
  term_id: string;
  total_faculty: number;
  average_quality_score: number;
  above_target_count: number;
  below_target_count: number;
  improvement_opportunities: string[];
  last_aggregated: string;
}

export interface QualityBenchmark {
  metric_name: string;
  institutional_average: number;
  departmental_average: number;
  top_quartile: number;
  bottom_quartile: number;
  target_value: number;
}

export interface QualityMetricsReport {
  term_id: string;
  report_generated_at: string;
  total_faculty_evaluated: number;
  average_quality_score: number;
  benchmarks: QualityBenchmark[];
  departments: QualityDashboardSummary[];
  trending_metrics: {
    metric_name: string;
    trend: 'up' | 'down' | 'stable';
    change_pct: number;
  }[];
}

export interface QualityImprovement {
  faculty_id: string;
  improvement_area: string;
  recommended_action: string;
  priority: 'high' | 'medium' | 'low';
  estimated_timeline_weeks: number;
  success_metric: string;
}
