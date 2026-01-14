# Egile Agent Scheduler - Implementation Summary

## Overview

The **Egile Agent Scheduler** is a new package that automates agent and team workflows based on cron-like schedules. It's designed to work seamlessly with the Egile Agent Hub and can run agents or teams at specified times, generating outputs in various formats.

## Key Features

### 1. **Cron-Based Scheduling**
- Standard cron syntax support (5-field format)
- Dictionary-based schedule for readability
- APScheduler backend for reliable execution

### 2. **Agent & Team Execution**
- Run individual agents or entire teams
- Full integration with egile-agent-hub
- Shared database and configuration
- Plugin support (investment, prospectfinder, x-twitter, slidedeck, etc.)

### 3. **Multiple Output Formats**
- **PDF**: Professional reports with ReportLab
- **Markdown**: Documentation-friendly
- **HTML**: Web-ready styled pages
- **JSON**: Structured data
- **Text**: Simple logs

### 4. **Flexible Configuration**
- YAML-based job definitions
- Reusable agent configurations
- Environment variable support
- Integration with hub's agents.yaml

## Architecture

```
egile-agent-scheduler/
├── src/egile_agent_scheduler/
│   ├── __init__.py           # Package initialization
│   ├── config.py             # Configuration loading and validation
│   ├── scheduler.py          # Main scheduler with APScheduler
│   ├── executor.py           # Agent/team execution engine
│   ├── output_handler.py     # Output format handlers
│   ├── cli.py                # Command-line interface
│   └── daemon.py             # Daemon mode runner
├── examples/
│   ├── scheduler.yaml.example              # Full example config
│   └── investment_scheduler_example.py     # Python example
├── pyproject.toml            # Package metadata
├── README.md                 # Full documentation
├── QUICKSTART.md             # Quick start guide
├── LICENSE                   # MIT license
└── install.sh/bat            # Installation scripts
```

## Core Components

### 1. Config Module (`config.py`)
- Loads and validates YAML configuration
- Validates job schedules (cron syntax)
- Ensures agent/team references are valid
- Provides configuration access methods

### 2. Scheduler Module (`scheduler.py`)
- Main `AgentScheduler` class
- Integrates with APScheduler (AsyncIOScheduler)
- Parses cron expressions and dict schedules
- Manages job lifecycle (add, remove, run)
- Handles signals for graceful shutdown

### 3. Executor Module (`executor.py`)
- `AgentExecutor` class for running agents/teams
- Creates Agno agents from configuration
- Manages plugin loading and tool registration
- Caches agents and teams for efficiency
- Integrates with egile-agent-hub configuration

### 4. Output Handler Module (`output_handler.py`)
- `OutputHandler` class for saving results
- Supports PDF, Markdown, HTML, JSON, and text
- Automatic timestamping of output files
- PDF generation with professional formatting
- Markdown-to-HTML conversion

### 5. CLI Module (`cli.py`)
- Command-line interface
- `--list`: Show scheduled jobs
- `--run JOB_NAME`: Run job once
- `--daemon`: Run continuously
- `--config PATH`: Custom config file
- `--verbose`: Enable debug logging

### 6. Daemon Module (`daemon.py`)
- Simple daemon mode runner
- Loads default configuration
- Runs scheduler continuously
- Handles interrupts gracefully

## Configuration Format

### Jobs

```yaml
jobs:
  - name: job_name              # Unique identifier
    description: "..."           # Optional description
    schedule: "0 9 * * *"        # Cron expression or dict
    agent: agent_name            # Agent to run (or team)
    team: team_name              # Team to run (or agent)
    task: "..."                  # Task prompt
    output:                      # Output configuration
      type: pdf                  # Output format
      path: output/dir           # Output directory
      filename: base_name        # Base filename
      title: "Title"             # PDF title
    notify_on_error: true        # Send notifications
```

### Schedule Formats

**Cron string:**
```yaml
schedule: "0 9 * * *"           # Daily at 9 AM
schedule: "0 9 * * 1-5"         # Weekdays at 9 AM
schedule: "0 */6 * * *"         # Every 6 hours
```

**Dictionary:**
```yaml
schedule:
  hour: 9
  minute: 0
  day_of_week: "mon-fri"
```

### Agents & Teams

```yaml
agents:
  - name: investment
    plugin_type: investment
    mcp_port: 8004
    instructions:
      - "Instruction 1"
      - "Instruction 2"

teams:
  - name: research_team
    members:
      - agent1
      - agent2
    instructions:
      - "Team instruction"
```

## Use Case: Daily Investment Report

### Configuration

```yaml
jobs:
  - name: daily_investment_report
    schedule: "0 9 * * *"        # 9 AM daily
    agent: investment
    task: |
      Generate an investment report:
      1. Analyze current portfolio
      2. Sell recommendations
      3. Buy opportunities
      4. Risk assessment
    output:
      type: pdf
      path: output/investments
      title: "Daily Investment Report"

agents:
  - name: investment
    plugin_type: investment
    mcp_port: 8004
```

### Workflow

1. **Scheduler starts** at 9:00 AM daily
2. **Executor creates** investment agent with plugin
3. **Agent analyzes** portfolio using MCP tools
4. **Agent generates** report text
5. **Output handler** converts to PDF
6. **PDF saved** to `output/investments/investment_report_YYYYMMDD_HHMMSS.pdf`

## Installation & Usage

### Install

```bash
cd egile-agent-scheduler
./install.sh  # or install.bat on Windows
```

### Configure

Edit `scheduler.yaml` and `.env`:

```yaml
# scheduler.yaml
jobs:
  - name: my_job
    schedule: "0 9 * * *"
    agent: my_agent
    task: "Do something"
```

```bash
# .env
MISTRAL_API_KEY=your_key_here
```

### Run

```bash
# List jobs
agent-scheduler --list

# Test run
agent-scheduler --run my_job

# Start daemon
agent-scheduler --daemon
```

## Integration with Egile Agent Hub

The scheduler can:

1. **Load agents from hub**: Reference agents defined in hub's `agents.yaml`
2. **Use hub teams**: Schedule entire teams from the hub
3. **Share configuration**: Reuse agent definitions
4. **Share database**: Common conversation history

**Example:**

```yaml
# scheduler.yaml
jobs:
  - name: daily_prospects
    schedule: "0 10 * * *"
    agent: prospectfinder  # Defined in hub's agents.yaml
    task: "Find prospects in fintech"

# No need to redefine agent - loaded from hub
```

## Advanced Features

### Multiple Schedules

```yaml
jobs:
  - name: business_hours_check
    schedule:
      hour: "9-17"
      minute: 0
      day_of_week: "mon-fri"
    agent: monitor
    task: "Check system status"
```

### Custom Models

```yaml
agents:
  - name: my_agent
    model_override:
      provider: openai
      model: gpt-4
```

### Error Notifications

```yaml
jobs:
  - name: critical_job
    notify_on_error: true
    # Sends notification on failure
```

## Dependencies

- `agno>=2.3.0` - Agent framework
- `apscheduler>=3.10.0` - Job scheduling
- `croniter>=2.0.0` - Cron parsing
- `reportlab>=4.0.0` - PDF generation
- `pyyaml>=6.0` - YAML parsing
- `python-dotenv>=1.0.0` - Environment variables
- `httpx>=0.27.0` - HTTP client

## Command-Line Interface

```bash
agent-scheduler --help

Options:
  -c, --config PATH    Config file (default: scheduler.yaml)
  -l, --list           List scheduled jobs
  -r, --run JOB_NAME   Run job once
  -d, --daemon         Run as daemon
  -v, --verbose        Verbose logging
```

## Output Examples

### PDF Report
- Professional formatting
- Title page with timestamp
- Markdown-to-PDF conversion
- Automatic pagination

### Markdown
- Raw content preserved
- Great for version control
- Easy to convert to other formats

### HTML
- Styled with CSS
- Responsive design
- Embedded timestamp

### JSON
- Structured data
- Timestamp included
- Easy to parse

## Future Enhancements

Possible additions:
- Email notifications
- Webhook integrations
- Job dependencies (run job B after job A)
- Conditional scheduling (only run if condition met)
- Job history and logs
- Web UI for configuration
- Retry logic for failed jobs
- Parallel job execution

## Example Scenarios

### 1. Daily Investment Reports
```yaml
schedule: "0 9 * * *"
output: pdf
```

### 2. Weekly Social Media Content
```yaml
schedule: "0 14 * * 5"  # Friday 2 PM
team: content_team
```

### 3. Hourly Market Monitoring
```yaml
schedule: "0 9-16 * * 1-5"  # Trading hours
output: json
```

### 4. Monthly Analysis
```yaml
schedule: "0 10 1 * *"  # First of month
output: pdf
```

## Summary

The Egile Agent Scheduler provides:
- ✅ Automated agent/team workflows
- ✅ Flexible cron-based scheduling
- ✅ Multiple output formats
- ✅ Hub integration
- ✅ Easy configuration
- ✅ Professional PDF reports
- ✅ Production-ready daemon mode

Perfect for automating recurring AI tasks like daily reports, periodic analysis, content generation, and monitoring.
