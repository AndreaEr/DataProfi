from dataclasses import dataclass, field


@dataclass
class Config:
    cache_dir: str = ".dataprofi_cache"
    default_db_url: str = "postgresql://localhost:5432/dataprofi"

    # Outlier detection
    outlier_method: str = "iqr"
    outlier_threshold: float = 1.5

    # Column classification
    id_unique_ratio: float = 0.95
    id_min_rows: int = 50
    category_max_cardinality: int = 50
    free_text_min_length: float = 50.0
    near_constant_ratio: float = 0.01

    # Cleaning
    fuzzy_match_threshold: int = 85

    # Correlation
    correlation_notable_threshold: float = 0.3
    correlation_redundant_threshold: float = 0.95
    functional_dependency_confidence: float = 0.95

    # Geo/Spatial
    spatial_outlier_std: float = 3.0

    # API loader
    max_rows: int = 50_000
    max_response_mb: int = 50
    api_timeout_seconds: int = 30

    # Quality scoring weights
    quality_weights: dict = field(default_factory=lambda: {
        "completeness": 0.25,
        "consistency": 0.20,
        "uniqueness": 0.20,
        "validity": 0.20,
        "timeliness": 0.15,
    })
