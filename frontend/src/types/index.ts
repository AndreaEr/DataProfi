export interface DatasetInfo {
  id: string;
  name: string;
  rows: number;
  columns: number;
  column_names: string[];
}

export interface ColumnProfile {
  name: string;
  dtype: string;
  total_count: number;
  null_count: number;
  unique_count: number;
  completeness: number;
  unique_ratio: number;
  mean: number | null;
  std: number | null;
  min_value: string | null;
  max_value: string | null;
  distribution: string | null;
  outlier_count: number;
  quality_issues: string[];
}

export interface QualityScore {
  overall_score: number;
  dimension_scores: Record<string, number>;
  row_count: number;
  column_count: number;
  worst_columns: string[];
  suggested_fixes: Array<{
    column: string;
    dimension: string;
    issue: string;
  }>;
}

export interface IndexRecommendation {
  column: string;
  index_type: string;
  reason: string;
  explanation: string;
  sql: string;
  priority: string;
  estimated_impact: string;
}

export interface MLReadinessCheck {
  name: string;
  passed: boolean;
  severity: string;
  message: string;
  suggestion: string;
}

export interface MLReadiness {
  overall_ready: boolean;
  score: number;
  checks: MLReadinessCheck[];
  recommended_next_steps: string[];
}

export interface CleaningAction {
  column: string;
  issue: string;
  strategy: string;
  rows_affected: number;
  description: string;
}

export interface CleanResponse {
  actions: CleaningAction[];
  rows_before: number;
  rows_after: number;
  score_before: number;
  score_after: number;
}

// Enhanced column profile types

export interface CategoryStats {
  top_values: Array<{ value: string; count: number }>;
  dominant_value_pct: number;
  is_skewed: boolean;
}

export interface NumericInsight {
  median: number;
  range_value: number;
  distribution_shape: string;
  interpretation: string;
  percentile_25: number;
  percentile_75: number;
}

export interface DatetimeInsight {
  date_range_start: string;
  date_range_end: string;
  frequency: string;
  gap_count: number;
}

export interface EnhancedColumnProfile {
  name: string;
  dtype: string;
  role: string;
  total_count: number;
  null_count: number;
  unique_count: number;
  completeness: number;
  unique_ratio: number;
  insight: string;
  category_stats: CategoryStats | null;
  numeric_insight: NumericInsight | null;
  datetime_insight: DatetimeInsight | null;
  mean: number | null;
  std: number | null;
  min_value: string | null;
  max_value: string | null;
  distribution: string | null;
  outlier_count: number;
  quality_issues: string[];
  anomaly_context: string[];
}

// Timeseries types

export interface TimeseriesProfile {
  column: string;
  frequency: string;
  is_regular: boolean;
  gap_count: number;
  gap_locations: string[];
  trend: string;
  has_seasonality: boolean;
  seasonality_period: number | null;
  is_stationary: boolean;
  date_range_start: string;
  date_range_end: string;
  total_points: number;
}

export interface TimeseriesReport {
  datetime_columns: string[];
  profiles: TimeseriesProfile[];
}

// Correlation types

export interface CorrelationPair {
  column_a: string;
  column_b: string;
  correlation: number;
  method: string;
}

export interface FunctionalDependency {
  determinant: string;
  dependent: string;
  confidence: number;
}

export interface CorrelationReport {
  numeric_correlations: CorrelationPair[];
  categorical_associations: CorrelationPair[];
  functional_dependencies: FunctionalDependency[];
  redundant_columns: Array<[string, string, number]>;
  correlation_matrix: Record<string, Record<string, number>>;
}

// Detailed quality types

export interface ColumnImpact {
  column: string;
  role: string;
  issue: string;
  severity: string;
  suggested_fix: string;
  estimated_impact: string;
}

export interface QualityJustification {
  dimension: string;
  score: number;
  explanation: string;
  column_impacts: ColumnImpact[];
}

export interface DetailedQualityScore {
  overall_score: number;
  dimension_scores: Record<string, number>;
  justifications: QualityJustification[];
  row_count: number;
  column_count: number;
  worst_columns: string[];
  suggested_fixes: Array<{ column: string; dimension: string; issue: string }>;
}
