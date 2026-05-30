from __future__ import annotations

import numpy as np
import pandas as pd

from dataprofi.core.types import MLReadinessCheck, MLReadinessReport


def _check_missing_values(df: pd.DataFrame) -> MLReadinessCheck:
    missing_pct = df.isna().mean().mean() * 100
    if missing_pct == 0:
        return MLReadinessCheck(
            name="Missing Values",
            passed=True,
            severity="info",
            message="No missing values detected",
        )
    elif missing_pct < 5:
        return MLReadinessCheck(
            name="Missing Values",
            passed=True,
            severity="warning",
            message=f"{missing_pct:.1f}% missing values - acceptable for most models",
            suggestion="Consider imputation for columns with >1% missing",
        )
    else:
        return MLReadinessCheck(
            name="Missing Values",
            passed=False,
            severity="critical",
            message=f"{missing_pct:.1f}% missing values - too high for reliable ML",
            suggestion="Apply imputation or drop columns with >50% missing",
        )


def _check_class_imbalance(df: pd.DataFrame) -> MLReadinessCheck:
    categorical_cols = df.select_dtypes(include=["object", "string", "category"]).columns
    if len(categorical_cols) == 0:
        return MLReadinessCheck(
            name="Class Imbalance",
            passed=True,
            severity="info",
            message="No categorical target columns detected",
        )

    worst_ratio = 1.0
    worst_col = ""
    for col in categorical_cols:
        counts = df[col].value_counts()
        if len(counts) < 2 or len(counts) > 20:
            continue
        ratio = counts.min() / counts.max()
        if ratio < worst_ratio:
            worst_ratio = ratio
            worst_col = col

    if worst_ratio > 0.3:
        return MLReadinessCheck(
            name="Class Imbalance",
            passed=True,
            severity="info",
            message=f"Classes are reasonably balanced (worst ratio: {worst_ratio:.2f})",
        )
    else:
        return MLReadinessCheck(
            name="Class Imbalance",
            passed=False,
            severity="warning",
            message=f"Severe imbalance in '{worst_col}' (ratio: {worst_ratio:.3f})",
            suggestion="Consider SMOTE, class weights, or stratified sampling",
        )


def _check_constant_columns(df: pd.DataFrame) -> MLReadinessCheck:
    constant_cols = [col for col in df.columns if df[col].nunique() <= 1]
    if not constant_cols:
        return MLReadinessCheck(
            name="Constant Columns",
            passed=True,
            severity="info",
            message="No constant columns found",
        )
    else:
        return MLReadinessCheck(
            name="Constant Columns",
            passed=False,
            severity="warning",
            message=f"{len(constant_cols)} constant column(s): {', '.join(constant_cols[:5])}",
            suggestion="Remove constant columns - they provide no signal",
        )


def _check_high_cardinality(df: pd.DataFrame) -> MLReadinessCheck:
    high_card_cols = []
    for col in df.select_dtypes(include=["object", "string"]).columns:
        ratio = df[col].nunique() / len(df)
        if ratio > 0.5 and df[col].nunique() > 100:
            high_card_cols.append(f"{col} ({df[col].nunique()} unique)")

    if not high_card_cols:
        return MLReadinessCheck(
            name="High Cardinality",
            passed=True,
            severity="info",
            message="No problematic high-cardinality categoricals",
        )
    else:
        return MLReadinessCheck(
            name="High Cardinality",
            passed=False,
            severity="warning",
            message=f"High-cardinality columns: {', '.join(high_card_cols[:3])}",
            suggestion="Use target encoding, hashing, or embeddings instead of one-hot",
        )


def _check_correlation(df: pd.DataFrame) -> MLReadinessCheck:
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] < 2:
        return MLReadinessCheck(
            name="Feature Correlation",
            passed=True,
            severity="info",
            message="Fewer than 2 numeric columns - correlation check skipped",
        )

    corr_matrix = numeric_df.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    high_corr_pairs = []

    for col in upper.columns:
        for idx in upper.index:
            val = upper.loc[idx, col]
            if pd.notna(val) and val > 0.95:
                high_corr_pairs.append(f"{idx} <-> {col} ({val:.3f})")

    if not high_corr_pairs:
        return MLReadinessCheck(
            name="Feature Correlation",
            passed=True,
            severity="info",
            message="No highly correlated feature pairs (>0.95)",
        )
    else:
        return MLReadinessCheck(
            name="Feature Correlation",
            passed=False,
            severity="warning",
            message=f"{len(high_corr_pairs)} highly correlated pairs: {', '.join(high_corr_pairs[:3])}",
            suggestion="Drop one of each correlated pair or use PCA for dimensionality reduction",
        )


def _check_target_leakage(df: pd.DataFrame) -> MLReadinessCheck:
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] < 2:
        return MLReadinessCheck(
            name="Target Leakage",
            passed=True,
            severity="info",
            message="Insufficient numeric columns for leakage detection",
        )

    suspicious = []
    for col in numeric_df.columns:
        if numeric_df[col].nunique() == 2:
            corrs = numeric_df.corr()[col].abs()
            perfect = corrs[(corrs > 0.99) & (corrs.index != col)]
            if len(perfect) > 0:
                suspicious.append(f"{col} perfectly correlates with {list(perfect.index)}")

    if not suspicious:
        return MLReadinessCheck(
            name="Target Leakage",
            passed=True,
            severity="info",
            message="No obvious target leakage detected",
        )
    else:
        return MLReadinessCheck(
            name="Target Leakage",
            passed=False,
            severity="critical",
            message=f"Possible leakage: {'; '.join(suspicious[:2])}",
            suggestion="Verify these features are available at prediction time",
        )


def _check_data_size(df: pd.DataFrame) -> MLReadinessCheck:
    rows, cols = df.shape
    if rows < 50:
        return MLReadinessCheck(
            name="Data Size",
            passed=False,
            severity="critical",
            message=f"Only {rows} rows - insufficient for most ML models",
            suggestion="Collect more data or use few-shot / transfer learning approaches",
        )
    elif rows < 500:
        return MLReadinessCheck(
            name="Data Size",
            passed=True,
            severity="warning",
            message=f"{rows} rows - small dataset, consider simpler models",
            suggestion="Use cross-validation and regularized models",
        )
    else:
        return MLReadinessCheck(
            name="Data Size",
            passed=True,
            severity="info",
            message=f"{rows:,} rows x {cols} columns - sufficient for training",
        )


def check_ml_readiness(df: pd.DataFrame) -> MLReadinessReport:
    checks = [
        _check_missing_values(df),
        _check_class_imbalance(df),
        _check_constant_columns(df),
        _check_high_cardinality(df),
        _check_correlation(df),
        _check_target_leakage(df),
        _check_data_size(df),
    ]

    critical_failures = [c for c in checks if not c.passed and c.severity == "critical"]
    all_passed = all(c.passed for c in checks)
    score = sum(1 for c in checks if c.passed) / len(checks) * 100

    next_steps = []
    for check in checks:
        if not check.passed and check.suggestion:
            next_steps.append(check.suggestion)

    return MLReadinessReport(
        overall_ready=all_passed and len(critical_failures) == 0,
        score=round(score, 1),
        checks=checks,
        recommended_next_steps=next_steps,
    )
