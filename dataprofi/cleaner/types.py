from __future__ import annotations

import pandas as pd
import numpy as np

from dataprofi.core.types import CleaningAction


def coerce_types(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    type_map: dict[str, str] | None = None,
) -> tuple[pd.DataFrame, list[CleaningAction]]:
    df = df.copy()
    actions = []
    target_cols = columns or df.columns.tolist()

    if type_map:
        for col, target_type in type_map.items():
            if col not in df.columns:
                continue
            original_type = str(df[col].dtype)
            try:
                if target_type == "numeric":
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                elif target_type == "datetime":
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                elif target_type == "string":
                    df[col] = df[col].astype(str)
                elif target_type == "category":
                    df[col] = df[col].astype("category")
                else:
                    df[col] = df[col].astype(target_type)

                coerced_nulls = int(df[col].isna().sum())
                actions.append(CleaningAction(
                    column=col,
                    issue="type_mismatch",
                    strategy=f"coerce to {target_type}",
                    rows_affected=coerced_nulls,
                    description=f"Coerced '{col}' from {original_type} to {target_type} ({coerced_nulls} failures → null)",
                ))
            except (ValueError, TypeError):
                pass
        return df, actions

    for col in target_cols:
        if not pd.api.types.is_string_dtype(df[col]) and df[col].dtype != "object":
            continue

        series = df[col].dropna()
        if len(series) == 0:
            continue

        numeric_parseable = pd.to_numeric(series, errors="coerce")
        if numeric_parseable.notna().mean() > 0.8:
            failed = int(numeric_parseable.isna().sum())
            df[col] = pd.to_numeric(df[col], errors="coerce")
            actions.append(CleaningAction(
                column=col,
                issue="type_mismatch",
                strategy="auto_coerce to numeric",
                rows_affected=failed,
                description=f"Auto-coerced '{col}' to numeric ({failed} unparseable → null)",
            ))
            continue

        date_parseable = pd.to_datetime(series.head(100), errors="coerce")
        if date_parseable.notna().mean() > 0.8:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            actions.append(CleaningAction(
                column=col,
                issue="type_mismatch",
                strategy="auto_coerce to datetime",
                rows_affected=0,
                description=f"Auto-coerced '{col}' to datetime",
            ))

    return df, actions
