from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler

from dataprofi.core.types import CleaningAction


def normalize_column(
    df: pd.DataFrame,
    column: str,
    method: str = "standard",
) -> tuple[pd.DataFrame, CleaningAction]:
    df = df.copy()

    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found")

    series = df[column]
    non_null_count = int(series.notna().sum())

    if method == "standard":
        scaler = StandardScaler()
        values = series.values.reshape(-1, 1)
        mask = ~np.isnan(values.flatten())
        result = np.full_like(values.flatten(), np.nan, dtype=float)
        if mask.any():
            result[mask] = scaler.fit_transform(values[mask].reshape(-1, 1)).flatten()
        df[column] = result
        description = f"Standardized '{column}' (mean=0, std=1)"

    elif method == "minmax":
        scaler = MinMaxScaler()
        values = series.values.reshape(-1, 1)
        mask = ~np.isnan(values.flatten())
        result = np.full_like(values.flatten(), np.nan, dtype=float)
        if mask.any():
            result[mask] = scaler.fit_transform(values[mask].reshape(-1, 1)).flatten()
        df[column] = result
        description = f"Min-max scaled '{column}' to [0, 1]"

    elif method == "log":
        min_val = series.min()
        if min_val <= 0:
            df[column] = np.log1p(series - min_val)
            description = f"Log-transformed '{column}' (shifted by {-min_val:.2f} for non-negative)"
        else:
            df[column] = np.log(series)
            description = f"Log-transformed '{column}'"

    elif method == "onehot":
        dummies = pd.get_dummies(df[column], prefix=column, dtype=int)
        df = pd.concat([df.drop(columns=[column]), dummies], axis=1)
        description = f"One-hot encoded '{column}' into {len(dummies.columns)} columns"

    else:
        raise ValueError(f"Unknown normalization method: {method}")

    action = CleaningAction(
        column=column,
        issue="normalization",
        strategy=method,
        rows_affected=non_null_count,
        description=description,
    )

    return df, action
