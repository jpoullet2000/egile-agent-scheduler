# Integration with Egile Investment Agent

This guide shows how to use the scheduler with the Egile Investment Agent to automate portfolio reports.

## Prerequisites

1. **Install Investment Agent**:
   ```bash
   cd egile-agent-investment
   ./install.sh
   ```

2. **Install Scheduler**:
   ```bash
   cd egile-agent-scheduler
   ./install.sh
   ```

3. **Configure API Keys** in `.env`:
   ```bash
   # AI Model
   MISTRAL_API_KEY=your_key_here
   
   # Investment data (if using external APIs)
   # Add any investment-specific API keys
   ```

## Quick Setup for Daily Investment Reports

### 1. Create Portfolio File

Create `portfolio.csv` in your home directory or project root:

```csv
symbol,shares,purchase_price
AAPL,50,150.00
MSFT,30,300.00
GOOGL,20,2500.00
TSLA,10,200.00
```

### 2. Configure Scheduler

Create or edit `scheduler.yaml`:

```yaml
jobs:
  # Daily morning briefing
  - name: morning_investment_brief
    description: "Daily investment briefing with actionable insights"
    schedule: "0 8 * * 1-5"  # Weekdays at 8 AM
    agent: investment
    task: |
      Generate my daily investment briefing:
      
      1. Portfolio Summary
         - Current total value
         - Top 3 performers
         - Top 3 underperformers
      
      2. Market Context
         - Key overnight market movements
         - Relevant news for my holdings
         - Economic data to watch today
      
      3. Action Items
         - Any stocks I should consider selling today (with clear reasoning)
         - Potential buying opportunities (based on valuation and technicals)
         - Risk alerts or concerns
      
      Keep it concise but informative. Focus on actionable insights.
    output:
      type: pdf
      path: output/investments
      title: "Morning Investment Briefing"
      filename: morning_brief
    notify_on_error: true

  # Weekly comprehensive review
  - name: weekly_portfolio_review
    description: "Deep weekly portfolio analysis"
    schedule: "0 18 * * 5"  # Friday at 6 PM
    agent: investment
    task: |
      Create a comprehensive weekly portfolio review:
      
      1. Week in Review
         - Overall performance vs S&P 500
         - Best and worst performers with analysis
         - Significant news or events
      
      2. Portfolio Health
         - Sector diversification analysis
         - Risk assessment (concentration, volatility)
         - Correlation with market indices
      
      3. Looking Ahead
         - Upcoming earnings reports for my holdings
         - Key economic events next week
         - Strategic adjustments to consider
      
      4. Buy/Sell Recommendations
         - Detailed analysis of potential sells
         - New opportunities across different sectors
         - Position sizing suggestions
      
      Provide in-depth analysis with supporting data.
    output:
      type: pdf
      path: output/investments/weekly
      title: "Weekly Portfolio Review"
      filename: weekly_review

  # Monthly deep dive
  - name: monthly_investment_analysis
    description: "Monthly strategic investment analysis"
    schedule: "0 9 1 * *"  # First day of month at 9 AM
    agent: investment
    task: |
      Conduct a comprehensive monthly investment analysis:
      
      1. Monthly Performance
         - Month-over-month returns by holding
         - Year-to-date performance
         - Benchmark comparisons
      
      2. Strategic Review
         - Portfolio allocation vs targets
         - Rebalancing recommendations
         - Tax-loss harvesting opportunities
      
      3. Market Outlook
         - Sector trends and opportunities
         - Economic indicators and forecast
         - Risk factors on the horizon
      
      4. Investment Opportunities
         - Detailed analysis of 5-10 potential new investments
         - Include valuation metrics, growth prospects, risks
         - Diversification benefits
      
      5. Action Plan
         - Specific trades to consider this month
         - Timeline and entry/exit strategies
      
      This should be a strategic document for longer-term planning.
    output:
      type: pdf
      path: output/investments/monthly
      title: "Monthly Investment Analysis"
      filename: monthly_analysis

agents:
  - name: investment
    description: "Investment monitoring and analysis agent"
    plugin_type: investment
    mcp_port: 8004
    instructions:
      - "You are a professional investment advisor and portfolio analyst."
      - "Always provide data-driven recommendations backed by analysis."
      - "Consider multiple factors: fundamentals, technicals, market sentiment, macroeconomics."
      - "Assess risk carefully and highlight potential downsides."
      - "Think long-term but identify tactical opportunities."
      - "Be specific with numbers, percentages, and price targets."
      - "Explain your reasoning clearly so I can make informed decisions."
      - "Consider tax implications when relevant."
      - "Focus on portfolio diversification and risk management."
```

### 3. Test Your Setup

Run a job once to test:

```bash
agent-scheduler --run morning_investment_brief
```

Check the output:
```bash
ls output/investments/
```

### 4. Start the Scheduler

Run as daemon:

```bash
./start.sh  # or start.bat on Windows
```

Or manually:

```bash
agent-scheduler --daemon
```

## Output Examples

### Morning Brief (PDF)
Generated at 8 AM on weekdays:
- **Location**: `output/investments/morning_brief_20260114_080000.pdf`
- **Content**: Quick actionable insights for the day
- **Size**: 2-3 pages
- **Time to generate**: 30-60 seconds

### Weekly Review (PDF)
Generated Friday at 6 PM:
- **Location**: `output/investments/weekly/weekly_review_20260117_180000.pdf`
- **Content**: Comprehensive weekly analysis
- **Size**: 5-8 pages
- **Time to generate**: 2-3 minutes

### Monthly Analysis (PDF)
Generated on 1st of month:
- **Location**: `output/investments/monthly/monthly_analysis_20260201_090000.pdf`
- **Content**: Strategic deep-dive
- **Size**: 10-15 pages
- **Time to generate**: 5-10 minutes

## Customization Tips

### Change Schedule Times

```yaml
# Before market opens
schedule: "0 8 * * 1-5"

# After market close
schedule: "0 17 * * 1-5"

# Weekend review
schedule: "0 10 * * 6"  # Saturday at 10 AM
```

### Adjust Detail Level

For shorter reports:
```yaml
task: "Give me a brief 1-page summary of..."
```

For more depth:
```yaml
task: "Provide a comprehensive analysis with detailed charts and data covering..."
```

### Focus on Specific Aspects

```yaml
# Focus on tech stocks
task: "Analyze only my technology holdings and suggest tech sector opportunities..."

# Focus on dividend income
task: "Review dividend-paying stocks in my portfolio and suggest high-yield opportunities..."

# Focus on growth
task: "Identify high-growth opportunities in emerging sectors..."
```

### Multiple Portfolios

```yaml
jobs:
  - name: growth_portfolio_report
    agent: investment
    task: "Analyze my growth portfolio (AAPL, MSFT, GOOGL, TSLA)..."
    
  - name: income_portfolio_report
    agent: investment
    task: "Analyze my dividend income portfolio (JNJ, PG, KO)..."
```

## Advanced: Using Teams

If you have multiple agents in the hub:

```yaml
teams:
  - name: investment_research_team
    description: "Comprehensive investment research team"
    members:
      - investment
      - market_research
      - risk_analyst
    instructions:
      - "Coordinate comprehensive investment analysis."
      - "Cross-validate recommendations across team members."
      - "Provide diverse perspectives on opportunities and risks."

jobs:
  - name: deep_dive_analysis
    schedule: "0 10 1 * *"  # Monthly
    team: investment_research_team  # Use team instead of agent
    task: "Conduct deep research on 5 potential investments..."
```

## Monitoring and Logs

Check scheduler logs:
```bash
# If running in daemon mode
tail -f scheduler.log

# Or check terminal output if running interactively
agent-scheduler --daemon --verbose
```

Review generated reports:
```bash
ls -la output/investments/
```

## Troubleshooting

**No output generated:**
- Check that MCP server is running (port 8004)
- Verify portfolio.csv exists
- Check logs for errors

**Agent errors:**
- Ensure API keys are set in `.env`
- Check investment agent is installed
- Verify MCP server configuration

**Schedule not running:**
- Verify cron expression is valid
- Check scheduler is running (`ps aux | grep agent-scheduler`)
- Review scheduler logs

## Next Steps

1. Review your first few reports and adjust the prompts
2. Fine-tune the schedule times for your timezone
3. Add more specialized jobs for specific needs
4. Set up email forwarding of reports (future feature)
5. Create custom analysis templates

## Support

For issues specific to:
- **Scheduler**: Check [egile-agent-scheduler](README.md)
- **Investment Agent**: Check [egile-agent-investment](../egile-agent-investment/README.md)
- **General**: Review [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
