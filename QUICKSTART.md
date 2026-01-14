# Quick Start Guide

## 1. Installation

Run the installer:

**Windows:**
```bash
install.bat
```

**Linux/Mac:**
```bash
chmod +x install.sh
./install.sh
```

## 2. Basic Configuration

Create `scheduler.yaml`:

```yaml
jobs:
  - name: daily_investment_report
    schedule: "0 9 * * *"  # 9 AM daily
    agent: investment
    task: |
      Generate an investment report with:
      - Current portfolio analysis
      - Sell recommendations
      - Buy opportunities
    output:
      type: pdf
      path: output/investments

agents:
  - name: investment
    plugin_type: investment
    mcp_port: 8004
```

## 3. Configure Environment

Edit `.env`:

```bash
MISTRAL_API_KEY=your_key_here
```

## 4. Test Your Configuration

List jobs:
```bash
agent-scheduler --list
```

Run once:
```bash
agent-scheduler --run daily_investment_report
```

## 5. Start the Scheduler

Run as daemon:
```bash
agent-scheduler --daemon
```

## Common Schedules

```yaml
# Every day at 9 AM
schedule: "0 9 * * *"

# Every weekday at 9 AM
schedule: "0 9 * * 1-5"

# Every 6 hours
schedule: "0 */6 * * *"

# Every Monday at 10 AM
schedule: "0 10 * * 1"

# First of month at 8:30 AM
schedule: "30 8 1 * *"
```

## Example: Investment Report Job

Full example with PDF output:

```yaml
jobs:
  - name: morning_brief
    description: "Daily investment briefing"
    schedule: "0 8 * * 1-5"  # Weekdays at 8 AM
    agent: investment
    task: |
      Create a morning investment briefing:
      1. Portfolio performance overnight
      2. Key market movers
      3. Actions to consider today
    output:
      type: pdf
      path: output/daily_briefs
      title: "Morning Investment Briefing"
      filename: morning_brief
    notify_on_error: true
```

## Next Steps

- See `README.md` for complete documentation
- Check `examples/scheduler.yaml.example` for more examples
- Read about [integration with egile-agent-hub](README.md#integration-with-egile-agent-hub)
