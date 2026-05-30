from __future__ import annotations

import uuid
from io import BytesIO, StringIO

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from dataprofi.api.schemas import (
    ApiLoadRequest,
    CleanRequest,
    ColumnProfileResponse,
    QualityScoreResponse,
    IndexRecommendationResponse,
    MLReadinessResponse,
    MLReadinessCheckResponse,
    CleanResponse,
    CleaningActionResponse,
    DatasetInfo,
    EnhancedColumnProfileResponse,
    CategoryStatsResponse,
    NumericInsightResponse,
    DatetimeInsightResponse,
    TimeseriesReportResponse,
    TimeseriesProfileResponse,
    CorrelationReportResponse,
    CorrelationPairResponse,
    FunctionalDependencyResponse,
    DetailedQualityScoreResponse,
    QualityJustificationResponse,
    ColumnImpactResponse,
)
from dataprofi.ingest.api_loader import load_from_api
from dataprofi.profiler.column_profiler import profile_columns, profile_columns_enhanced, get_outlier_rows, get_issue_rows
from dataprofi.profiler.geo_profiler import profile_geo
from dataprofi.profiler.schema_recommender import recommend_schema
from dataprofi.profiler.methodology import get_methodology
from dataprofi.profiler.quality_scorer import score_quality, score_quality_detailed
from dataprofi.profiler.ml_readiness import check_ml_readiness
from dataprofi.profiler.timeseries_profiler import profile_timeseries
from dataprofi.profiler.correlation_profiler import profile_correlations
from dataprofi.cleaner.pipeline import CleaningPipeline
from dataprofi.indexer.recommender import recommend_indexes

_datasets: dict[str, pd.DataFrame] = {}


def create_app() -> FastAPI:
    app = FastAPI(
        title="DataProfi API",
        description="Data quality profiling, cleaning, and index recommendation",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/methodology")
    async def methodology():
        return get_methodology()

    @app.post("/api/ingest/upload", response_model=DatasetInfo)
    async def upload_file(file: UploadFile = File(...)):
        content = await file.read()
        filename = file.filename or "upload"

        if filename.endswith(".csv"):
            df = pd.read_csv(BytesIO(content))
        elif filename.endswith(".json"):
            df = pd.read_json(BytesIO(content))
        else:
            raise HTTPException(400, "Unsupported file format. Use CSV or JSON.")

        dataset_id = str(uuid.uuid4())[:8]
        _datasets[dataset_id] = df

        return DatasetInfo(
            id=dataset_id,
            name=filename,
            rows=len(df),
            columns=len(df.columns),
            column_names=df.columns.tolist(),
        )

    @app.post("/api/ingest/api", response_model=DatasetInfo)
    async def load_from_api_endpoint(request: ApiLoadRequest):
        try:
            df = load_from_api(request.url, record_path=request.record_path, limit=request.limit)
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            raise HTTPException(400, f"Failed to load data: {e}")

        dataset_id = str(uuid.uuid4())[:8]
        _datasets[dataset_id] = df

        url_name = request.url.split("/")[-1].split("?")[0] or "api_data"
        return DatasetInfo(
            id=dataset_id,
            name=url_name,
            rows=len(df),
            columns=len(df.columns),
            column_names=df.columns.tolist(),
        )

    @app.get("/api/profile/{dataset_id}", response_model=list[ColumnProfileResponse])
    async def get_profile(dataset_id: str):
        df = _get_dataset(dataset_id)
        profiles = profile_columns(df)
        return [
            ColumnProfileResponse(
                name=p.name,
                dtype=p.dtype,
                total_count=p.total_count,
                null_count=p.null_count,
                unique_count=p.unique_count,
                completeness=p.completeness,
                unique_ratio=p.unique_ratio,
                mean=p.mean,
                std=p.std,
                min_value=str(p.min_value) if p.min_value is not None else None,
                max_value=str(p.max_value) if p.max_value is not None else None,
                distribution=p.distribution,
                outlier_count=p.outlier_count,
                quality_issues=p.quality_issues,
            )
            for p in profiles
        ]

    @app.get("/api/profile/{dataset_id}/outliers/{column}")
    async def get_outlier_details(dataset_id: str, column: str):
        df = _get_dataset(dataset_id)
        result = get_outlier_rows(df, column)
        return {
            "column": column,
            "outlier_count": len(result["rows"]),
            "context": result["context"],
            "rows": result["rows"],
        }

    @app.get("/api/profile/{dataset_id}/issues/{column}")
    async def get_column_issues(dataset_id: str, column: str, issue_type: str = "all"):
        df = _get_dataset(dataset_id)
        return get_issue_rows(df, column, issue_type=issue_type)

    @app.get("/api/profile/{dataset_id}/score", response_model=QualityScoreResponse)
    async def get_quality_score(dataset_id: str):
        df = _get_dataset(dataset_id)
        report = score_quality(df)
        return QualityScoreResponse(
            overall_score=report.overall_score,
            dimension_scores=report.dimension_scores,
            row_count=report.row_count,
            column_count=report.column_count,
            worst_columns=report.worst_columns,
            suggested_fixes=report.suggested_fixes,
        )

    @app.post("/api/clean/{dataset_id}", response_model=CleanResponse)
    async def clean_dataset(dataset_id: str, request: CleanRequest):
        df = _get_dataset(dataset_id)
        pipeline = CleaningPipeline()

        for step in request.steps:
            params = {}
            if step.strategy:
                params["strategy"] = step.strategy
            if step.method:
                params["method"] = step.method
            if step.action:
                params["action"] = step.action
            if step.columns:
                params["columns"] = step.columns
            if step.threshold:
                params["threshold"] = step.threshold
            pipeline.add_step(step.step_type, **params)

        cleaned_df = pipeline.run(df)
        _datasets[dataset_id] = cleaned_df

        report = pipeline.report()
        return CleanResponse(
            actions=[
                CleaningActionResponse(
                    column=a.column,
                    issue=a.issue,
                    strategy=a.strategy,
                    rows_affected=a.rows_affected,
                    description=a.description,
                )
                for a in report.actions
            ],
            rows_before=report.rows_before,
            rows_after=report.rows_after,
            score_before=report.score_before,
            score_after=report.score_after,
        )

    @app.get("/api/dataset/{dataset_id}/preview")
    async def preview_dataset(dataset_id: str, rows: int = 10):
        df = _get_dataset(dataset_id)
        rows = min(rows, 50)
        sample = df.head(rows)
        return {
            "columns": df.columns.tolist(),
            "total_rows": len(df),
            "rows": sample.fillna("").astype(str).values.tolist(),
        }

    @app.get("/api/dataset/{dataset_id}/download")
    async def download_dataset(dataset_id: str):
        df = _get_dataset(dataset_id)
        buffer = StringIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=cleaned_{dataset_id}.csv"},
        )

    @app.get("/api/index/{dataset_id}/recommend", response_model=list[IndexRecommendationResponse])
    async def get_index_recommendations(dataset_id: str, table_name: str = "table"):
        df = _get_dataset(dataset_id)
        recommendations = recommend_indexes(df, table_name=table_name)
        return [
            IndexRecommendationResponse(
                column=r.column,
                index_type=r.index_type.value,
                reason=r.reason,
                explanation=r.explanation,
                sql=r.sql,
                priority=r.priority,
                estimated_impact=r.estimated_impact,
            )
            for r in recommendations
        ]

    @app.get("/api/ml/{dataset_id}/readiness", response_model=MLReadinessResponse)
    async def get_ml_readiness(dataset_id: str):
        df = _get_dataset(dataset_id)
        report = check_ml_readiness(df)
        return MLReadinessResponse(
            overall_ready=report.overall_ready,
            score=report.score,
            checks=[
                MLReadinessCheckResponse(
                    name=c.name,
                    passed=c.passed,
                    severity=c.severity,
                    message=c.message,
                    suggestion=c.suggestion,
                )
                for c in report.checks
            ],
            recommended_next_steps=report.recommended_next_steps,
        )

    @app.get("/api/profile/{dataset_id}/enhanced", response_model=list[EnhancedColumnProfileResponse])
    async def get_enhanced_profile(dataset_id: str):
        df = _get_dataset(dataset_id)
        profiles = profile_columns_enhanced(df)
        results = []
        for p in profiles:
            cat_stats = None
            if p.category_stats:
                cat_stats = CategoryStatsResponse(
                    top_values=p.category_stats.top_values,
                    dominant_value_pct=p.category_stats.dominant_value_pct,
                    is_skewed=p.category_stats.is_skewed,
                )
            num_insight = None
            if p.numeric_insight:
                num_insight = NumericInsightResponse(
                    median=p.numeric_insight.median,
                    range_value=p.numeric_insight.range_value,
                    distribution_shape=p.numeric_insight.distribution_shape,
                    interpretation=p.numeric_insight.interpretation,
                    percentile_25=p.numeric_insight.percentile_25,
                    percentile_75=p.numeric_insight.percentile_75,
                )
            dt_insight = None
            if p.datetime_insight:
                dt_insight = DatetimeInsightResponse(
                    date_range_start=p.datetime_insight.date_range_start,
                    date_range_end=p.datetime_insight.date_range_end,
                    frequency=p.datetime_insight.frequency,
                    gap_count=p.datetime_insight.gap_count,
                )
            results.append(EnhancedColumnProfileResponse(
                name=p.name,
                dtype=p.dtype,
                role=p.role,
                total_count=p.total_count,
                null_count=p.null_count,
                unique_count=p.unique_count,
                completeness=p.completeness,
                unique_ratio=p.unique_ratio,
                insight=p.insight,
                category_stats=cat_stats,
                numeric_insight=num_insight,
                datetime_insight=dt_insight,
                mean=p.mean,
                std=p.std,
                min_value=str(p.min_value) if p.min_value is not None else None,
                max_value=str(p.max_value) if p.max_value is not None else None,
                distribution=p.distribution,
                outlier_count=p.outlier_count,
                quality_issues=p.quality_issues,
                anomaly_context=p.anomaly_context,
            ))
        return results

    @app.get("/api/profile/{dataset_id}/timeseries", response_model=TimeseriesReportResponse)
    async def get_timeseries_profile(dataset_id: str):
        df = _get_dataset(dataset_id)
        report = profile_timeseries(df)
        return TimeseriesReportResponse(
            datetime_columns=report.datetime_columns,
            profiles=[
                TimeseriesProfileResponse(
                    column=p.column,
                    frequency=p.frequency,
                    is_regular=p.is_regular,
                    gap_count=p.gap_count,
                    gap_locations=p.gap_locations,
                    trend=p.trend,
                    has_seasonality=p.has_seasonality,
                    seasonality_period=p.seasonality_period,
                    is_stationary=p.is_stationary,
                    date_range_start=p.date_range_start,
                    date_range_end=p.date_range_end,
                    total_points=p.total_points,
                )
                for p in report.profiles
            ],
        )

    @app.get("/api/profile/{dataset_id}/correlations", response_model=CorrelationReportResponse)
    async def get_correlations(dataset_id: str):
        df = _get_dataset(dataset_id)
        report = profile_correlations(df)
        return CorrelationReportResponse(
            numeric_correlations=[
                CorrelationPairResponse(
                    column_a=p.column_a, column_b=p.column_b,
                    correlation=p.correlation, method=p.method,
                )
                for p in report.numeric_correlations
            ],
            categorical_associations=[
                CorrelationPairResponse(
                    column_a=p.column_a, column_b=p.column_b,
                    correlation=p.correlation, method=p.method,
                )
                for p in report.categorical_associations
            ],
            functional_dependencies=[
                FunctionalDependencyResponse(
                    determinant=d.determinant, dependent=d.dependent,
                    confidence=d.confidence,
                )
                for d in report.functional_dependencies
            ],
            redundant_columns=report.redundant_columns,
            correlation_matrix=report.correlation_matrix,
        )

    @app.get("/api/profile/{dataset_id}/geo")
    async def get_geo_profile(dataset_id: str):
        df = _get_dataset(dataset_id)
        report = profile_geo(df)
        return {
            "detected_pairs": report.detected_pairs,
            "profiles": [
                {
                    "column_lat": p.column_lat,
                    "column_lng": p.column_lng,
                    "total_points": p.total_points,
                    "valid_points": p.valid_points,
                    "invalid_count": p.invalid_count,
                    "invalid_reasons": p.invalid_reasons,
                    "centroid_lat": p.centroid_lat,
                    "centroid_lng": p.centroid_lng,
                    "bounding_box": p.bounding_box,
                    "spatial_spread_km": p.spatial_spread_km,
                    "density_points_per_sq_km": p.density_points_per_sq_km,
                    "outlier_count": p.outlier_count,
                    "outlier_indices": p.outlier_indices,
                    "outlier_details": p.outlier_details,
                    "cluster_count": p.cluster_count,
                    "clusters": p.clusters,
                }
                for p in report.profiles
            ],
        }

    @app.get("/api/profile/{dataset_id}/schema")
    async def get_schema_recommendation(dataset_id: str, table_name: str = "my_table"):
        df = _get_dataset(dataset_id)
        rec = recommend_schema(df, table_name=table_name)
        return {
            "table_name": rec.table_name,
            "columns": [
                {
                    "name": c.name,
                    "pg_type": c.pg_type,
                    "nullable": c.nullable,
                    "is_primary_key": c.is_primary_key,
                    "is_unique": c.is_unique,
                    "check_constraint": c.check_constraint,
                    "comment": c.comment,
                }
                for c in rec.columns
            ],
            "primary_key": rec.primary_key,
            "unique_constraints": rec.unique_constraints,
            "foreign_key_hints": [
                {
                    "column": fk.column,
                    "references_table": fk.references_table,
                    "references_column": fk.references_column,
                    "confidence": fk.confidence,
                    "reason": fk.reason,
                }
                for fk in rec.foreign_key_hints
            ],
            "normalization_hints": [
                {
                    "column": nh.column,
                    "unique_values": nh.unique_values,
                    "total_rows": nh.total_rows,
                    "suggestion": nh.suggestion,
                }
                for nh in rec.normalization_hints
            ],
            "ddl": rec.ddl,
        }

    @app.get("/api/profile/{dataset_id}/score/detailed", response_model=DetailedQualityScoreResponse)
    async def get_detailed_quality_score(dataset_id: str):
        df = _get_dataset(dataset_id)
        report = score_quality_detailed(df)
        return DetailedQualityScoreResponse(
            overall_score=report.overall_score,
            dimension_scores=report.dimension_scores,
            justifications=[
                QualityJustificationResponse(
                    dimension=j.dimension,
                    score=j.score,
                    explanation=j.explanation,
                    column_impacts=[
                        ColumnImpactResponse(
                            column=i.column, role=i.role, issue=i.issue,
                            severity=i.severity, suggested_fix=i.suggested_fix,
                            estimated_impact=i.estimated_impact,
                        )
                        for i in j.column_impacts
                    ],
                )
                for j in report.justifications
            ],
            row_count=report.row_count,
            column_count=report.column_count,
            worst_columns=report.worst_columns,
            suggested_fixes=report.suggested_fixes,
        )

    @app.get("/api/datasets", response_model=list[DatasetInfo])
    async def list_datasets():
        return [
            DatasetInfo(
                id=did,
                name=f"dataset_{did}",
                rows=len(df),
                columns=len(df.columns),
                column_names=df.columns.tolist(),
            )
            for did, df in _datasets.items()
        ]

    return app


def _get_dataset(dataset_id: str) -> pd.DataFrame:
    if dataset_id not in _datasets:
        raise HTTPException(404, f"Dataset '{dataset_id}' not found. Upload or load one first.")
    return _datasets[dataset_id]


app = create_app()
