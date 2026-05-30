from __future__ import annotations

from dataprofi.core.types import IndexType
from dataprofi.indexer.analyzer import ColumnAnalysis


INDEX_ANALOGIES = {
    IndexType.BTREE: (
        "Think of a B-tree index like a book's table of contents. Without it, "
        "PostgreSQL reads every single row (like flipping through every page). "
        "With a B-tree index, it can jump directly to matching rows - "
        "like looking up a chapter number and going straight to that page."
    ),
    IndexType.BRIN: (
        "A BRIN index is like knowing that chapters 1-5 cover topics A-E. "
        "Instead of indexing every page, it remembers the range of values in "
        "each block of data. This works beautifully when your data is physically "
        "ordered (like timestamps) - it's tiny and very fast for range queries."
    ),
    IndexType.GIN: (
        "A GIN index is like the index at the back of a textbook - it maps every "
        "keyword to all the pages where it appears. It's perfect for searching "
        "inside arrays, JSON documents, or full-text fields where one row can "
        "contain multiple searchable values."
    ),
    IndexType.GIST: (
        "A GiST index is like a geographic atlas with progressively detailed maps. "
        "It organizes data in a tree of bounding regions, making it ideal for "
        "spatial queries ('find all restaurants within 2km') or range overlaps."
    ),
    IndexType.HASH: (
        "A hash index is like a coat check - you hand over your ticket number "
        "and immediately get your coat. It's blazing fast for exact-match lookups "
        "but can't help with ranges or sorting."
    ),
}


def explain_index(analysis: ColumnAnalysis, table_name: str) -> str:
    if analysis.recommended_index is None:
        return (
            f"No index recommended for '{analysis.name}'. "
            f"{'Column has too few unique values to benefit.' if analysis.cardinality <= 1 else ''}"
            f"{'Column is mostly null.' if analysis.null_ratio > 0.95 else ''}"
        )

    idx_type = analysis.recommended_index
    analogy = INDEX_ANALOGIES.get(idx_type, "")

    lines = [
        f"Index Recommendation: {analysis.name}",
        f"{'=' * 50}",
        "",
        analogy,
        "",
        f"Why {idx_type.value.upper()} for this column:",
    ]

    reasons = _build_reasons(analysis)
    for reason in reasons:
        lines.append(f"  - {reason}")

    lines.extend([
        "",
        f"Column stats:",
        f"  - Cardinality: {analysis.cardinality:,} unique values",
        f"  - Data type: {analysis.dtype}",
        f"  - Null ratio: {analysis.null_ratio:.1%}",
        f"  - Table size: {analysis.total_rows:,} rows",
    ])

    impact = _estimate_impact(analysis)
    lines.extend([
        "",
        f"Expected impact: {impact}",
    ])

    return "\n".join(lines)


def _build_reasons(analysis: ColumnAnalysis) -> list[str]:
    reasons = []
    idx_type = analysis.recommended_index

    if idx_type == IndexType.BTREE:
        if analysis.cardinality_ratio > 0.5:
            reasons.append("High cardinality - many unique values make B-tree very selective")
        else:
            reasons.append(f"{analysis.cardinality} unique values provide good selectivity")
        if analysis.is_numeric:
            reasons.append("Numeric type supports efficient range scans (>, <, BETWEEN)")
        reasons.append("Best general-purpose index for equality and range queries")

    elif idx_type == IndexType.BRIN:
        reasons.append("Data appears physically ordered - BRIN is extremely compact")
        reasons.append("Uses 1000x less disk space than B-tree for ordered data")
        reasons.append("Ideal for append-only tables (logs, time-series, transactions)")

    elif idx_type == IndexType.GIN:
        if analysis.is_array_or_json:
            reasons.append("Contains array/JSON data - GIN indexes all contained values")
            reasons.append("Enables fast @>, ?, ?| operators on JSON/array columns")
        else:
            reasons.append("Long text values suggest full-text search use case")
            reasons.append("GIN with tsvector enables fast keyword search")

    elif idx_type == IndexType.GIST:
        reasons.append("Geometric or range data benefits from GiST's spatial tree")
        reasons.append("Supports overlap, containment, and nearest-neighbor queries")

    return reasons


def _estimate_impact(analysis: ColumnAnalysis) -> str:
    if analysis.total_rows < 1000:
        return "Minimal - table is small enough for sequential scan"

    idx_type = analysis.recommended_index
    selectivity = 1 / analysis.cardinality if analysis.cardinality > 0 else 1

    if idx_type == IndexType.BRIN and analysis.is_sorted:
        return f"High - BRIN on ordered data can skip ~95% of blocks, est. 10-50x speedup"

    if idx_type == IndexType.BTREE:
        if selectivity < 0.01:
            return f"High - index scan reads ~{selectivity * 100:.1f}% of table vs full scan"
        elif selectivity < 0.1:
            return f"Medium - index scan reads ~{selectivity * 100:.0f}% of table"
        else:
            return "Low-medium - moderate selectivity, helpful for sorted output"

    if idx_type == IndexType.GIN:
        return "High for containment/search queries - avoid full-table text scans"

    return "Medium - reduces I/O for filtered queries"
