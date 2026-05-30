import numpy as np
import pandas as pd
import pytest

from dataprofi.profiler.column_profiler import profile_column, profile_columns, detect_distribution
from dataprofi.profiler.quality_scorer import score_quality
from dataprofi.profiler.ml_readiness import check_ml_readiness


@pytest.fixture
def sample_df():
    np.random.seed(42)
    return pd.DataFrame({
        "id": range(1000),
        "price": np.random.lognormal(10, 1, 1000),
        "category": np.random.choice(["A", "B", "C", "D"], 1000),
        "rating": np.random.uniform(1, 5, 1000),
        "missing_col": [None if i % 10 == 0 else i for i in range(1000)],
        "constant": ["same"] * 1000,
    })


class TestColumnProfiler:
    def test_profile_numeric(self, sample_df):
        profile = profile_column(sample_df["price"])
        assert profile.name == "price"
        assert profile.completeness == 100.0
        assert profile.mean is not None
        assert profile.std is not None
        assert profile.total_count == 1000

    def test_profile_categorical(self, sample_df):
        profile = profile_column(sample_df["category"])
        assert profile.dtype in ("object", "str", "string[python]")
        assert profile.unique_count == 4
        assert profile.distribution == "categorical"

    def test_profile_with_nulls(self, sample_df):
        profile = profile_column(sample_df["missing_col"])
        assert profile.null_count == 100
        assert profile.completeness == 90.0

    def test_profile_all_columns(self, sample_df):
        profiles = profile_columns(sample_df)
        assert len(profiles) == 6

    def test_detect_distribution_normal(self):
        data = pd.Series(np.random.normal(0, 1, 10000))
        assert detect_distribution(data) == "normal"

    def test_detect_distribution_skewed(self):
        data = pd.Series(np.random.lognormal(0, 1, 10000))
        assert "skew" in detect_distribution(data) or detect_distribution(data) == "right_skewed"

    def test_constant_column_issue(self, sample_df):
        profile = profile_column(sample_df["constant"])
        assert any("near-constant" in issue.lower() or "unique" in issue.lower()
                   for issue in profile.quality_issues) or profile.unique_count == 1


class TestQualityScorer:
    def test_overall_score_range(self, sample_df):
        report = score_quality(sample_df)
        assert 0 <= report.overall_score <= 100

    def test_dimension_scores(self, sample_df):
        report = score_quality(sample_df)
        assert "completeness" in report.dimension_scores
        assert "consistency" in report.dimension_scores
        assert "uniqueness" in report.dimension_scores
        assert "validity" in report.dimension_scores
        assert "timeliness" in report.dimension_scores

    def test_complete_df_scores_high(self):
        df = pd.DataFrame({
            "a": range(100),
            "b": np.random.uniform(0, 1, 100),
        })
        report = score_quality(df)
        assert report.dimension_scores["completeness"] == 100.0

    def test_worst_columns_identified(self, sample_df):
        report = score_quality(sample_df)
        assert len(report.worst_columns) <= 5

    def test_row_and_column_count(self, sample_df):
        report = score_quality(sample_df)
        assert report.row_count == 1000
        assert report.column_count == 6


class TestMLReadiness:
    def test_sufficient_data(self, sample_df):
        report = check_ml_readiness(sample_df)
        data_check = next(c for c in report.checks if c.name == "Data Size")
        assert data_check.passed

    def test_insufficient_data(self):
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        report = check_ml_readiness(df)
        data_check = next(c for c in report.checks if c.name == "Data Size")
        assert not data_check.passed

    def test_constant_column_detected(self, sample_df):
        report = check_ml_readiness(sample_df)
        const_check = next(c for c in report.checks if c.name == "Constant Columns")
        assert not const_check.passed

    def test_score_range(self, sample_df):
        report = check_ml_readiness(sample_df)
        assert 0 <= report.score <= 100
