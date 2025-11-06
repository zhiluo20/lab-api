# syntax=docker/dockerfile:1

FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"
WORKDIR /app

RUN useradd --create-home appuser
COPY --from=builder /opt/venv /opt/venv
COPY . .
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app.wsgi:app"]
