#!/bin/bash
set -e

echo "🚀 Setting up Python development environment (simplified)..."

# Update package list and install essential tools
echo "📦 Installing system dependencies..."
apt-get update
apt-get install -y --no-install-recommends \
    git \
    curl \
    wget \
    ca-certificates \
    build-essential \
    vim \
    nano \
    procps 

# Clean up apt cache to reduce image size
rm -rf /var/lib/apt/lists/*

# Upgrade pip
echo "🐍 Upgrading pip..."
pip install --upgrade pip

# Install common development tools
echo "🛠️  Installing Python development tools..."
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

# Install Node.js (required for Claude Code)
echo "📦 Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# Install Claude Code CLI
echo "🤖 Installing Claude Code..."
npm install -g @anthropic-ai/claude-code

# Install Model Context Protocol Inspector
echo "🔍 Installing Model Context Protocol Inspector..."
npm install -g @modelcontextprotocol/inspector

echo "✅ Setup complete!"
echo ""
echo "🐍 Python version:"
python --version
echo ""
echo "💡 Usage tips:"
echo "  - Create virtualenv: python -m venv .venv"
echo "  - Use Poetry: poetry init && poetry install"
echo "  - Use Pipenv: pipenv install"
echo "  - Use uv (fast): uv pip install -r requirements.txt"
echo ""
