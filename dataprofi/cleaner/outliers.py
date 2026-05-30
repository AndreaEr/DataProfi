from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from dataprofi.core.types import CleaningAction


def handle_outliers(
    df: pd.DataFrame,
    method: str = "iqr",
    action: str = "clip",
    columns: list[str] | None = None,
    threshold: float = 1.5,
) -> tuple[pd.DataFrame, list[CleaningAction]]:
    df = df.copy()
    actions = []
    target_cols = columns or df.select_dtypes(include=[np.number]).columns.tolist()

    for col in target_cols:
        if col not in df.columns or df[col].dtype.kind not in ("i", "f"):
            continue

        series = df[col].dropna()
        if len(series) < 10:
            continue

        if method == "iqr":
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr
            outlier_mask = (df[col] < lower) | (df[col] > upper)

        elif method == "zscore":
            mean = series.mean()
            std = series.std()
            if std == 0:
                continue
            z_scores = np.abs((df[col] - mean) / std)
            outlier_mask = z_scores > threshold

        elif method == "isolation_forest":
            iso = IsolationForest(contamination=0.05, random_state=42)
            predictions = iso.fit_predict(df[[col]].fillna(0))
            outlier_mask = pd.Series(predictions == -1, index=df.index)

        else:
            continue

        outlier_count = int(outlier_mask.sum())
        if outlier_count == 0:
            continue

        if action == "clip":
            if method == "iqr":
                df[col] = df[col].clip(lower=lower, upper=upper)
            elif method == "zscore":
                clip_lower = mean - threshold * std
                clip_upper = mean + threshold * std
                df[col] = df[col].clip(lower=clip_lower, upper=clip_upper)
            actions.append(CleaningAction(
                column=col,
                issue="outliers",
                strategy=f"clip ({method})",
                rows_affected=outlier_count,
                description=f"Clipped {outlier_count} outliers in '{col}' to bounds",
            ))

        elif action == "remove":
            df = df[~outlier_mask]
            actions.append(CleaningAction(
                column=col,
                issue="outliers",
                strategy=f"remove ({method})",
                rows_affected=outlier_count,
                description=f"Removed {outlier_count} outlier rows from '{col}'",
            ))

        elif action == "winsorize":
            if method in ("iqr", "zscore"):
                lower_val = series.quantile(0.05)
                upper_val = series.quantile(0.95)
                df[col] = df[col].clip(lower=lower_val, upper=upper_val)
            actions.append(CleaningAction(
                column=col,
                issue="outliers",
                strategy="winsorize (5th-95th percentile)",
                rows_affected=outlier_count,
                description=f"Winsorized {outlier_count} outliers in '{col}'",
            ))

        elif action == "flag":
            flag_col = f"{col}_is_outlier"
            df[flag_col] = outlier_mask.astype(int)
            actions.append(CleaningAction(
                column=col,
                issue="outliers",
                strategy="flag_only",
                rows_affected=outlier_count,
                description=f"Flagged {outlier_count} outliers in new column '{flag_col}'",
            ))

    return df, actions
