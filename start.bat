@echo off
REM Start the Egile Agent Scheduler daemon

REM Activate virtual environment
if exist ".venv" (
    call .venv\Scripts\activate.bat
) else (
    echo Error: Virtual environment not found. Run install.bat first.
    pause
    exit /b 1
)

REM Check for config file
if not exist "scheduler.yaml" (
    if exist "scheduler.yaml.example" (
        echo No scheduler.yaml found. Copying from example...
        copy scheduler.yaml.example scheduler.yaml
        echo Please edit scheduler.yaml and configure your jobs.
        pause
        exit /b 1
    ) else (
        echo Error: No scheduler.yaml found
        pause
        exit /b 1
    )
)

REM Start the daemon
echo Starting Egile Agent Scheduler...
agent-scheduler-daemon
