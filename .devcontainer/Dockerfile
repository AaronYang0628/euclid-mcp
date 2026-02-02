FROM m.daocloud.io/docker.io/library/python:3.12-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Update package list and install system dependencies
RUN unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY && \
    apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    ca-certificates \
    build-essential \
    vim \
    nano \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Install Python development tools
RUN unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY && \
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-cache-dir \
    poetry \
    pipenv \
    virtualenv \
    uv \
    ipython \
    black \
    isort \
    flake8 \
    ruff \
    mypy \
    pytest \
    pytest-cov

# Install Node.js 20.x
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI and MCP Inspector
RUN npm install -g @anthropic-ai/claude-code @modelcontextprotocol/inspector

# Set working directory
WORKDIR /workspace

# Display versions
RUN echo "Python version:" && python --version && \
    echo "Node version:" && node --version && \
    echo "npm version:" && npm --version

CMD ["/bin/bash"]
