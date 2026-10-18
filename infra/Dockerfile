FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir git+https://github.com/hamid-digitalmarketer/ai-marketing-shared.git

# Install dependencies first for better layer caching.
COPY pyproject.toml ./
COPY lab ./lab
COPY fixtures ./fixtures
COPY evaluation ./evaluation

RUN pip install --no-cache-dir -e .

CMD ["python", "-m", "evaluation.run"]
