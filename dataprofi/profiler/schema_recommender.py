from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from dataprofi.profiler.column_profiler import classify_column_role
from dataprofi.core.types import ColumnRole


@dataclass
class ColumnSchema:
    name: str
    pg_type: str
    nullable: bool
    is_primary_key: bool = False
    is_unique: bool = False
    check_constraint: str | None = None
    default_value: str | None = None
    comment: str | None = None


@dataclass
class ForeignKeyHint:
    column: str
    references_table: str
    references_column: str
    confidence: float
    reason: str


@dataclass
class NormalizationHint:
    column: str
    unique_values: int
    total_rows: int
    suggestion: str


@dataclass
class SchemaRecommendation:
    table_name: str
    columns: list[ColumnSchema] = field(default_factory=list)
    primary_key: str | None = None
    unique_constraints: list[str] = field(default_factory=list)
    foreign_key_hints: list[ForeignKeyHint] = field(default_factory=list)
    normalization_hints: list[NormalizationHint] = field(default_factory=list)
    ddl: str = ""


def _infer_pg_type(series: pd.Series, role: ColumnRole) -> str:
    dtype = series.dtype
    non_null = series.dropna()

    if role == ColumnRole.BOOLEAN:
        return "BOOLEAN"

    if role == ColumnRole.DATETIME:
        return "TIMESTAMPTZ"

    if dtype.kind == "i":
        if len(non_null) > 0:
            max_val = non_null.max()
            min_val = non_null.min()
            if min_val >= -32768 and max_val <= 32767:
                return "SMALLINT"
            elif min_val >= -2147483648 and max_val <= 2147483647:
                return "INTEGER"
            else:
                return "BIGINT"
        return "INTEGER"

    if dtype.kind == "f":
        if len(non_null) > 0:
            decimals = non_null.apply(lambda x: len(str(x).split(".")[-1]) if "." in str(x) else 0)
            max_dec = int(decimals.max()) if len(decimals) > 0 else 2
            max_digits = len(str(int(abs(non_null.max())))) + max_dec
            if max_dec <= 4 and max_digits <= 12:
                return f"NUMERIC({max_digits},{max_dec})"
        return "DOUBLE PRECISION"

    if dtype.kind == "O":
        if role == ColumnRole.FREE_TEXT:
            return "TEXT"
        if len(non_null) > 0:
            max_len = int(non_null.astype(str).str.len().max())
            if max_len <= 10:
                return "VARCHAR(16)"
            elif max_len <= 50:
                return "VARCHAR(64)"
            elif max_len <= 100:
                return "VARCHAR(128)"
            elif max_len <= 255:
                return "VARCHAR(255)"
            else:
                return "TEXT"
        return "VARCHAR(255)"

    return "TEXT"


def _detect_foreign_keys(df: pd.DataFrame, roles: dict[str, ColumnRole]) -> list[ForeignKeyHint]:
    hints = []
    fk_patterns = {"_id", "id_", "_key", "_code", "_ref"}

    for col in df.columns:
        col_lower = col.lower()
        role = roles.get(col, ColumnRole.MEASURE)

        if role == ColumnRole.ID and col_lower != "id":
            base_name = col_lower.replace("_id", "").replace("id_", "").replace("_key", "").replace("_code", "")
            if base_name and base_name != col_lower and any(p in col_lower for p in fk_patterns):
                ref_table = base_name.rstrip("s") + "s"
                hints.append(ForeignKeyHint(
                    column=col,
                    references_table=ref_table,
                    references_column="id",
                    confidence=0.8,
                    reason=f"Column name '{col}' follows foreign key naming convention",
                ))
                continue

        if role == ColumnRole.CATEGORY:
            nunique = df[col].nunique()
            total = len(df)
            if nunique < 20 and total / nunique > 5:
                hints.append(ForeignKeyHint(
                    column=col,
                    references_table=col.lower().rstrip("s") + "s",
                    references_column="id",
                    confidence=0.5,
                    reason=f"Low-cardinality column ({nunique} values) could reference a lookup table",
                ))

    return hints


def _detect_normalization(df: pd.DataFrame, roles: dict[str, ColumnRole]) -> list[NormalizationHint]:
    hints = []
    total = len(df)

    for col in df.columns:
        role = roles.get(col, ColumnRole.MEASURE)
        if role != ColumnRole.CATEGORY:
            continue
        nunique = df[col].nunique()
        if nunique <= 20 and total > 50 and total / nunique > 10:
            hints.append(NormalizationHint(
                column=col,
                unique_values=nunique,
                total_rows=total,
                suggestion=f"'{col}' has only {nunique} distinct values repeated across {total} rows. Consider a separate lookup table.",
            ))

    return hints


def _generate_ddl(rec: SchemaRecommendation) -> str:
    lines = [f'CREATE TABLE "{rec.table_name}" (']
    col_defs = []
    for col in rec.columns:
        parts = [f'    "{col.name}"', col.pg_type]
        if not col.nullable:
            parts.append("NOT NULL")
        if col.is_primary_key:
            parts.append("PRIMARY KEY")
        elif col.is_unique:
            parts.append("UNIQUE")
        if col.check_constraint:
            parts.append(f"CHECK ({col.check_constraint})")
        if col.default_value:
            parts.append(f"DEFAULT {col.default_value}")
        col_defs.append(" ".join(parts))
    lines.append(",\n".join(col_defs))
    lines.append(");")

    ddl = "\n".join(lines)

    if rec.foreign_key_hints:
        ddl += "\n"
        for fk in rec.foreign_key_hints:
            if fk.confidence >= 0.7:
                ddl += f'\n-- Suggested: ALTER TABLE "{rec.table_name}" ADD CONSTRAINT "fk_{fk.column}" FOREIGN KEY ("{fk.column}") REFERENCES "{fk.references_table}" ("{fk.references_column}");'

    return ddl


_GEO_PATTERNS = {"lat", "latitude", "lng", "lon", "long", "longitude", "x_coord", "y_coord"}


def _is_geo_column(col_name: str) -> bool:
    return col_name.lower().replace(" ", "_") in _GEO_PATTERNS or any(
        p in col_name.lower() for p in ("latitude", "longitude", "lat_", "lng_", "_lat", "_lng")
    )


def recommend_schema(df: pd.DataFrame, table_name: str = "my_table") -> SchemaRecommendation:
    roles = {}
    for col in df.columns:
        roles[col] = classify_column_role(df[col])

    columns = []
    primary_key = None
    unique_constraints = []

    for col in df.columns:
        series = df[col]
        role = roles[col]
        pg_type = _infer_pg_type(series, role)
        nullable = bool(series.isna().any())
        is_pk = False
        is_unique = False

        is_geo = _is_geo_column(col)

        if role == ColumnRole.ID and primary_key is None and not is_geo:
            col_lower = col.lower()
            has_id_name = "id" in col_lower or "key" in col_lower or "code" in col_lower
            is_integer = series.dtype.kind == "i"
            if has_id_name or is_integer:
                is_pk = True
                primary_key = col
                nullable = False
        elif role == ColumnRole.ID and not is_geo:
            is_unique = True
            unique_constraints.append(col)

        if is_geo:
            pg_type = "DOUBLE PRECISION"

        check = None
        if role == ColumnRole.MEASURE and series.dtype.kind in ("i", "f") and not is_geo:
            non_null = series.dropna()
            if len(non_null) > 0 and non_null.min() >= 0:
                check = f'"{col}" >= 0'

        comment = None
        if role == ColumnRole.BOOLEAN:
            comment = "Binary flag"
        elif role == ColumnRole.DATETIME:
            comment = "Temporal column"

        columns.append(ColumnSchema(
            name=col,
            pg_type=pg_type,
            nullable=nullable,
            is_primary_key=is_pk,
            is_unique=is_unique,
            check_constraint=check,
            default_value=None,
            comment=comment,
        ))

    if primary_key is None:
        columns.insert(0, ColumnSchema(
            name="id",
            pg_type="SERIAL",
            nullable=False,
            is_primary_key=True,
            is_unique=False,
            check_constraint=None,
            default_value=None,
            comment="Auto-generated primary key (no natural ID column detected)",
        ))
        primary_key = "id"

    foreign_key_hints = _detect_foreign_keys(df, roles)
    normalization_hints = _detect_normalization(df, roles)

    rec = SchemaRecommendation(
        table_name=table_name,
        columns=columns,
        primary_key=primary_key,
        unique_constraints=unique_constraints,
        foreign_key_hints=foreign_key_hints,
        normalization_hints=normalization_hints,
    )
    rec.ddl = _generate_ddl(rec)
    return rec
