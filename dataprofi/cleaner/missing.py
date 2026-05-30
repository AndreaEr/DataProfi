from __future__ import annotations

import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer

from dataprofi.core.types import CleaningAction


def handle_missing(
    df: pd.DataFrame,
    strategy: str = "median",
    columns: list[str] | None = None,
    constant_value=None,
) -> tuple[pd.DataFrame, list[CleaningAction]]:
    df = df.copy()
    actions = []
    target_cols = columns or df.columns[df.isna().any()].tolist()

    for col in target_cols:
        if col not in df.columns:
            continue
        null_count = int(df[col].isna().sum())
        if null_count == 0:
            continue

        if strategy == "drop":
            before_len = len(df)
            df = df.dropna(subset=[col])
            actions.append(CleaningAction(
                column=col,
                issue="missing_values",
                strategy="drop_rows",
                rows_affected=before_len - len(df),
                description=f"Dropped {before_len - len(df)} rows with null '{col}'",
            ))

        elif strategy == "mean":
            if df[col].dtype.kind in ("i", "f"):
                fill_value = df[col].mean()
                df[col] = df[col].fillna(fill_value)
                actions.append(CleaningAction(
                    column=col,
                    issue="missing_values",
                    strategy="mean_imputation",
                    rows_affected=null_count,
                    description=f"Filled {null_count} nulls in '{col}' with mean ({fill_value:.2f})",
                ))

        elif strategy == "median":
            if df[col].dtype.kind in ("i", "f"):
                fill_value = df[col].median()
                df[col] = df[col].fillna(fill_value)
                actions.append(CleaningAction(
                    column=col,
                    issue="missing_values",
                    strategy="median_imputation",
                    rows_affected=null_count,
                    description=f"Filled {null_count} nulls in '{col}' with median ({fill_value:.2f})",
                ))

        elif strategy == "mode":
            fill_value = df[col].mode().iloc[0] if not df[col].mode().empty else None
            if fill_value is not None:
                df[col] = df[col].fillna(fill_value)
                actions.append(CleaningAction(
                    column=col,
                    issue="missing_values",
                    strategy="mode_imputation",
                    rows_affected=null_count,
                    description=f"Filled {null_count} nulls in '{col}' with mode ({fill_value})",
                ))

        elif strategy == "forward_fill":
            df[col] = df[col].ffill()
            remaining = int(df[col].isna().sum())
            actions.append(CleaningAction(
                column=col,
                issue="missing_values",
                strategy="forward_fill",
                rows_affected=null_count - remaining,
                description=f"Forward-filled {null_count - remaining} nulls in '{col}'",
            ))

        elif strategy == "constant":
            fill_value = constant_value if constant_value is not None else 0
            df[col] = df[col].fillna(fill_value)
            actions.append(CleaningAction(
                column=col,
                issue="missing_values",
                strategy="constant_fill",
                rows_affected=null_count,
                description=f"Filled {null_count} nulls in '{col}' with constant ({fill_value})",
            ))

        elif strategy == "ml_impute":
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if col in numeric_cols and len(numeric_cols) > 1:
                imputer = KNNImputer(n_neighbors=5)
                df[numeric_cols] = pd.DataFrame(
                    imputer.fit_transform(df[numeric_cols]),
                    columns=numeric_cols,
                    index=df.index,
                )
                actions.append(CleaningAction(
                    column=col,
                    issue="missing_values",
                    strategy="knn_imputation",
                    rows_affected=null_count,
                    description=f"KNN-imputed {null_count} nulls in '{col}' using 5 neighbors",
                ))

    return df, actions
