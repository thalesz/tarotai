# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build-time args to receive env values and set them in the image
ARG ACCESS_SECRET_KEY
ARG AZURE_API_KEY
ARG AZURE_ENDPOINT
ARG CONFIRMATION_SECRET_KEY
ARG REFRESH_SECRET_KEY
ARG RESET_PASSWORD_SECRET_KEY
ARG SCM_DO_BUILD_DURING_DEPLOYMENT
ARG SMTP_SECRET_KEY
ARG POSTGRES_URL
ARG FRONTEND_URL

# Persist envs in the runtime image (simple approach per request)
ENV ACCESS_SECRET_KEY=${ACCESS_SECRET_KEY} \
    AZURE_API_KEY=${AZURE_API_KEY} \
    AZURE_ENDPOINT=${AZURE_ENDPOINT} \
    CONFIRMATION_SECRET_KEY=${CONFIRMATION_SECRET_KEY} \
    REFRESH_SECRET_KEY=${REFRESH_SECRET_KEY} \
    RESET_PASSWORD_SECRET_KEY=${RESET_PASSWORD_SECRET_KEY} \
    SCM_DO_BUILD_DURING_DEPLOYMENT=${SCM_DO_BUILD_DURING_DEPLOYMENT} \
    SMTP_SECRET_KEY=${SMTP_SECRET_KEY} \
    POSTGRES_URL=${POSTGRES_URL} \
    FRONTEND_URL=${FRONTEND_URL}

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/docs').read()"

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
