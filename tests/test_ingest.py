import json
import pandas as pd
import pytest
from pathlib import Path

from dataprofi.ingest.csv_loader import load_csv
from dataprofi.ingest.json_loader import load_json


@pytest.fixture
def tmp_csv(tmp_path):
    csv_path = tmp_path / "test.csv"
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def tmp_json(tmp_path):
    json_path = tmp_path / "test.json"
    data = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}, {"a": 3, "b": "z"}]
    json_path.write_text(json.dumps(data))
    return json_path


class TestCSVLoader:
    def test_load_basic_csv(self, tmp_csv):
        df = load_csv(tmp_csv)
        assert len(df) == 3
        assert list(df.columns) == ["a", "b"]

    def test_load_with_sample(self, tmp_csv):
        df = load_csv(tmp_csv, sample_size=2)
        assert len(df) == 2

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_csv("/nonexistent/path.csv")


class TestJSONLoader:
    def test_load_basic_json(self, tmp_json):
        df = load_json(tmp_json)
        assert len(df) == 3
        assert "a" in df.columns

    def test_load_with_sample(self, tmp_json):
        df = load_json(tmp_json, sample_size=2)
        assert len(df) == 2

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_json("/nonexistent/path.json")
