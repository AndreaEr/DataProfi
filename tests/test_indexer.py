import numpy as np
import pandas as pd
import pytest

from dataprofi.indexer.analyzer import analyze_column_for_index
from dataprofi.indexer.generator import generate_index_sql, generate_composite_index_sql
from dataprofi.indexer.explainer import explain_index
from dataprofi.indexer.recommender import recommend_indexes
from dataprofi.core.types import IndexType


@pytest.fixture
def large_df():
    np.random.seed(42)
    n = 10000
    return pd.DataFrame({
        "id": range(n),
        "timestamp": pd.date_range("2020-01-01", periods=n, freq="h"),
        "category": np.random.choice(["A", "B", "C", "D", "E"] * 20, n),
        "price": np.random.lognormal(5, 1, n),
        "description": ["Long text description " * 10] * n,
        "tags": ['["tag1", "tag2"]'] * n,
        "constant": [1] * n,
    })


class TestColumnAnalyzer:
    def test_high_cardinality_numeric(self, large_df):
        analysis = analyze_column_for_index(large_df["id"], len(large_df))
        assert analysis.recommended_index == IndexType.BTREE
        assert analysis.cardinality == 10000

    def test_sorted_column_gets_brin(self, large_df):
        analysis = analyze_column_for_index(large_df["id"], len(large_df))
        assert analysis.is_sorted
        assert analysis.recommended_index in (IndexType.BTREE, IndexType.BRIN)

    def test_json_column_gets_gin(self, large_df):
        analysis = analyze_column_for_index(large_df["tags"], len(large_df))
        assert analysis.is_array_or_json
        assert analysis.recommended_index == IndexType.GIN

    def test_constant_column_no_index(self, large_df):
        analysis = analyze_column_for_index(large_df["constant"], len(large_df))
        assert analysis.recommended_index is None

    def test_categorical_column(self, large_df):
        analysis = analyze_column_for_index(large_df["category"], len(large_df))
        assert analysis.cardinality_ratio < 0.01


class TestSQLGenerator:
    def test_btree_sql(self):
        sql = generate_index_sql("users", "email", IndexType.BTREE)
        assert "USING btree" in sql
        assert "idx_users_email" in sql
        assert "users" in sql

    def test_gin_sql(self):
        sql = generate_index_sql("posts", "tags", IndexType.GIN)
        assert "USING gin" in sql

    def test_brin_sql(self):
        sql = generate_index_sql("logs", "created_at", IndexType.BRIN)
        assert "USING brin" in sql

    def test_composite_index(self):
        sql = generate_composite_index_sql("orders", ["user_id", "created_at"])
        assert "user_id" in sql
        assert "created_at" in sql
        assert "idx_orders_user_id_created_at" in sql

    def test_schema_included(self):
        sql = generate_index_sql("users", "email", IndexType.BTREE, schema="app")
        assert '"app"."users"' in sql


class TestExplainer:
    def test_btree_explanation(self, large_df):
        analysis = analyze_column_for_index(large_df["id"], len(large_df))
        explanation = explain_index(analysis, "products")
        assert "B-tree" in explanation or "btree" in explanation.lower() or "BRIN" in explanation
        assert "products" in explanation or "id" in explanation

    def test_no_index_explanation(self, large_df):
        analysis = analyze_column_for_index(large_df["constant"], len(large_df))
        explanation = explain_index(analysis, "test")
        assert "No index recommended" in explanation


class TestRecommender:
    def test_recommendations_generated(self, large_df):
        recs = recommend_indexes(large_df, table_name="test_table")
        assert len(recs) > 0

    def test_recommendations_have_sql(self, large_df):
        recs = recommend_indexes(large_df, table_name="test_table")
        for rec in recs:
            assert rec.sql.startswith("CREATE INDEX")

    def test_recommendations_sorted_by_priority(self, large_df):
        recs = recommend_indexes(large_df, table_name="test_table")
        priority_order = {"high": 0, "medium": 1, "low": 2}
        priorities = [priority_order[r.priority] for r in recs]
        assert priorities == sorted(priorities)

    def test_constant_column_excluded(self, large_df):
        recs = recommend_indexes(large_df, table_name="test_table")
        rec_columns = [r.column for r in recs]
        assert "constant" not in rec_columns
