FROM m.daocloud.io/docker.io/library/python:3.12-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY && \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install Python dependencies
RUN unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY && \
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --upgrade pip && \
    pip install -e .

# Create data directories
RUN mkdir -p /data/catalogs/euclid /data/catalogs/desi /data/output

# Expose port
EXPOSE 8000

# Run the MCP server
CMD ["python", "-m", "euclid_crossmatch_mcp.server"]
