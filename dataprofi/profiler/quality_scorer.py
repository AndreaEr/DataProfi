from __future__ import annotations

import pandas as pd
import numpy as np

from dataprofi.core.types import (
    QualityDimension,
    QualityScore,
    QualityReport,
    ColumnProfile,
    DetailedQualityReport,
    QualityJustification,
    ColumnImpact,
)
from dataprofi.core.config import Config
from dataprofi.profiler.column_profiler import profile_columns, classify_column_role


def _score_completeness(df: pd.DataFrame) -> QualityScore:
    total_cells = df.shape[0] * df.shape[1]
    null_cells = int(df.isna().sum().sum())
    score = ((total_cells - null_cells) / total_cells * 100) if total_cells > 0 else 0

    issues = []
    for col in df.columns:
        null_pct = df[col].isna().mean() * 100
        if null_pct > 5:
            issues.append(f"{col}: {null_pct:.1f}% missing")

    return QualityScore(
        dimension=QualityDimension.COMPLETENESS,
        score=round(score, 2),
        details=f"{null_cells} null values across {total_cells} cells",
        issues=issues,
    )


def _score_consistency(df: pd.DataFrame) -> QualityScore:
    issues = []
    inconsistencies = 0
    total_checks = 0

    for col in df.select_dtypes(include=["object", "string"]).columns:
        series = df[col].dropna()
        if len(series) == 0:
            continue
        total_checks += 1

        has_mixed_case = series.str.islower().any() and series.str.isupper().any()
        if has_mixed_case:
            inconsistencies += 1
            issues.append(f"{col}: mixed case formatting")

        has_mixed_whitespace = series.str.startswith(" ").any() or series.str.endswith(" ").any()
        if has_mixed_whitespace:
            inconsistencies += 1
            issues.append(f"{col}: inconsistent whitespace")

        unique_lengths = series.str.len().nunique()
        if unique_lengths == 1 and len(series.unique()) > 1:
            pass
        elif series.str.contains(r"^\d+$", na=False).mean() > 0.5 and series.str.contains(
            r"[a-zA-Z]", na=False
        ).any():
            inconsistencies += 1
            issues.append(f"{col}: mixed numeric and text values")

    score = 100.0
    if total_checks > 0:
        score = max(0, 100 - (inconsistencies / total_checks * 50))

    return QualityScore(
        dimension=QualityDimension.CONSISTENCY,
        score=round(score, 2),
        details=f"{inconsistencies} consistency issues found",
        issues=issues,
    )


def _score_uniqueness(df: pd.DataFrame) -> QualityScore:
    total_rows = len(df)
    duplicate_rows = int(df.duplicated().sum())
    score = ((total_rows - duplicate_rows) / total_rows * 100) if total_rows > 0 else 100

    issues = []
    if duplicate_rows > 0:
        issues.append(f"{duplicate_rows} duplicate rows ({duplicate_rows / total_rows * 100:.1f}%)")

    for col in df.columns:
        if df[col].dtype.kind in ("i", "f"):
            continue
        dup_values = df[col].duplicated().sum()
        dup_pct = dup_values / total_rows * 100
        if dup_pct > 80 and df[col].nunique() < 5:
            issues.append(f"{col}: very low cardinality ({df[col].nunique()} unique values)")

    return QualityScore(
        dimension=QualityDimension.UNIQUENESS,
        score=round(score, 2),
        details=f"{duplicate_rows} exact duplicate rows",
        issues=issues,
    )


def _score_validity(df: pd.DataFrame) -> QualityScore:
    issues = []
    invalid_count = 0
    total_checks = 0

    for col in df.select_dtypes(include=["float64", "int64"]).columns:
        series = df[col].dropna()
        if len(series) == 0:
            continue
        total_checks += 1

        negative_count = (series < 0).sum()
        if negative_count > 0 and series.min() < -1e10:
            invalid_count += 1
            issues.append(f"{col}: suspicious extreme negative values")

        inf_count = np.isinf(series).sum()
        if inf_count > 0:
            invalid_count += 1
            issues.append(f"{col}: {inf_count} infinite values")

        zero_pct = (series == 0).mean()
        if zero_pct > 0.9 and len(series) > 100:
            invalid_count += 1
            issues.append(f"{col}: {zero_pct * 100:.0f}% zeros - possibly missing data encoded as 0")

    for col in df.select_dtypes(include=["object", "string"]).columns:
        series = df[col].dropna()
        if len(series) == 0:
            continue
        total_checks += 1

        empty_count = (series.str.strip() == "").sum()
        if empty_count > 0:
            invalid_count += 1
            issues.append(f"{col}: {empty_count} empty strings (not null)")

    score = 100.0
    if total_checks > 0:
        score = max(0, 100 - (invalid_count / total_checks * 30))

    return QualityScore(
        dimension=QualityDimension.VALIDITY,
        score=round(score, 2),
        details=f"{invalid_count} validity issues across {total_checks} columns",
        issues=issues,
    )


def _score_timeliness(df: pd.DataFrame) -> QualityScore:
    issues = []
    datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

    for col in df.select_dtypes(include=["object", "string"]).columns:
        sample = df[col].dropna().head(100)
        try:
            parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
            if parsed.notna().mean() > 0.8:
                datetime_cols.append(col)
        except (ValueError, TypeError):
            pass

    if not datetime_cols:
        return QualityScore(
            dimension=QualityDimension.TIMELINESS,
            score=80.0,
            details="No datetime columns detected - timeliness cannot be fully assessed",
            issues=["No temporal columns found for timeliness check"],
        )

    score = 100.0
    for col in datetime_cols[:3]:
        try:
            dates = pd.to_datetime(df[col], errors="coerce")
            valid_dates = dates.dropna()
            if len(valid_dates) == 0:
                continue

            date_range = (valid_dates.max() - valid_dates.min()).days
            if date_range == 0:
                issues.append(f"{col}: all dates are the same")
                score -= 10

            gaps = valid_dates.sort_values().diff().dropna()
            if len(gaps) > 1:
                median_gap = gaps.median()
                large_gaps = gaps[gaps > median_gap * 3]
                if len(large_gaps) > 0:
                    issues.append(f"{col}: {len(large_gaps)} unusual temporal gaps detected")
                    score -= 5
        except (ValueError, TypeError):
            continue

    return QualityScore(
        dimension=QualityDimension.TIMELINESS,
        score=round(max(0, score), 2),
        details=f"Analyzed {len(datetime_cols)} temporal column(s)",
        issues=issues,
    )


def score_quality(df: pd.DataFrame, config: Config | None = None) -> QualityReport:
    config = config or Config()

    scores = {
        QualityDimension.COMPLETENESS: _score_completeness(df),
        QualityDimension.CONSISTENCY: _score_consistency(df),
        QualityDimension.UNIQUENESS: _score_uniqueness(df),
        QualityDimension.VALIDITY: _score_validity(df),
        QualityDimension.TIMELINESS: _score_timeliness(df),
    }

    weights = config.quality_weights
    overall = sum(
        scores[QualityDimension(dim)].score * weight
        for dim, weight in weights.items()
    )

    profiles = profile_columns(df)
    worst_columns = sorted(profiles, key=lambda p: p.completeness)[:5]

    suggested_fixes = []
    for dim_score in scores.values():
        for issue in dim_score.issues:
            col_name = issue.split(":")[0] if ":" in issue else ""
            suggested_fixes.append({
                "column": col_name,
                "dimension": dim_score.dimension.value,
                "issue": issue,
            })

    return QualityReport(
        overall_score=round(overall, 2),
        dimension_scores={dim.value: s.score for dim, s in scores.items()},
        column_profiles=profiles,
        worst_columns=[p.name for p in worst_columns],
        suggested_fixes=suggested_fixes,
        row_count=len(df),
        column_count=len(df.columns),
    )


_ROLE_NULL_MULTIPLIER = {
    "id": 5.0,
    "category": 1.5,
    "measure": 1.0,
    "datetime": 2.0,
    "boolean": 1.0,
    "free_text": 0.3,
}

_ROLE_NULL_CONTEXT = {
    "id": "Missing IDs indicate data pipeline integrity failure",
    "category": "Missing categories may introduce analysis bias",
    "measure": "Missing values affect aggregation accuracy",
    "datetime": "Temporal gaps complicate time-series analysis",
    "boolean": "Missing flags cause ambiguous filtering",
    "free_text": "Low impact - text fields are often optional",
}


def score_quality_detailed(df: pd.DataFrame, config: Config | None = None) -> DetailedQualityReport:
    config = config or Config()
    base_report = score_quality(df, config)

    column_roles = {}
    for col in df.columns:
        role = classify_column_role(df[col])
        column_roles[col] = role.value

    justifications = []

    completeness_impacts = []
    for col in df.columns:
        null_pct = df[col].isna().mean() * 100
        if null_pct > 2:
            role = column_roles[col]
            multiplier = _ROLE_NULL_MULTIPLIER.get(role, 1.0)
            severity = "critical" if null_pct * multiplier > 25 else "warning" if null_pct * multiplier > 10 else "info"
            fix = f"Impute or resolve {null_pct:.0f}% missing values"
            impact_pts = round(null_pct * multiplier * 0.25 / len(df.columns), 1)
            completeness_impacts.append(ColumnImpact(
                column=col,
                role=role,
                issue=f"{null_pct:.1f}% missing",
                severity=severity,
                suggested_fix=fix,
                estimated_impact=f"+{impact_pts} overall" if impact_pts > 0 else "minimal",
            ))

    comp_score = base_report.dimension_scores.get("completeness", 100)
    problem_cols = len([i for i in completeness_impacts if i.severity in ("critical", "warning")])
    comp_explanation = (
        f"Score {comp_score:.0f}/100: {problem_cols} columns have significant missing data. "
        if problem_cols > 0
        else f"Score {comp_score:.0f}/100: data is well-populated across all columns."
    )
    if completeness_impacts:
        worst = completeness_impacts[0]
        comp_explanation += f"Most impactful: '{worst.column}' ({worst.role}) with {worst.issue}. {_ROLE_NULL_CONTEXT.get(worst.role, '')}"

    justifications.append(QualityJustification(
        dimension="completeness",
        score=comp_score,
        explanation=comp_explanation,
        column_impacts=completeness_impacts[:10],
    ))

    for dim_name in ["consistency", "uniqueness", "validity", "timeliness"]:
        dim_score = base_report.dimension_scores.get(dim_name, 100)
        dim_enum = QualityDimension(dim_name)
        dim_issues = []
        for fix in base_report.suggested_fixes:
            if fix.get("dimension") == dim_name:
                col = fix.get("column", "")
                role = column_roles.get(col, "measure")
                dim_issues.append(ColumnImpact(
                    column=col,
                    role=role,
                    issue=fix.get("issue", ""),
                    severity="warning",
                    suggested_fix=f"Address {dim_name} issue in '{col}'",
                    estimated_impact=f"+{round((100 - dim_score) * 0.1, 1)} overall",
                ))

        issue_count = len(dim_issues)
        if dim_score >= 95:
            explanation = f"Score {dim_score:.0f}/100: excellent {dim_name}, no significant issues found."
        elif dim_score >= 80:
            explanation = f"Score {dim_score:.0f}/100: {issue_count} minor {dim_name} issues detected."
        else:
            explanation = f"Score {dim_score:.0f}/100: {issue_count} {dim_name} issues require attention."

        justifications.append(QualityJustification(
            dimension=dim_name,
            score=dim_score,
            explanation=explanation,
            column_impacts=dim_issues[:10],
        ))

    return DetailedQualityReport(
        overall_score=base_report.overall_score,
        dimension_scores=base_report.dimension_scores,
        justifications=justifications,
        row_count=base_report.row_count,
        column_count=base_report.column_count,
        worst_columns=base_report.worst_columns,
        suggested_fixes=base_report.suggested_fixes,
    )
