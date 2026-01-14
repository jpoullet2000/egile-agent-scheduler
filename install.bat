@echo off
REM Installation script for Egile Agent Scheduler

echo ==================================
echo Egile Agent Scheduler Installation
echo ==================================

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python 3.10+ is required but not found
    exit /b 1
)

echo Using Python:
python --version

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install the package in editable mode
echo Installing egile-agent-scheduler...
pip install -e .

REM Install optional dependencies
echo Installing optional dependencies...
pip install -e .[all]

REM Create example configuration if it doesn't exist
if not exist "scheduler.yaml" (
    echo Creating example configuration...
    copy examples\scheduler.yaml.example scheduler.yaml
)

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file...
    (
        echo # AI Model API Keys ^(at least one required^)
        echo MISTRAL_API_KEY=your_mistral_api_key_here
        echo XAI_API_KEY=your_xai_api_key_here
        echo OPENAI_API_KEY=your_openai_api_key_here
        echo.
        echo # Scheduler Database
        echo SCHEDULER_DB_FILE=scheduler.db
        echo.
        echo # Output Directory
        echo OUTPUT_DIR=output
    ) > .env
    echo Please edit .env and add your API keys
)

echo.
echo ✅ Installation complete!
echo.
echo Next steps:
echo 1. Edit .env and add your API keys
echo 2. Edit scheduler.yaml to configure your jobs
echo 3. Run 'agent-scheduler --list' to see scheduled jobs
echo 4. Run 'agent-scheduler --daemon' to start the scheduler
echo.

pause
