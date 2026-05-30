from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class QualityDimension(Enum):
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    UNIQUENESS = "uniqueness"
    VALIDITY = "validity"
    TIMELINESS = "timeliness"


class IndexType(Enum):
    BTREE = "btree"
    GIN = "gin"
    GIST = "gist"
    BRIN = "brin"
    HASH = "hash"


class CleaningStrategy(Enum):
    DROP = "drop"
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"
    FORWARD_FILL = "forward_fill"
    CONSTANT = "constant"
    ML_IMPUTE = "ml_impute"


class OutlierMethod(Enum):
    IQR = "iqr"
    ZSCORE = "zscore"
    ISOLATION_FOREST = "isolation_forest"


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    total_count: int
    null_count: int
    unique_count: int
    completeness: float
    unique_ratio: float
    mean: float | None = None
    std: float | None = None
    min_value: float | str | None = None
    max_value: float | str | None = None
    distribution: str | None = None
    outlier_count: int = 0
    sample_values: list = field(default_factory=list)
    quality_issues: list[str] = field(default_factory=list)


@dataclass
class QualityScore:
    dimension: QualityDimension
    score: float  # 0-100
    details: str = ""
    issues: list[str] = field(default_factory=list)


@dataclass
class QualityReport:
    overall_score: float
    dimension_scores: dict[str, float] = field(default_factory=dict)
    column_profiles: list[ColumnProfile] = field(default_factory=list)
    worst_columns: list[str] = field(default_factory=list)
    suggested_fixes: list[dict] = field(default_factory=list)
    row_count: int = 0
    column_count: int = 0


@dataclass
class IndexRecommendation:
    column: str
    index_type: IndexType
    reason: str
    explanation: str
    sql: str
    priority: str = "medium"  # high, medium, low
    estimated_impact: str = ""


@dataclass
class CleaningAction:
    column: str
    issue: str
    strategy: str
    rows_affected: int
    description: str


@dataclass
class CleaningReport:
    actions: list[CleaningAction] = field(default_factory=list)
    rows_before: int = 0
    rows_after: int = 0
    score_before: float = 0.0
    score_after: float = 0.0


@dataclass
class MLReadinessCheck:
    name: str
    passed: bool
    severity: str  # "critical", "warning", "info"
    message: str
    suggestion: str = ""


@dataclass
class MLReadinessReport:
    overall_ready: bool
    score: float
    checks: list[MLReadinessCheck] = field(default_factory=list)
    recommended_next_steps: list[str] = field(default_factory=list)


class ColumnRole(Enum):
    ID = "id"
    CATEGORY = "category"
    MEASURE = "measure"
    DATETIME = "datetime"
    FREE_TEXT = "free_text"
    BOOLEAN = "boolean"


@dataclass
class CategoryStats:
    top_values: list[dict] = field(default_factory=list)
    dominant_value_pct: float = 0.0
    is_skewed: bool = False


@dataclass
class NumericInsight:
    median: float = 0.0
    range_value: float = 0.0
    distribution_shape: str = ""
    interpretation: str = ""
    percentile_25: float = 0.0
    percentile_75: float = 0.0


@dataclass
class DatetimeInsight:
    date_range_start: str = ""
    date_range_end: str = ""
    frequency: str = ""
    gap_count: int = 0


@dataclass
class EnhancedColumnProfile:
    name: str
    dtype: str
    role: str
    total_count: int
    null_count: int
    unique_count: int
    completeness: float
    unique_ratio: float
    insight: str = ""
    category_stats: CategoryStats | None = None
    numeric_insight: NumericInsight | None = None
    datetime_insight: DatetimeInsight | None = None
    mean: float | None = None
    std: float | None = None
    min_value: float | str | None = None
    max_value: float | str | None = None
    distribution: str | None = None
    outlier_count: int = 0
    sample_values: list = field(default_factory=list)
    quality_issues: list[str] = field(default_factory=list)
    anomaly_context: list[str] = field(default_factory=list)


@dataclass
class TimeseriesProfile:
    column: str
    frequency: str
    is_regular: bool
    gap_count: int
    gap_locations: list[str] = field(default_factory=list)
    trend: str = "flat"
    has_seasonality: bool = False
    seasonality_period: int | None = None
    is_stationary: bool = True
    date_range_start: str = ""
    date_range_end: str = ""
    total_points: int = 0


@dataclass
class TimeseriesReport:
    datetime_columns: list[str] = field(default_factory=list)
    profiles: list[TimeseriesProfile] = field(default_factory=list)


@dataclass
class CorrelationPair:
    column_a: str
    column_b: str
    correlation: float
    method: str


@dataclass
class FunctionalDependency:
    determinant: str
    dependent: str
    confidence: float


@dataclass
class CorrelationReport:
    numeric_correlations: list[CorrelationPair] = field(default_factory=list)
    categorical_associations: list[CorrelationPair] = field(default_factory=list)
    functional_dependencies: list[FunctionalDependency] = field(default_factory=list)
    redundant_columns: list[list] = field(default_factory=list)
    correlation_matrix: dict[str, dict[str, float]] = field(default_factory=dict)


@dataclass
class ColumnImpact:
    column: str
    role: str
    issue: str
    severity: str
    suggested_fix: str
    estimated_impact: str


@dataclass
class QualityJustification:
    dimension: str
    score: float
    explanation: str
    column_impacts: list[ColumnImpact] = field(default_factory=list)


@dataclass
class DetailedQualityReport:
    overall_score: float
    dimension_scores: dict[str, float] = field(default_factory=dict)
    justifications: list[QualityJustification] = field(default_factory=list)
    row_count: int = 0
    column_count: int = 0
    worst_columns: list[str] = field(default_factory=list)
    suggested_fixes: list[dict] = field(default_factory=list)


@dataclass
class GeoColumnProfile:
    column_lat: str
    column_lng: str
    total_points: int
    valid_points: int
    invalid_count: int
    invalid_reasons: list[str] = field(default_factory=list)
    centroid_lat: float = 0.0
    centroid_lng: float = 0.0
    bounding_box: dict = field(default_factory=dict)
    spatial_spread_km: float = 0.0
    density_points_per_sq_km: float = 0.0
    outlier_count: int = 0
    outlier_indices: list[int] = field(default_factory=list)
    outlier_details: list[dict] = field(default_factory=list)
    cluster_count: int = 0
    clusters: list[dict] = field(default_factory=list)


@dataclass
class GeoReport:
    detected_pairs: list[tuple] = field(default_factory=list)
    profiles: list[GeoColumnProfile] = field(default_factory=list)
