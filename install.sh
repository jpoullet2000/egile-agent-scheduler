#!/bin/bash
# Installation script for Egile Agent Scheduler

set -e

echo "=================================="
echo "Egile Agent Scheduler Installation"
echo "=================================="

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3.10+ is required but not found"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Using Python: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install the package in editable mode
echo "Installing egile-agent-scheduler..."
pip install -e .

# Install optional dependencies
echo "Installing optional dependencies..."
pip install -e ".[all]"

# Create example configuration if it doesn't exist
if [ ! -f "scheduler.yaml" ]; then
    echo "Creating example configuration..."
    cp examples/scheduler.yaml.example scheduler.yaml
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
# AI Model API Keys (at least one required)
MISTRAL_API_KEY=your_mistral_api_key_here
XAI_API_KEY=your_xai_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Scheduler Database
SCHEDULER_DB_FILE=scheduler.db

# Output Directory
OUTPUT_DIR=output
EOF
    echo "Please edit .env and add your API keys"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Edit scheduler.yaml to configure your jobs"
echo "3. Run 'agent-scheduler --list' to see scheduled jobs"
echo "4. Run 'agent-scheduler --daemon' to start the scheduler"
echo ""
