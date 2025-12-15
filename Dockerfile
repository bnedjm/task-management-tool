# Multi-stage Dockerfile for production deployment

# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir --no-warn-script-location -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user first
RUN useradd -m -u 1000 appuser && \
    mkdir -p /data /app/logs && \
    chown -R appuser:appuser /data /app/logs

# Copy Python dependencies from builder and set ownership
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser src/ ./src/

# Switch to non-root user
USER appuser

# Make sure scripts in .local are usable
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app

# Production environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check with better error handling
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; import urllib.request; \
    try: \
        urllib.request.urlopen('http://localhost:8000/health', timeout=5).read(); \
        sys.exit(0) \
    except Exception: \
        sys.exit(1)" || exit 1

EXPOSE 8000

# Run the application with production settings
# Using --workers for production (adjust based on CPU cores)
# Using --log-level warning to reduce noise
# Using --access-log for request logging
CMD ["uvicorn", "src.api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--log-level", "warning", \
     "--access-log", \
     "--no-use-colors", \
     "--proxy-headers"]
