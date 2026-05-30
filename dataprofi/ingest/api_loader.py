from __future__ import annotations

import httpx
import pandas as pd

from dataprofi.core.config import Config

_config = Config()
MAX_ROWS = _config.max_rows
MAX_RESPONSE_MB = _config.max_response_mb
TIMEOUT_SECONDS = _config.api_timeout_seconds


def _extract_records(data: dict | list, record_path: str | None = None) -> list[dict]:
    if isinstance(data, list):
        return data

    if record_path:
        parts = record_path.strip(".").split(".")
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                raise ValueError(
                    f"Path '{record_path}' not found in response. "
                    f"Available keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}"
                )
        if isinstance(current, list):
            return current
        raise ValueError(f"Path '{record_path}' resolved to {type(current).__name__}, expected a list.")

    if isinstance(data, dict):
        for key in ("data", "results", "records", "items", "rows", "entries"):
            if key in data and isinstance(data[key], list):
                return data[key]
            if key in data and isinstance(data[key], dict):
                for subkey, subval in data[key].items():
                    if isinstance(subval, list) and len(subval) > 0 and isinstance(subval[0], dict):
                        return subval
        for key, val in data.items():
            if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                return val

    raise ValueError(
        "Could not find a list of records in the response. "
        "Specify a record_path (e.g. 'data.records') to locate the data."
    )


def load_from_api(
    url: str,
    record_path: str | None = None,
    limit: int = 5000,
) -> pd.DataFrame:
    limit = min(limit, MAX_ROWS)

    if not url.startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")

    from urllib.parse import urlparse
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if host in ("localhost", "127.0.0.1", "0.0.0.0", "::1") or host.startswith("192.168.") or host.startswith("10."):
        raise ValueError("Cannot load from local/private network addresses.")

    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS, follow_redirects=True) as client:
            response = client.get(url)
    except httpx.ConnectError as e:
        if "CERTIFICATE_VERIFY_FAILED" in str(e):
            with httpx.Client(timeout=TIMEOUT_SECONDS, verify=False, follow_redirects=True) as client:  # noqa: S501
                response = client.get(url)
        else:
            raise ValueError("Could not connect to the server. Check the URL is correct.")
    except httpx.TimeoutException:
        raise ValueError(f"Request timed out after {TIMEOUT_SECONDS}s. The API may be slow or unreachable.")

    if response.status_code != 200:
        raise ValueError(f"API returned status {response.status_code}. Check the URL is correct and accessible.")

    content_length = len(response.content)
    if content_length > MAX_RESPONSE_MB * 1024 * 1024:
        raise ValueError(
            f"Response is too large ({content_length / 1024 / 1024:.0f} MB, limit is {MAX_RESPONSE_MB} MB)."
        )

    try:
        data = response.json()
    except Exception:
        raise ValueError("Response is not valid JSON. Only JSON APIs are supported.")

    records = _extract_records(data, record_path)

    if not records:
        raise ValueError("API returned an empty dataset (0 records).")

    if len(records) > limit:
        records = records[:limit]

    df = pd.json_normalize(records, sep="_")

    if df.empty:
        raise ValueError("Could not parse records into a table. Check the API response format.")

    return df
