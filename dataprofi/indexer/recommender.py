from __future__ import annotations

import re

import pandas as pd
from sqlalchemy import create_engine, text

from dataprofi.core.types import IndexRecommendation, IndexType
from dataprofi.indexer.analyzer import analyze_column_for_index, ColumnAnalysis
from dataprofi.indexer.generator import generate_index_sql
from dataprofi.indexer.explainer import explain_index


def _validate_identifier(name: str) -> str:
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise ValueError(f"Invalid SQL identifier: '{name}'")
    return name


class IndexPilot:
    def __init__(self, connection_string: str | None = None):
        self._connection_string = connection_string
        self._engine = create_engine(connection_string) if connection_string else None

    def analyze_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str = "table",
    ) -> list[IndexRecommendation]:
        recommendations = []
        total_rows = len(df)

        for col in df.columns:
            analysis = analyze_column_for_index(df[col], total_rows)
            if analysis.recommended_index is None:
                continue

            rec = IndexRecommendation(
                column=analysis.name,
                index_type=analysis.recommended_index,
                reason=_build_short_reason(analysis),
                explanation=explain_index(analysis, table_name),
                sql=generate_index_sql(table_name, analysis.name, analysis.recommended_index),
                priority=analysis.priority,
                estimated_impact=_estimate_impact_short(analysis),
            )
            recommendations.append(rec)

        recommendations.sort(key=lambda r: {"high": 0, "medium": 1, "low": 2}[r.priority])
        return recommendations

    def analyze_table(
        self,
        table_name: str,
        schema: str = "public",
        sample_size: int = 10000,
    ) -> list[IndexRecommendation]:
        if not self._engine:
            raise RuntimeError("No database connection. Pass connection_string to IndexPilot.")

        _validate_identifier(table_name)
        _validate_identifier(schema)

        with self._engine.connect() as conn:
            query = text(f'SELECT * FROM "{schema}"."{table_name}" LIMIT :limit')
            df = pd.read_sql(query, conn, params={"limit": sample_size})

            existing_idx_query = text("""
                SELECT a.attname as column_name
                FROM pg_index i
                JOIN pg_class c ON c.oid = i.indrelid
                JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = ANY(i.indkey)
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relname = :table AND n.nspname = :schema
            """)
            result = conn.execute(existing_idx_query, {"table": table_name, "schema": schema})
            indexed_columns = {row[0] for row in result}

        recommendations = []
        total_rows = len(df)

        for col in df.columns:
            if col in indexed_columns:
                continue

            analysis = analyze_column_for_index(df[col], total_rows)
            if analysis.recommended_index is None:
                continue

            rec = IndexRecommendation(
                column=analysis.name,
                index_type=analysis.recommended_index,
                reason=_build_short_reason(analysis),
                explanation=explain_index(analysis, table_name),
                sql=generate_index_sql(table_name, analysis.name, analysis.recommended_index, schema),
                priority=analysis.priority,
                estimated_impact=_estimate_impact_short(analysis),
            )
            recommendations.append(rec)

        recommendations.sort(key=lambda r: {"high": 0, "medium": 1, "low": 2}[r.priority])
        return recommendations

    def apply_recommendations(
        self,
        recommendations: list[IndexRecommendation],
        dry_run: bool = False,
    ) -> list[str]:
        if not self._engine:
            raise RuntimeError("No database connection.")

        results = []
        for rec in recommendations:
            if dry_run:
                results.append(f"[DRY RUN] {rec.sql}")
            else:
                with self._engine.connect() as conn:
                    conn.execute(text(rec.sql))
                    conn.commit()
                results.append(f"[APPLIED] {rec.sql}")

        return results


def recommend_indexes(
    df: pd.DataFrame,
    table_name: str = "table",
) -> list[IndexRecommendation]:
    pilot = IndexPilot()
    return pilot.analyze_dataframe(df, table_name)


def _build_short_reason(analysis: ColumnAnalysis) -> str:
    idx_type = analysis.recommended_index
    if idx_type == IndexType.BTREE:
        return (
            f"High cardinality ({analysis.cardinality} unique), "
            f"good selectivity for filtered queries"
        )
    elif idx_type == IndexType.BRIN:
        return "Data is physically ordered - BRIN provides compact range filtering"
    elif idx_type == IndexType.GIN:
        if analysis.is_array_or_json:
            return "Array/JSON data - GIN enables fast containment queries"
        return "Long text values - GIN supports full-text search"
    elif idx_type == IndexType.GIST:
        return "Spatial/range data benefits from GiST tree structure"
    return ""


def _estimate_impact_short(analysis: ColumnAnalysis) -> str:
    if analysis.total_rows < 1000:
        return "Low - small table"
    if analysis.recommended_index == IndexType.BRIN and analysis.is_sorted:
        return "Estimated 90%+ block skip rate"
    selectivity = 1 / analysis.cardinality if analysis.cardinality > 0 else 1
    if selectivity < 0.01:
        return f"Estimated {(1 - selectivity) * 100:.0f}% row skip for filtered queries"
    elif selectivity < 0.1:
        return f"Estimated {(1 - selectivity) * 100:.0f}% improvement for filtered queries"
    return "Moderate improvement for sorted/filtered access"
