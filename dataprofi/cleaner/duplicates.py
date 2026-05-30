from __future__ import annotations

import pandas as pd
from thefuzz import fuzz

from dataprofi.core.types import CleaningAction


def remove_duplicates(
    df: pd.DataFrame,
    method: str = "exact",
    columns: list[str] | None = None,
    keep: str = "first",
    threshold: int = 85,
) -> tuple[pd.DataFrame, list[CleaningAction]]:
    df = df.copy()
    actions = []
    before_len = len(df)

    if method == "exact":
        subset = columns if columns else None
        df = df.drop_duplicates(subset=subset, keep=keep)
        removed = before_len - len(df)
        if removed > 0:
            actions.append(CleaningAction(
                column=", ".join(columns) if columns else "all",
                issue="duplicate_rows",
                strategy="exact_dedup",
                rows_affected=removed,
                description=f"Removed {removed} exact duplicate rows (kept {keep})",
            ))

    elif method == "fuzzy":
        if not columns:
            columns = df.select_dtypes(include=["object", "string"]).columns.tolist()[:3]

        if not columns:
            return df, actions

        to_drop = set()
        col = columns[0]
        values = df[col].dropna().tolist()

        for i in range(len(values)):
            if i in to_drop:
                continue
            for j in range(i + 1, min(i + 100, len(values))):
                if j in to_drop:
                    continue
                similarity = fuzz.ratio(str(values[i]), str(values[j]))
                if similarity >= threshold:
                    to_drop.add(j)

        if to_drop:
            df = df.drop(df.index[list(to_drop)])
            actions.append(CleaningAction(
                column=col,
                issue="near_duplicates",
                strategy=f"fuzzy_dedup (threshold={threshold}%)",
                rows_affected=len(to_drop),
                description=f"Removed {len(to_drop)} fuzzy duplicates in '{col}'",
            ))

    return df, actions
