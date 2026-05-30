from __future__ import annotations

from pydantic import BaseModel


class ApiLoadRequest(BaseModel):
    url: str
    record_path: str | None = None
    limit: int = 5000


class CleaningStepRequest(BaseModel):
    step_type: str
    strategy: str | None = None
    method: str | None = None
    action: str | None = None
    columns: list[str] | None = None
    threshold: float | None = None


class CleanRequest(BaseModel):
    steps: list[CleaningStepRequest]


class ColumnProfileResponse(BaseModel):
    name: str
    dtype: str
    total_count: int
    null_count: int
    unique_count: int
    completeness: float
    unique_ratio: float
    mean: float | None = None
    std: float | None = None
    min_value: str | None = None
    max_value: str | None = None
    distribution: str | None = None
    outlier_count: int = 0
    quality_issues: list[str] = []


class QualityScoreResponse(BaseModel):
    overall_score: float
    dimension_scores: dict[str, float]
    row_count: int
    column_count: int
    worst_columns: list[str]
    suggested_fixes: list[dict]


class IndexRecommendationResponse(BaseModel):
    column: str
    index_type: str
    reason: str
    explanation: str
    sql: str
    priority: str
    estimated_impact: str


class MLReadinessCheckResponse(BaseModel):
    name: str
    passed: bool
    severity: str
    message: str
    suggestion: str = ""


class MLReadinessResponse(BaseModel):
    overall_ready: bool
    score: float
    checks: list[MLReadinessCheckResponse]
    recommended_next_steps: list[str]


class CleaningActionResponse(BaseModel):
    column: str
    issue: str
    strategy: str
    rows_affected: int
    description: str


class CleanResponse(BaseModel):
    actions: list[CleaningActionResponse]
    rows_before: int
    rows_after: int
    score_before: float
    score_after: float


class DatasetInfo(BaseModel):
    id: str
    name: str
    rows: int
    columns: int
    column_names: list[str]


# Enhanced column profile responses

class CategoryStatsResponse(BaseModel):
    top_values: list[dict] = []
    dominant_value_pct: float = 0.0
    is_skewed: bool = False


class NumericInsightResponse(BaseModel):
    median: float = 0.0
    range_value: float = 0.0
    distribution_shape: str = ""
    interpretation: str = ""
    percentile_25: float = 0.0
    percentile_75: float = 0.0


class DatetimeInsightResponse(BaseModel):
    date_range_start: str = ""
    date_range_end: str = ""
    frequency: str = ""
    gap_count: int = 0


class EnhancedColumnProfileResponse(BaseModel):
    name: str
    dtype: str
    role: str
    total_count: int
    null_count: int
    unique_count: int
    completeness: float
    unique_ratio: float
    insight: str = ""
    category_stats: CategoryStatsResponse | None = None
    numeric_insight: NumericInsightResponse | None = None
    datetime_insight: DatetimeInsightResponse | None = None
    mean: float | None = None
    std: float | None = None
    min_value: str | None = None
    max_value: str | None = None
    distribution: str | None = None
    outlier_count: int = 0
    quality_issues: list[str] = []
    anomaly_context: list[str] = []


# Timeseries responses

class TimeseriesProfileResponse(BaseModel):
    column: str
    frequency: str
    is_regular: bool
    gap_count: int
    gap_locations: list[str] = []
    trend: str = "flat"
    has_seasonality: bool = False
    seasonality_period: int | None = None
    is_stationary: bool = True
    date_range_start: str = ""
    date_range_end: str = ""
    total_points: int = 0


class TimeseriesReportResponse(BaseModel):
    datetime_columns: list[str] = []
    profiles: list[TimeseriesProfileResponse] = []


# Correlation responses

class CorrelationPairResponse(BaseModel):
    column_a: str
    column_b: str
    correlation: float
    method: str


class FunctionalDependencyResponse(BaseModel):
    determinant: str
    dependent: str
    confidence: float


class CorrelationReportResponse(BaseModel):
    numeric_correlations: list[CorrelationPairResponse] = []
    categorical_associations: list[CorrelationPairResponse] = []
    functional_dependencies: list[FunctionalDependencyResponse] = []
    redundant_columns: list[list] = []
    correlation_matrix: dict[str, dict[str, float]] = {}


# Detailed quality score responses

class ColumnImpactResponse(BaseModel):
    column: str
    role: str
    issue: str
    severity: str
    suggested_fix: str
    estimated_impact: str


class QualityJustificationResponse(BaseModel):
    dimension: str
    score: float
    explanation: str
    column_impacts: list[ColumnImpactResponse] = []


class DetailedQualityScoreResponse(BaseModel):
    overall_score: float
    dimension_scores: dict[str, float]
    justifications: list[QualityJustificationResponse] = []
    row_count: int
    column_count: int
    worst_columns: list[str] = []
    suggested_fixes: list[dict] = []
