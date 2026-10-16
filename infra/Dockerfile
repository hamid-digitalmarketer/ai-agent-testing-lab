FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for better layer caching.
COPY pyproject.toml ./
COPY lab ./lab
COPY fixtures ./fixtures
COPY evaluation ./evaluation

RUN pip install --no-cache-dir -e .

CMD ["python", "-m", "evaluation.run"]
