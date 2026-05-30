import numpy as np
import pandas as pd
import pytest

from dataprofi.cleaner.missing import handle_missing
from dataprofi.cleaner.duplicates import remove_duplicates
from dataprofi.cleaner.outliers import handle_outliers
from dataprofi.cleaner.types import coerce_types
from dataprofi.cleaner.pipeline import CleaningPipeline


@pytest.fixture
def df_with_issues():
    return pd.DataFrame({
        "price": [100, 200, None, 400, 500, None, 700, 800, 900, 10000],
        "name": ["Alice", "Bob", "Alice", "Bob", "Charlie", "Alice", "Bob", "Charlie", "Alice", "Bob"],
        "age": ["25", "30", "25", "30", "35", "bad", "30", "35", "25", "30"],
        "score": [1.0, 2.0, 1.0, 2.0, 3.0, 1.0, 2.0, 3.0, 1.0, 2.0],
    })


class TestMissingValues:
    def test_median_imputation(self, df_with_issues):
        result, actions = handle_missing(df_with_issues, strategy="median", columns=["price"])
        assert result["price"].isna().sum() == 0
        assert len(actions) == 1
        assert actions[0].strategy == "median_imputation"

    def test_mean_imputation(self, df_with_issues):
        result, actions = handle_missing(df_with_issues, strategy="mean", columns=["price"])
        assert result["price"].isna().sum() == 0

    def test_mode_imputation(self, df_with_issues):
        result, actions = handle_missing(df_with_issues, strategy="mode", columns=["name"])
        assert result["name"].isna().sum() == 0

    def test_drop_strategy(self, df_with_issues):
        result, actions = handle_missing(df_with_issues, strategy="drop", columns=["price"])
        assert len(result) == 8

    def test_constant_fill(self, df_with_issues):
        result, actions = handle_missing(
            df_with_issues, strategy="constant", columns=["price"], constant_value=-1
        )
        assert (result["price"] == -1).sum() == 2


class TestDuplicates:
    def test_exact_dedup(self):
        df = pd.DataFrame({"a": [1, 2, 1, 2], "b": ["x", "y", "x", "y"]})
        result, actions = remove_duplicates(df, method="exact")
        assert len(result) == 2
        assert actions[0].rows_affected == 2

    def test_no_duplicates(self):
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        result, actions = remove_duplicates(df, method="exact")
        assert len(result) == 3
        assert len(actions) == 0

    def test_column_specific_dedup(self):
        df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "y", "z"]})
        result, actions = remove_duplicates(df, method="exact", columns=["a"])
        assert len(result) == 2


class TestOutliers:
    def test_iqr_clip(self):
        data = list(range(100)) + [10000]
        df = pd.DataFrame({"val": data})
        result, actions = handle_outliers(df, method="iqr", action="clip", columns=["val"])
        assert result["val"].max() < 10000
        assert len(actions) == 1

    def test_zscore_remove(self):
        np.random.seed(42)
        data = np.random.normal(0, 1, 100).tolist() + [100]
        df = pd.DataFrame({"val": data})
        result, actions = handle_outliers(df, method="zscore", action="remove", threshold=3)
        assert len(result) < 101

    def test_flag_only(self):
        data = list(range(100)) + [10000]
        df = pd.DataFrame({"val": data})
        result, actions = handle_outliers(df, method="iqr", action="flag", columns=["val"])
        assert "val_is_outlier" in result.columns


class TestTypeCoercion:
    def test_auto_numeric_coercion(self):
        df = pd.DataFrame({"num": pd.array(["1", "2", "3", "4", "5"], dtype="object")})
        result, actions = coerce_types(df, columns=["num"])
        assert result["num"].dtype in ("int64", "float64")

    def test_explicit_type_map(self):
        df = pd.DataFrame({"val": ["1", "2", "bad", "4"]})
        result, actions = coerce_types(df, type_map={"val": "numeric"})
        assert result["val"].dtype == "float64"
        assert result["val"].isna().sum() == 1


class TestPipeline:
    def test_full_pipeline(self, df_with_issues):
        pipeline = CleaningPipeline()
        pipeline.add_step("duplicates", method="exact")
        pipeline.add_step("missing", strategy="median", columns=["price"])
        pipeline.add_step("outliers", method="iqr", action="clip", columns=["price"])

        result = pipeline.run(df_with_issues)
        report = pipeline.report()

        assert result["price"].isna().sum() == 0
        assert report.rows_before == 10
        assert len(report.actions) > 0
        assert report.score_after >= report.score_before

    def test_pipeline_summary(self, df_with_issues):
        pipeline = CleaningPipeline()
        pipeline.add_step("missing", strategy="median", columns=["price"])
        pipeline.run(df_with_issues)
        summary = pipeline.summary()
        assert "Cleaning Pipeline Report" in summary
