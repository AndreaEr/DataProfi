from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from dataprofi.core.types import IndexType


@dataclass
class ColumnAnalysis:
    name: str
    dtype: str
    cardinality: int
    cardinality_ratio: float
    total_rows: int
    null_ratio: float
    is_sorted: bool
    is_numeric: bool
    is_text: bool
    is_array_or_json: bool
    is_likely_filter_column: bool = False
    avg_text_length: float | None = None
    recommended_index: IndexType | None = None
    priority: str = "low"


_FILTER_PATTERNS = {
    "id", "key", "code", "type", "status", "category",
    "date", "time", "created", "updated", "timestamp",
    "country", "region", "city", "state", "department",
    "user", "customer", "account", "order", "product",
}

_FILTER_SUFFIXES = {"_id", "_key", "_code", "_type", "_status", "_date", "_name"}
_FILTER_PREFIXES = {"id_", "is_", "has_"}


def _is_likely_filter_column(name: str, series: pd.Series, cardinality_ratio: float) -> bool:
    name_lower = name.lower()
    parts = set(name_lower.replace("-", "_").split("_"))
    if parts & _FILTER_PATTERNS:
        return True
    if any(name_lower.endswith(s) for s in _FILTER_SUFFIXES):
        return True
    if any(name_lower.startswith(p) for p in _FILTER_PREFIXES):
        return True
    if series.dtype.kind == "i" and cardinality_ratio > 0.9:
        return True
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    if series.dtype == "object" and cardinality_ratio < 0.05:
        return True
    return False


def analyze_column_for_index(series: pd.Series, total_rows: int) -> ColumnAnalysis:
    name = series.name or "unnamed"
    dtype = str(series.dtype)
    non_null = series.dropna()
    cardinality = int(non_null.nunique())
    cardinality_ratio = cardinality / total_rows if total_rows > 0 else 0
    null_ratio = series.isna().mean()

    is_numeric = series.dtype.kind in ("i", "f")
    is_text = series.dtype == "object" or pd.api.types.is_string_dtype(series)
    is_array_or_json = False

    avg_text_length = None
    if is_text and len(non_null) > 0:
        avg_text_length = non_null.str.len().mean()
        sample = non_null.head(100)
        if sample.str.startswith("[").any() or sample.str.startswith("{").any():
            is_array_or_json = True

    is_sorted = False
    if is_numeric and len(non_null) > 10:
        diffs = non_null.diff().dropna()
        is_sorted = (diffs >= 0).mean() > 0.95 or (diffs <= 0).mean() > 0.95

    is_filter = _is_likely_filter_column(name, series, cardinality_ratio)

    analysis = ColumnAnalysis(
        name=name,
        dtype=dtype,
        cardinality=cardinality,
        cardinality_ratio=cardinality_ratio,
        total_rows=total_rows,
        null_ratio=null_ratio,
        is_sorted=is_sorted,
        is_numeric=is_numeric,
        is_text=is_text,
        is_array_or_json=is_array_or_json,
        is_likely_filter_column=is_filter,
        avg_text_length=avg_text_length,
    )

    analysis.recommended_index, analysis.priority = _determine_index_type(analysis)
    return analysis


def _determine_index_type(analysis: ColumnAnalysis) -> tuple[IndexType | None, str]:
    if analysis.null_ratio > 0.95:
        return None, "low"

    if analysis.is_array_or_json:
        return IndexType.GIN, "high"

    if analysis.cardinality <= 1:
        return None, "low"

    if not analysis.is_likely_filter_column:
        return None, "low"

    if analysis.is_text and analysis.avg_text_length and analysis.avg_text_length > 100:
        return IndexType.GIN, "medium"

    if analysis.is_sorted and analysis.total_rows > 10000:
        return IndexType.BRIN, "high"

    if analysis.cardinality_ratio > 0.01 and analysis.cardinality > 10:
        if analysis.total_rows > 1000:
            return IndexType.BTREE, "high"
        else:
            return IndexType.BTREE, "medium"

    if analysis.cardinality_ratio < 0.05 and analysis.cardinality > 2:
        return IndexType.BTREE, "low"

    return None, "low"
