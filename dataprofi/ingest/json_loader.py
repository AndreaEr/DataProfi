from pathlib import Path

import pandas as pd


def load_json(
    path: str | Path,
    record_path: str | None = None,
    sample_size: int | None = None,
) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    if record_path:
        df = pd.read_json(path)
        if record_path in df.columns:
            df = pd.json_normalize(df[record_path].tolist())
    else:
        df = pd.read_json(path)

    if sample_size and len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=42)

    return df
