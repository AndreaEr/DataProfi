FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY dataprofi/ dataprofi/

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "dataprofi.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
