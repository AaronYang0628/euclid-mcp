FROM m.daocloud.io/docker.io/library/python:3.12-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -e .

# Create data directory
RUN mkdir -p /data/catalogs

# Expose port
EXPOSE 8000

# Run the MCP server
CMD ["python", "-m", "euclid_catalog_mcp.server"]
