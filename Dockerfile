# ---- Base image ----
FROM python:3.12-slim

# ---- System deps ----
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# ---- Set workdir ----
WORKDIR /app

# ---- Copy dependency files ----
COPY pyproject.toml requirements.txt ./

# ---- Install Python deps ----
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---- Copy application code ----
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .
COPY docker/entrypoint.sh /entrypoint.sh

# ---- Make entrypoint executable ----
RUN chmod +x /entrypoint.sh

# ---- Expose port ----
EXPOSE 8000

# ---- Entrypoint ----
ENTRYPOINT ["/entrypoint.sh"]