from __future__ import annotations

import numpy as np
import pandas as pd

from dataprofi.core.types import TimeseriesProfile, TimeseriesReport


def _detect_datetime_columns(df: pd.DataFrame) -> list[str]:
    dt_cols = []
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            dt_cols.append(col)
            continue
        if df[col].dtype.kind == "O":
            sample = df[col].dropna().head(50)
            if len(sample) == 0:
                continue
            parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
            if parsed.notna().mean() > 0.8:
                dt_cols.append(col)
    return dt_cols


def _infer_frequency(diffs: pd.Series) -> tuple[str, pd.Timedelta]:
    if len(diffs) == 0:
        return "irregular", pd.Timedelta(0)
    mode_vals = diffs.mode()
    mode_diff = mode_vals.iloc[0] if len(mode_vals) > 0 else diffs.median()
    seconds = mode_diff.total_seconds()
    if seconds < 7200:
        return "hourly", mode_diff
    elif seconds < 172800:
        return "daily", mode_diff
    elif seconds < 864000:
        return "weekly", mode_diff
    elif seconds < 3888000:
        return "monthly", mode_diff
    else:
        return "irregular", mode_diff


def _detect_trend(values: pd.Series) -> str:
    clean = values.dropna()
    if len(clean) < 10:
        return "flat"
    first_half = clean.iloc[: len(clean) // 2].mean()
    second_half = clean.iloc[len(clean) // 2 :].mean()
    if second_half == 0 and first_half == 0:
        return "flat"
    pct_change = (second_half - first_half) / (abs(first_half) + 1e-10)
    if pct_change > 0.1:
        return "increasing"
    elif pct_change < -0.1:
        return "decreasing"
    return "flat"


def _detect_seasonality(values: pd.Series) -> tuple[bool, int | None]:
    clean = values.dropna().values
    if len(clean) < 30:
        return False, None
    clean = (clean - clean.mean()) / (clean.std() + 1e-10)
    best_lag = None
    best_corr = 0.0
    for lag in [7, 12, 14, 24, 28, 30, 52, 60, 90, 365]:
        if lag >= len(clean) // 2:
            continue
        corr = np.corrcoef(clean[:-lag], clean[lag:])[0, 1]
        if not np.isnan(corr) and abs(corr) > best_corr:
            best_corr = abs(corr)
            best_lag = lag
    if best_corr > 0.4 and best_lag is not None:
        return True, best_lag
    return False, None


def _check_stationarity(values: pd.Series) -> bool:
    clean = values.dropna().values
    if len(clean) < 30:
        return True
    n = len(clean)
    chunk_size = n // 3
    chunks = [clean[i * chunk_size : (i + 1) * chunk_size] for i in range(3)]
    variances = [c.var() for c in chunks if len(c) > 0]
    if min(variances) == 0:
        return True
    ratio = max(variances) / (min(variances) + 1e-10)
    return ratio < 2.0


def _profile_single_column(df: pd.DataFrame, col: str) -> TimeseriesProfile:
    try:
        dt_series = pd.to_datetime(df[col], errors="coerce", format="mixed")
    except Exception:
        dt_series = pd.to_datetime(df[col], errors="coerce")
    valid = dt_series.dropna().sort_values().reset_index(drop=True)

    if len(valid) < 2:
        return TimeseriesProfile(
            column=col,
            frequency="insufficient_data",
            is_regular=False,
            gap_count=0,
            total_points=len(valid),
        )

    diffs = valid.diff().dropna()
    frequency, mode_diff = _infer_frequency(diffs)
    is_regular = (diffs == mode_diff).mean() > 0.9 if mode_diff.total_seconds() > 0 else False

    gap_mask = diffs > mode_diff * 2 if mode_diff.total_seconds() > 0 else pd.Series(dtype=bool)
    gap_count = int(gap_mask.sum())
    gap_locations = []
    if gap_count > 0:
        gap_indices = gap_mask[gap_mask].index[:10]
        gap_locations = [str(valid.iloc[i].date()) for i in gap_indices if i < len(valid)]

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    trend = "flat"
    has_seasonality = False
    seasonality_period = None
    is_stationary = True

    if len(numeric_cols) > 0:
        sorted_df = df.loc[valid.index]
        first_numeric = sorted_df[numeric_cols[0]].dropna()
        if len(first_numeric) >= 10:
            trend = _detect_trend(first_numeric)
            has_seasonality, seasonality_period = _detect_seasonality(first_numeric)
            is_stationary = _check_stationarity(first_numeric)

    return TimeseriesProfile(
        column=col,
        frequency=frequency,
        is_regular=is_regular,
        gap_count=gap_count,
        gap_locations=gap_locations,
        trend=trend,
        has_seasonality=has_seasonality,
        seasonality_period=seasonality_period,
        is_stationary=is_stationary,
        date_range_start=str(valid.iloc[0].date()),
        date_range_end=str(valid.iloc[-1].date()),
        total_points=len(valid),
    )


def profile_timeseries(df: pd.DataFrame) -> TimeseriesReport:
    dt_cols = _detect_datetime_columns(df)
    if not dt_cols:
        return TimeseriesReport()
    profiles = [_profile_single_column(df, col) for col in dt_cols]
    return TimeseriesReport(datetime_columns=dt_cols, profiles=profiles)
