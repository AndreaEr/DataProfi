from __future__ import annotations

from dataprofi.core.types import IndexType


def generate_index_sql(
    table_name: str,
    column_name: str,
    index_type: IndexType,
    schema: str = "public",
) -> str:
    safe_col = column_name.replace('"', '""')
    safe_table = table_name.replace('"', '""')
    idx_name = f"idx_{safe_table}_{safe_col}".lower().replace(" ", "_")

    if index_type == IndexType.BTREE:
        return (
            f'CREATE INDEX "{idx_name}" ON "{schema}"."{safe_table}" '
            f'USING btree ("{safe_col}");'
        )
    elif index_type == IndexType.GIN:
        return (
            f'CREATE INDEX "{idx_name}" ON "{schema}"."{safe_table}" '
            f'USING gin ("{safe_col}");'
        )
    elif index_type == IndexType.GIST:
        return (
            f'CREATE INDEX "{idx_name}" ON "{schema}"."{safe_table}" '
            f'USING gist ("{safe_col}");'
        )
    elif index_type == IndexType.BRIN:
        return (
            f'CREATE INDEX "{idx_name}" ON "{schema}"."{safe_table}" '
            f'USING brin ("{safe_col}");'
        )
    elif index_type == IndexType.HASH:
        return (
            f'CREATE INDEX "{idx_name}" ON "{schema}"."{safe_table}" '
            f'USING hash ("{safe_col}");'
        )
    else:
        return (
            f'CREATE INDEX "{idx_name}" ON "{schema}"."{safe_table}" '
            f'("{safe_col}");'
        )


def generate_composite_index_sql(
    table_name: str,
    columns: list[str],
    index_type: IndexType = IndexType.BTREE,
    schema: str = "public",
) -> str:
    safe_table = table_name.replace('"', '""')
    safe_cols = [c.replace('"', '""') for c in columns]
    idx_name = f"idx_{safe_table}_{'_'.join(safe_cols)}".lower().replace(" ", "_")
    col_list = ", ".join(f'"{c}"' for c in safe_cols)

    return (
        f'CREATE INDEX "{idx_name}" ON "{schema}"."{safe_table}" '
        f"USING {index_type.value} ({col_list});"
    )
