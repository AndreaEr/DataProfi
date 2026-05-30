from pathlib import Path

import pandas as pd


def load_csv(
    path: str | Path,
    encoding: str = "utf-8",
    sample_size: int | None = None,
) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    df = pd.read_csv(path, encoding=encoding)

    if sample_size and len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=42)

    return df
