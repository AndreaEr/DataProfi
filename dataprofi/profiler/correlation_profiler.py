from __future__ import annotations

import numpy as np
import pandas as pd

from dataprofi.core.config import Config
from dataprofi.core.types import (
    CorrelationPair,
    CorrelationReport,
    FunctionalDependency,
)

_config = Config()


def _cramers_v(col_a: pd.Series, col_b: pd.Series) -> float:
    contingency = pd.crosstab(col_a, col_b)
    n = contingency.sum().sum()
    if n == 0:
        return 0.0
    row_sums = contingency.sum(axis=1).values
    col_sums = contingency.sum(axis=0).values
    expected = np.outer(row_sums, col_sums) / n
    with np.errstate(divide="ignore", invalid="ignore"):
        chi2 = np.sum((contingency.values - expected) ** 2 / (expected + 1e-10))
    r, c = contingency.shape
    min_dim = min(r, c) - 1
    if min_dim <= 0:
        return 0.0
    return float(np.sqrt(chi2 / (n * min_dim)))


def _find_functional_dependencies(
    df: pd.DataFrame, max_cardinality: int = 200
) -> list[FunctionalDependency]:
    deps = []
    candidates = []
    for col in df.columns:
        nunique = df[col].nunique()
        if 2 <= nunique <= max_cardinality:
            candidates.append(col)

    for det in candidates:
        for dep in df.columns:
            if det == dep:
                continue
            grouped = df.dropna(subset=[det, dep]).groupby(det)[dep].nunique()
            if len(grouped) == 0:
                continue
            confidence = float((grouped == 1).sum() / len(grouped))
            if confidence > _config.functional_dependency_confidence:
                deps.append(FunctionalDependency(
                    determinant=det,
                    dependent=dep,
                    confidence=round(confidence, 3),
                ))
    return deps


def profile_correlations(df: pd.DataFrame) -> CorrelationReport:
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = [
        c for c in df.select_dtypes(include=["object", "category"]).columns
        if df[c].nunique() <= 50
    ]

    numeric_correlations = []
    correlation_matrix: dict[str, dict[str, float]] = {}
    redundant_columns: list[list] = []

    if len(numeric_cols) >= 2:
        corr_df = df[numeric_cols].corr()
        correlation_matrix = {
            col: {row: round(float(corr_df.loc[row, col]), 4) for row in numeric_cols}
            for col in numeric_cols
        }
        seen = set()
        for i, col_a in enumerate(numeric_cols):
            for j, col_b in enumerate(numeric_cols):
                if j <= i:
                    continue
                pair_key = (col_a, col_b)
                if pair_key in seen:
                    continue
                seen.add(pair_key)
                r = float(corr_df.loc[col_a, col_b])
                if np.isnan(r):
                    continue
                if abs(r) > _config.correlation_notable_threshold:
                    numeric_correlations.append(CorrelationPair(
                        column_a=col_a,
                        column_b=col_b,
                        correlation=round(r, 4),
                        method="pearson",
                    ))
                if abs(r) > _config.correlation_redundant_threshold:
                    redundant_columns.append([col_a, col_b, round(r, 4)])

    numeric_correlations.sort(key=lambda p: abs(p.correlation), reverse=True)

    categorical_associations = []
    if len(cat_cols) >= 2:
        seen_cat = set()
        for i, col_a in enumerate(cat_cols):
            for j, col_b in enumerate(cat_cols):
                if j <= i:
                    continue
                pair_key = (col_a, col_b)
                if pair_key in seen_cat:
                    continue
                seen_cat.add(pair_key)
                valid = df[[col_a, col_b]].dropna()
                if len(valid) < 10:
                    continue
                v = _cramers_v(valid[col_a], valid[col_b])
                if v > _config.correlation_notable_threshold:
                    categorical_associations.append(CorrelationPair(
                        column_a=col_a,
                        column_b=col_b,
                        correlation=round(v, 4),
                        method="cramers_v",
                    ))
        categorical_associations.sort(key=lambda p: abs(p.correlation), reverse=True)

    functional_dependencies = _find_functional_dependencies(df)

    return CorrelationReport(
        numeric_correlations=numeric_correlations[:20],
        categorical_associations=categorical_associations[:20],
        functional_dependencies=functional_dependencies[:20],
        redundant_columns=redundant_columns,
        correlation_matrix=correlation_matrix,
    )
