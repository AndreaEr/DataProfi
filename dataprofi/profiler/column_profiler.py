from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

from dataprofi.core.config import Config
from dataprofi.core.types import (
    ColumnProfile,
    ColumnRole,
    EnhancedColumnProfile,
    CategoryStats,
    NumericInsight,
    DatetimeInsight,
)


def detect_distribution(series: pd.Series) -> str:
    if series.dtype.kind not in ("i", "f"):
        return "categorical"

    clean = series.dropna()
    if len(clean) < 10:
        return "insufficient_data"

    skewness = clean.skew()
    kurtosis = clean.kurtosis()

    if abs(skewness) < 0.5 and abs(kurtosis) < 1:
        return "normal"
    elif skewness > 1:
        return "right_skewed"
    elif skewness < -1:
        return "left_skewed"
    elif kurtosis > 3:
        return "heavy_tailed"
    elif abs(skewness) < 0.5:
        return "symmetric"
    else:
        return "moderate_skew"


def count_outliers(series: pd.Series, method: str = "iqr", threshold: float = 1.5) -> int:
    if series.dtype.kind not in ("i", "f"):
        return 0

    clean = series.dropna()
    if len(clean) < 4:
        return 0

    if method == "iqr":
        q1 = clean.quantile(0.25)
        q3 = clean.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - threshold * iqr
        upper = q3 + threshold * iqr
        return int(((clean < lower) | (clean > upper)).sum())
    elif method == "zscore":
        z_scores = np.abs((clean - clean.mean()) / clean.std())
        return int((z_scores > threshold).sum())

    return 0


def get_outlier_rows(
    df: pd.DataFrame, column: str, method: str = "iqr", threshold: float = 1.5, max_rows: int = 20
) -> dict:
    if column not in df.columns:
        return {"rows": [], "context": {}}
    series = df[column]
    if series.dtype.kind not in ("i", "f"):
        return {"rows": [], "context": {}}
    clean = series.dropna()
    if len(clean) < 4:
        return {"rows": [], "context": {}}

    q1 = float(clean.quantile(0.25))
    q3 = float(clean.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - threshold * iqr
    upper = q3 + threshold * iqr
    mean_val = float(clean.mean())

    if method == "iqr":
        mask = (series < lower) | (series > upper)
    else:
        full_z = np.abs((series - clean.mean()) / clean.std())
        mask = full_z > threshold

    context = {
        "normal_min": round(lower, 4),
        "normal_max": round(upper, 4),
        "mean": round(mean_val, 4),
        "q1": round(q1, 4),
        "q3": round(q3, 4),
        "method": f"IQR (values outside Q1-1.5*IQR to Q3+1.5*IQR)" if method == "iqr" else f"Z-score (> {threshold} std from mean)",
    }

    outlier_indices = series[mask].index.tolist()[:max_rows]
    rows = []
    for idx in outlier_indices:
        value = float(series.iloc[idx])
        distance = abs(value - mean_val)
        direction = "above" if value > upper else "below"
        reason = f"Value {value:.4g} is {direction} the normal range ({lower:.4g} to {upper:.4g}). It is {distance:.4g} away from the mean ({mean_val:.4g})."

        row_data = {"_row": int(idx), "_value": value, "_reason": reason}
        for col in df.columns[:6]:
            val = df[col].iloc[idx]
            row_data[col] = str(val) if pd.notna(val) else None
        rows.append(row_data)

    return {"rows": rows, "context": context}


def _format_row(df: pd.DataFrame, idx: int, context_cols: int = 6) -> dict:
    row_data: dict = {"_row": int(idx)}
    for col in df.columns[:context_cols]:
        val = df[col].iloc[idx]
        row_data[col] = str(val) if pd.notna(val) else None
    return row_data


def get_issue_rows(
    df: pd.DataFrame, column: str, issue_type: str = "all", max_rows: int = 50
) -> dict:
    if column not in df.columns:
        return {"issues": []}

    series = df[column]
    issues = []

    if issue_type in ("all", "missing"):
        missing_mask = series.isna()
        missing_count = int(missing_mask.sum())
        if missing_count > 0:
            indices = series[missing_mask].index.tolist()[:max_rows]
            issues.append({
                "type": "missing",
                "label": f"{missing_count} missing values",
                "count": missing_count,
                "rows": [_format_row(df, idx) for idx in indices],
            })

    if issue_type in ("all", "outliers") and series.dtype.kind in ("i", "f"):
        clean = series.dropna()
        if len(clean) >= 4:
            cfg = Config()
            q1 = clean.quantile(0.25)
            q3 = clean.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - cfg.outlier_threshold * iqr
            upper = q3 + cfg.outlier_threshold * iqr
            outlier_mask = (series < lower) | (series > upper)
            outlier_count = int(outlier_mask.sum())
            if outlier_count > 0:
                indices = series[outlier_mask].index.tolist()[:max_rows]
                rows = []
                for idx in indices:
                    row = _format_row(df, idx)
                    row["_value"] = str(series.iloc[idx])
                    rows.append(row)
                issues.append({
                    "type": "outliers",
                    "label": f"{outlier_count} outliers detected",
                    "count": outlier_count,
                    "rows": rows,
                })

    if issue_type in ("all", "duplicates"):
        dup_mask = df.duplicated(subset=[column], keep="first")
        dup_count = int(dup_mask.sum())
        if dup_count > 0:
            indices = df[dup_mask].index.tolist()[:max_rows]
            issues.append({
                "type": "duplicates",
                "label": f"{dup_count} duplicate values in this column",
                "count": dup_count,
                "rows": [_format_row(df, idx) for idx in indices],
            })

    return {"column": column, "issues": issues}


def classify_column_role(series: pd.Series) -> ColumnRole:
    non_null = series.dropna()
    total = len(series)
    unique_count = int(non_null.nunique())
    unique_ratio = unique_count / len(non_null) if len(non_null) > 0 else 0

    if series.dtype == bool or (unique_count <= 2 and len(non_null) > 0):
        return ColumnRole.BOOLEAN

    if pd.api.types.is_datetime64_any_dtype(series):
        return ColumnRole.DATETIME

    if series.dtype.kind == "O" and len(non_null) > 10:
        sample = non_null.head(min(100, len(non_null)))
        parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
        if parsed.notna().mean() > 0.8:
            return ColumnRole.DATETIME

    cfg = Config()
    if series.dtype.kind in ("i", "f"):
        if unique_ratio > cfg.id_unique_ratio and total > cfg.id_min_rows:
            return ColumnRole.ID
        if unique_count <= 2:
            return ColumnRole.BOOLEAN
        return ColumnRole.MEASURE

    if series.dtype.kind == "O":
        if unique_ratio > cfg.id_unique_ratio and total > cfg.id_min_rows:
            return ColumnRole.ID
        avg_len = non_null.astype(str).str.len().mean() if len(non_null) > 0 else 0
        if avg_len > cfg.free_text_min_length or unique_ratio > 0.8:
            return ColumnRole.FREE_TEXT
        return ColumnRole.CATEGORY

    return ColumnRole.MEASURE


def _build_category_stats(series: pd.Series) -> CategoryStats:
    non_null = series.dropna()
    if len(non_null) == 0:
        return CategoryStats()
    counts = non_null.value_counts().head(8)
    total = len(non_null)
    top_values = [{"value": str(v), "count": int(c)} for v, c in counts.items()]
    dominant_pct = round(counts.iloc[0] / total * 100, 1) if len(counts) > 0 else 0
    return CategoryStats(
        top_values=top_values,
        dominant_value_pct=dominant_pct,
        is_skewed=dominant_pct > 50,
    )


def _build_numeric_insight(series: pd.Series) -> NumericInsight:
    clean = series.dropna()
    if len(clean) == 0:
        return NumericInsight()
    dist = detect_distribution(series)
    interp_map = {
        "normal": "Normally distributed, standard parametric methods apply",
        "right_skewed": "Right-skewed, consider log transformation for modeling",
        "left_skewed": "Left-skewed, consider power transformation",
        "heavy_tailed": "Heavy-tailed, sensitive to outliers",
        "symmetric": "Symmetric distribution, well-behaved for most analyses",
        "moderate_skew": "Moderate skew, may benefit from normalization",
        "insufficient_data": "Too few values for reliable distribution analysis",
    }
    return NumericInsight(
        median=round(float(clean.median()), 4),
        range_value=round(float(clean.max() - clean.min()), 4),
        distribution_shape=dist,
        interpretation=interp_map.get(dist, ""),
        percentile_25=round(float(clean.quantile(0.25)), 4),
        percentile_75=round(float(clean.quantile(0.75)), 4),
    )


def _build_datetime_insight(series: pd.Series) -> DatetimeInsight:
    try:
        dt_series = pd.to_datetime(series, errors="coerce", format="mixed")
    except Exception:
        return DatetimeInsight()
    valid = dt_series.dropna().sort_values()
    if len(valid) < 2:
        return DatetimeInsight()
    diffs = valid.diff().dropna()
    if len(diffs) == 0:
        return DatetimeInsight(
            date_range_start=str(valid.iloc[0]),
            date_range_end=str(valid.iloc[-1]),
        )
    mode_diff = diffs.mode().iloc[0] if len(diffs.mode()) > 0 else diffs.median()
    total_seconds = mode_diff.total_seconds()
    if total_seconds < 7200:
        freq = "hourly"
    elif total_seconds < 172800:
        freq = "daily"
    elif total_seconds < 864000:
        freq = "weekly"
    elif total_seconds < 3888000:
        freq = "monthly"
    else:
        freq = "irregular"
    gap_count = int((diffs > mode_diff * 2).sum()) if mode_diff.total_seconds() > 0 else 0
    return DatetimeInsight(
        date_range_start=str(valid.iloc[0].date()),
        date_range_end=str(valid.iloc[-1].date()),
        frequency=freq,
        gap_count=gap_count,
    )


def _generate_insight(role: ColumnRole, series: pd.Series, profile: dict) -> str:
    non_null = series.dropna()
    total = len(series)
    null_pct = round((total - len(non_null)) / total * 100, 1) if total > 0 else 0

    if role == ColumnRole.ID:
        return f"Identifier column, {profile.get('completeness', 0):.0f}% complete with {profile.get('unique_count', 0)} unique values"
    elif role == ColumnRole.BOOLEAN:
        if len(non_null) > 0:
            true_count = non_null.astype(bool).sum()
            true_pct = round(true_count / len(non_null) * 100, 1)
            return f"Binary flag, {true_pct}% true, {null_pct}% missing"
        return "Binary flag column"
    elif role == ColumnRole.CATEGORY:
        unique = int(non_null.nunique())
        top_val = non_null.value_counts().index[0] if len(non_null) > 0 else "N/A"
        top_pct = round(non_null.value_counts().iloc[0] / len(non_null) * 100, 1) if len(non_null) > 0 else 0
        return f"{unique} categories, {top_pct}% are '{top_val}'"
    elif role == ColumnRole.MEASURE:
        dist = profile.get("distribution", "unknown")
        outliers = profile.get("outlier_count", 0)
        suffix = f", {outliers} outliers" if outliers > 0 else ""
        return f"{dist.replace('_', ' ').capitalize()} distribution (range {profile.get('min_value', '?')} to {profile.get('max_value', '?')}){suffix}"
    elif role == ColumnRole.DATETIME:
        dt_insight = _build_datetime_insight(series)
        if dt_insight.date_range_start:
            return f"{dt_insight.frequency.capitalize()} data spanning {dt_insight.date_range_start} to {dt_insight.date_range_end}"
        return "Temporal column"
    elif role == ColumnRole.FREE_TEXT:
        avg_len = round(non_null.astype(str).str.len().mean(), 0) if len(non_null) > 0 else 0
        return f"Free-form text, avg {int(avg_len)} chars, {null_pct}% missing"
    return ""


def _generate_anomaly_context(role: ColumnRole, issues: list[str]) -> list[str]:
    context = []
    for issue in issues:
        if "missing" in issue.lower():
            if role == ColumnRole.ID:
                context.append(f"{issue} - critical for an ID column, investigate data pipeline integrity")
            elif role == ColumnRole.CATEGORY:
                context.append(f"{issue} - may introduce bias in categorical analysis")
            elif role == ColumnRole.MEASURE:
                context.append(f"{issue} - consider imputation strategy before aggregation")
            elif role == ColumnRole.FREE_TEXT:
                context.append(f"{issue} - acceptable for text fields, low impact")
            else:
                context.append(issue)
        elif "outlier" in issue.lower():
            context.append(f"{issue} - verify these are real values, not data entry errors")
        elif "near-constant" in issue.lower():
            context.append(f"{issue} - provides no analytical value, consider dropping")
        elif "entirely null" in issue.lower():
            context.append(f"{issue} - column should be removed or data source investigated")
        else:
            context.append(issue)
    return context


def profile_column(series: pd.Series) -> ColumnProfile:
    total = len(series)
    null_count = int(series.isna().sum())
    non_null = series.dropna()
    unique_count = int(non_null.nunique())

    profile = ColumnProfile(
        name=series.name or "unnamed",
        dtype=str(series.dtype),
        total_count=total,
        null_count=null_count,
        unique_count=unique_count,
        completeness=round((total - null_count) / total * 100, 2) if total > 0 else 0,
        unique_ratio=round(unique_count / len(non_null), 4) if len(non_null) > 0 else 0,
    )

    if series.dtype.kind in ("i", "f"):
        profile.mean = round(float(non_null.mean()), 4)
        profile.std = round(float(non_null.std()), 4)
        profile.min_value = float(non_null.min())
        profile.max_value = float(non_null.max())
        profile.distribution = detect_distribution(series)
        profile.outlier_count = count_outliers(series)
    else:
        profile.min_value = str(non_null.min()) if len(non_null) > 0 else None
        profile.max_value = str(non_null.max()) if len(non_null) > 0 else None
        profile.distribution = "categorical"

    profile.sample_values = non_null.head(5).tolist()

    cfg = Config()
    issues = []
    if profile.completeness < 95:
        issues.append(f"{null_count} missing values ({100 - profile.completeness:.1f}% null)")
    if profile.outlier_count > 0:
        issues.append(f"{profile.outlier_count} outliers detected")
    if profile.unique_ratio == 1.0 and total > 100:
        issues.append("All values unique - possible ID column")
    if profile.unique_ratio < cfg.near_constant_ratio and total > 100:
        issues.append("Near-constant column - low information value")
    if null_count == total:
        issues.append("Column is entirely null")

    profile.quality_issues = issues
    return profile


def profile_column_enhanced(series: pd.Series) -> EnhancedColumnProfile:
    basic = profile_column(series)
    role = classify_column_role(series)

    profile_dict = {
        "completeness": basic.completeness,
        "unique_count": basic.unique_count,
        "distribution": basic.distribution,
        "outlier_count": basic.outlier_count,
        "min_value": basic.min_value,
        "max_value": basic.max_value,
    }

    category_stats = None
    numeric_insight = None
    datetime_insight = None

    if role == ColumnRole.CATEGORY:
        category_stats = _build_category_stats(series)
    elif role == ColumnRole.MEASURE:
        numeric_insight = _build_numeric_insight(series)
    elif role == ColumnRole.DATETIME:
        datetime_insight = _build_datetime_insight(series)
    elif role == ColumnRole.BOOLEAN:
        category_stats = _build_category_stats(series)

    insight = _generate_insight(role, series, profile_dict)
    anomaly_context = _generate_anomaly_context(role, basic.quality_issues)

    return EnhancedColumnProfile(
        name=basic.name,
        dtype=basic.dtype,
        role=role.value,
        total_count=basic.total_count,
        null_count=basic.null_count,
        unique_count=basic.unique_count,
        completeness=basic.completeness,
        unique_ratio=basic.unique_ratio,
        insight=insight,
        category_stats=category_stats,
        numeric_insight=numeric_insight,
        datetime_insight=datetime_insight,
        mean=basic.mean,
        std=basic.std,
        min_value=basic.min_value,
        max_value=basic.max_value,
        distribution=basic.distribution,
        outlier_count=basic.outlier_count,
        sample_values=basic.sample_values,
        quality_issues=basic.quality_issues,
        anomaly_context=anomaly_context,
    )


def profile_columns(df: pd.DataFrame) -> list[ColumnProfile]:
    return [profile_column(df[col]) for col in df.columns]


def profile_columns_enhanced(df: pd.DataFrame) -> list[EnhancedColumnProfile]:
    return [profile_column_enhanced(df[col]) for col in df.columns]
