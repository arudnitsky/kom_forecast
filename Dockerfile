# Multi-stage build for KOM-Forecast
# Stage 1: Builder - Install dependencies with uv
FROM python:3.13-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Create virtual environment and install dependencies
RUN uv venv /app/.venv && \
    uv pip install --no-cache -r pyproject.toml

# Stage 2: Runtime - Minimal image with only what's needed
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application files
COPY app.py server.py main.py config.py kom_reader.py get_wind_forecast.py ./
COPY templates/ ./templates/
COPY static/ ./static/
COPY kom-list.csv ./

# Set Python path to use virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Expose port 8030
EXPOSE 8030

# Health check
# HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
#     CMD python -c "import requests; requests.get('http://localhost:8030/', timeout=2)"

# Run the application
# Note: Update server.py or override with --host and --port flags
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8030"]
