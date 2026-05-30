from __future__ import annotations

import webbrowser
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

from dataprofi.core.types import QualityReport, IndexRecommendation, MLReadinessReport
from dataprofi.profiler.quality_scorer import score_quality
from dataprofi.profiler.ml_readiness import check_ml_readiness
from dataprofi.cleaner.pipeline import auto_clean as _auto_clean
from dataprofi.indexer.recommender import IndexPilot, recommend_indexes as _recommend_indexes


def analyze(df: pd.DataFrame) -> QualityReport:
    return score_quality(df)


def auto_clean(df: pd.DataFrame) -> pd.DataFrame:
    return _auto_clean(df)


def recommend_indexes(
    df: pd.DataFrame,
    table_name: str = "table",
) -> list[IndexRecommendation]:
    return _recommend_indexes(df, table_name=table_name)


def ml_readiness(df: pd.DataFrame) -> MLReadinessReport:
    return check_ml_readiness(df)


def to_postgres(
    df: pd.DataFrame,
    table_name: str,
    connection: str,
    schema: str = "public",
    if_exists: str = "replace",
    create_indexes: bool = True,
) -> dict:
    engine = create_engine(connection)

    df.to_sql(table_name, engine, schema=schema, if_exists=if_exists, index=False)

    result = {
        "table": table_name,
        "rows_loaded": len(df),
        "indexes_created": [],
    }

    if create_indexes:
        pilot = IndexPilot(connection_string=connection)
        recommendations = pilot.analyze_table(table_name, schema=schema)
        applied = pilot.apply_recommendations(recommendations)
        result["indexes_created"] = applied

    return result


def serve(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True):
    import uvicorn
    from dataprofi.api.server import app

    if open_browser:
        webbrowser.open(f"http://{host}:{port}")

    uvicorn.run(app, host=host, port=port)
