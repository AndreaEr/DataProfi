import re

import pandas as pd
from sqlalchemy import create_engine, text


def _validate_identifier(name: str) -> str:
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise ValueError(f"Invalid SQL identifier: '{name}'")
    return name


def load_from_postgres(
    table_name: str,
    connection_string: str,
    schema: str = "public",
    limit: int | None = None,
) -> pd.DataFrame:
    _validate_identifier(table_name)
    _validate_identifier(schema)

    engine = create_engine(connection_string)

    query = f'SELECT * FROM "{schema}"."{table_name}"'
    if limit and isinstance(limit, int) and limit > 0:
        query += f" LIMIT {int(limit)}"

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    return df


def get_table_info(table_name: str, connection_string: str, schema: str = "public") -> dict:
    _validate_identifier(table_name)
    _validate_identifier(schema)

    engine = create_engine(connection_string)

    with engine.connect() as conn:
        columns_query = text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = :table AND table_schema = :schema
            ORDER BY ordinal_position
        """)
        columns = conn.execute(columns_query, {"table": table_name, "schema": schema}).fetchall()

        indexes_query = text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = :table AND schemaname = :schema
        """)
        indexes = conn.execute(indexes_query, {"table": table_name, "schema": schema}).fetchall()

        count_query = text(f'SELECT COUNT(*) FROM "{schema}"."{table_name}"')
        row_count = conn.execute(count_query).scalar()

    return {
        "table_name": table_name,
        "schema": schema,
        "row_count": row_count,
        "columns": [
            {
                "name": c[0],
                "type": c[1],
                "nullable": c[2] == "YES",
                "default": c[3],
            }
            for c in columns
        ],
        "existing_indexes": [
            {"name": idx[0], "definition": idx[1]} for idx in indexes
        ],
    }
