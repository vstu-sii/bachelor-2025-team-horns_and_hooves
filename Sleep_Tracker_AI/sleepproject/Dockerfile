# Use Python 3.12 base image
FROM python:3.12

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libzstd-dev \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip, setuptools, wheel, virtualenv
RUN pip install --upgrade pip setuptools wheel virtualenv

# Install Poetry
RUN pip install --no-cache-dir poetry

# Optional: clear Poetry cache
RUN poetry cache clear pypi --all

# Install Poetry + export plugin
RUN pip install --no-cache-dir "poetry>=1.8.0" "poetry-plugin-export"

# Copy only pyproject.toml and poetry.lock to leverage Docker cache
COPY pyproject.toml poetry.lock* /app/

# Export dependencies to requirements.txt and install with pip
RUN poetry config virtualenvs.create false \
    && poetry export -f requirements.txt --output requirements.txt --without-hashes \
    && pip install --no-cache-dir -r requirements.txt --retries 10 --timeout 100


# Copy the rest of the project
COPY . .

# Create necessary directories
RUN mkdir -p /app/static /app/media

# Run as non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose the port the app runs on
EXPOSE 8000
