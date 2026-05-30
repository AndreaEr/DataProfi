from dataprofi.ingest.csv_loader import load_csv
from dataprofi.ingest.json_loader import load_json
from dataprofi.ingest.api_loader import load_from_api
from dataprofi.ingest.postgres_loader import load_from_postgres

__all__ = ["load_csv", "load_json", "load_from_api", "load_from_postgres"]
