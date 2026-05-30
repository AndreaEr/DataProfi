"""DataProfi - Data quality profiling, cleaning, and index recommendation."""

from dataprofi.high_level import analyze, auto_clean, recommend_indexes, to_postgres, serve
from dataprofi.ingest.api_loader import load_from_api

__version__ = "1.0.0"
__all__ = [
    "analyze",
    "auto_clean",
    "recommend_indexes",
    "to_postgres",
    "serve",
    "load_from_api",
]
