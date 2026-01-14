# Egile Agent Scheduler

**Automate your AI agents and teams** - Schedule tasks to run automatically at specific times using cron-like scheduling.

## Overview

Egile Agent Scheduler allows you to automate agent and team workflows by scheduling them to run at specific times. Perfect for:

- 📊 **Daily Reports**: Generate investment reports, market analysis, or summaries
- 📧 **Automated Outreach**: Schedule social media posts or prospect research
- 🔄 **Periodic Tasks**: Run maintenance tasks, data collection, or monitoring
- 🤖 **Agent Workflows**: Coordinate complex multi-agent workflows on a schedule

## Features

✅ **Cron-Like Scheduling**
- Standard cron syntax support
- Flexible time expressions (daily, weekly, monthly, hourly)
- Dictionary-based schedule configuration for clarity

✅ **Agent & Team Support**
- Run individual agents or entire teams
- Full integration with egile-agent-hub
- Share configuration across hub and scheduler

✅ **Multiple Output Formats**
- PDF reports with professional formatting
- Markdown for documentation
- HTML for web publishing
- JSON for data processing
- Plain text for simple logs

✅ **Easy Configuration**
- YAML-based job definitions
- Reusable agent configurations
- Environment variable support

## Quick Start

### 1. Installation

**Windows:**
```bash
cd egile-agent-scheduler
install.bat
```

**Linux/Mac:**
```bash
cd egile-agent-scheduler
chmod +x install.sh
./install.sh
```

### 2. Configure Your Jobs

Edit `scheduler.yaml`:

```yaml
jobs:
  - name: daily_investment_report
    description: "Generate daily investment report"
    schedule: "0 9 * * *"  # Every day at 9:00 AM
    agent: investment
    task: |
      Generate a comprehensive investment report:
      1. Analyze current holdings
      2. Provide sell/buy recommendations
      3. Include risk assessment
    output:
      type: pdf
      path: output/investments
      title: "Daily Investment Report"

agents:
  - name: investment
    description: "Investment analysis agent"
    plugin_type: investment
    mcp_port: 8004
```

### 3. Set Up Environment

Edit `.env`:

```bash
# AI Model API Keys (at least one required)
MISTRAL_API_KEY=your_mistral_api_key_here
XAI_API_KEY=your_xai_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Scheduler Database
SCHEDULER_DB_FILE=scheduler.db

# Output Directory
OUTPUT_DIR=output
```

### 4. Run the Scheduler

**List scheduled jobs:**
```bash
agent-scheduler --list
```

**Run a job once (for testing):**
```bash
agent-scheduler --run daily_investment_report
```

**Start the daemon:**
```bash
agent-scheduler --daemon
```

Or use the shortcut:
```bash
agent-scheduler-daemon
```

## Schedule Syntax

### Cron Format

Standard cron expressions with 5 fields:

```
┌────────── minute (0-59)
│ ┌──────── hour (0-23)
│ │ ┌────── day of month (1-31)
│ │ │ ┌──── month (1-12)
│ │ │ │ ┌── day of week (0-6, Sunday=0)
│ │ │ │ │
* * * * *
```

**Examples:**

```yaml
# Daily at 9:00 AM
schedule: "0 9 * * *"

# Weekdays at 9:00 AM
schedule: "0 9 * * 1-5"

# Every 6 hours
schedule: "0 */6 * * *"

# First day of month at 8:30 AM
schedule: "30 8 1 * *"

# Every Monday at 10:00 AM
schedule: "0 10 * * 1"
```

### Dictionary Format

For better readability:

```yaml
# Daily at 9:00 AM
schedule:
  hour: 9
  minute: 0

# Mondays at 9:00 AM
schedule:
  hour: 9
  minute: 0
  day_of_week: mon

# First Friday of each month at 5:00 PM
schedule:
  hour: 17
  minute: 0
  day_of_week: fri
  day: "1-7"
```

## Configuration Reference

### Job Configuration

```yaml
jobs:
  - name: job_name              # Required: Unique job identifier
    description: "..."           # Optional: Human-readable description
    schedule: "0 9 * * *"        # Required: When to run (cron or dict)
    agent: agent_name            # Required (or team): Agent to run
    team: team_name              # Required (or agent): Team to run
    task: "..."                  # Required: Task/prompt for agent/team
    output:                      # Optional: Output configuration
      type: pdf                  # pdf, markdown, html, json, text
      path: output/reports       # Output directory
      filename: report           # Base filename (auto-timestamped)
      title: "Report Title"      # Title for PDF reports
    notify_on_error: true        # Optional: Send notification on failure
```

### Agent Configuration

```yaml
agents:
  - name: agent_name
    description: "..."
    plugin_type: investment      # Plugin type (prospectfinder, x-twitter, etc.)
    mcp_port: 8004              # MCP server port
    instructions:               # Agent instructions
      - "Instruction 1"
      - "Instruction 2"
    model_override: gpt-4       # Optional: Override default model
```

### Team Configuration

```yaml
teams:
  - name: team_name
    description: "..."
    members:                    # List of agent names
      - agent1
      - agent2
    instructions:
      - "Team instruction 1"
```

## Use Cases

### Daily Investment Report

Generate a PDF report every morning with investment recommendations:

```yaml
jobs:
  - name: daily_investment_report
    schedule: "0 9 * * *"
    agent: investment
    task: |
      Analyze my portfolio and provide:
      1. Stocks to consider selling with reasoning
      2. Buy opportunities based on current market
      3. Risk assessment and diversification advice
    output:
      type: pdf
      path: output/investments
      title: "Daily Investment Report"
```

### Weekly Social Media Content

Create social media content every Friday:

```yaml
jobs:
  - name: weekly_social_content
    schedule: "0 14 * * 5"  # Friday at 2:00 PM
    team: content_team
    task: |
      Create 5 engaging social media posts for next week
      based on recent industry trends and our portfolio performance.
    output:
      type: markdown
      path: output/social
```

### Hourly Market Monitoring

Monitor market conditions during trading hours:

```yaml
jobs:
  - name: market_watch
    schedule:
      hour: "9-16"    # 9 AM to 4 PM
      minute: 0
      day_of_week: "mon-fri"
    agent: investment
    task: "Check for significant movements in my portfolio"
    output:
      type: json
      path: output/market_watch
```

## Integration with Egile Agent Hub

The scheduler seamlessly integrates with egile-agent-hub:

1. **Shared Configuration**: Use the same `agents.yaml` from the hub
2. **Reuse Agents**: Reference hub agents in your jobs
3. **Teams Support**: Schedule entire teams defined in the hub
4. **Unified Database**: Share conversation history and state

**Example using hub agents:**

```yaml
# scheduler.yaml
jobs:
  - name: daily_prospect_search
    schedule: "0 10 * * *"
    agent: prospectfinder  # Defined in hub's agents.yaml
    task: "Find 10 prospects in the fintech sector in UK"

# No need to redefine agents - scheduler loads from hub
```

## Output Formats

### PDF Reports

Professional reports with formatting:

```yaml
output:
  type: pdf
  path: output/reports
  title: "Investment Analysis"
  filename: analysis
```

Features:
- Title page with timestamp
- Markdown-to-PDF conversion
- Professional styling
- Automatic pagination

### Markdown

Web-friendly documentation:

```yaml
output:
  type: markdown
  path: output/docs
  filename: report
```

### HTML

Styled HTML pages:

```yaml
output:
  type: html
  path: output/web
  filename: report
```

### JSON

Structured data for processing:

```yaml
output:
  type: json
  path: output/data
  filename: results
```

## Command-Line Interface

```bash
# List all scheduled jobs
agent-scheduler --list

# Run a specific job once
agent-scheduler --run job_name

# Start daemon mode
agent-scheduler --daemon

# Use custom config file
agent-scheduler --config /path/to/scheduler.yaml --daemon

# Enable verbose logging
agent-scheduler --verbose --daemon
```

## Environment Variables

```bash
# Database file
SCHEDULER_DB_FILE=scheduler.db

# Output directory
OUTPUT_DIR=output

# AI Model API Keys
MISTRAL_API_KEY=your_key
XAI_API_KEY=your_key
OPENAI_API_KEY=your_key
```

## Advanced Features

### Error Notifications

Get notified when jobs fail:

```yaml
jobs:
  - name: critical_job
    notify_on_error: true
    # ... rest of config
```

### Custom Models

Override the default model per job:

```yaml
agents:
  - name: my_agent
    model_override:
      provider: openai
      model: gpt-4
```

### Complex Schedules

Combine multiple time specifications:

```yaml
# Business hours only
schedule:
  hour: "9-17"
  minute: 0
  day_of_week: "mon-fri"

# Quarterly reports
schedule:
  day: 1
  month: "*/3"  # Every 3 months
  hour: 9
```

## Troubleshooting

**Jobs not running:**
- Check cron syntax with `agent-scheduler --list`
- Verify agent/team names match configuration
- Check logs for errors

**Agent errors:**
- Ensure API keys are set in `.env`
- Verify MCP servers are configured correctly
- Check agent has required plugins installed

**Output not saved:**
- Verify output directory exists and is writable
- Check output type is valid
- Review logs for save errors

## Examples

See `examples/scheduler.yaml.example` for complete examples including:
- Daily investment reports
- Weekly summaries
- Monthly deep analysis
- Hourly market monitoring

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [egile-agent-scheduler](https://github.com/yourusername/egile-agent-scheduler)
- Documentation: See QUICKSTART.md for more examples
