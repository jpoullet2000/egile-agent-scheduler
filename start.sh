#!/bin/bash
# Start the Egile Agent Scheduler daemon

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Error: Virtual environment not found. Run install.sh first."
    exit 1
fi

# Load environment
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check for config file
if [ ! -f "scheduler.yaml" ]; then
    if [ -f "scheduler.yaml.example" ]; then
        echo "No scheduler.yaml found. Copying from example..."
        cp scheduler.yaml.example scheduler.yaml
        echo "Please edit scheduler.yaml and configure your jobs."
        exit 1
    else
        echo "Error: No scheduler.yaml found"
        exit 1
    fi
fi

# Start the daemon
echo "Starting Egile Agent Scheduler..."
agent-scheduler-daemon
