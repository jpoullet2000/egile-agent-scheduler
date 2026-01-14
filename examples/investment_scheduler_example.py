"""
Example: Daily Investment Report Scheduler

This example demonstrates how to set up a scheduler that generates
daily PDF investment reports automatically.
"""

import asyncio
import logging
from pathlib import Path

from egile_agent_scheduler.config import SchedulerConfig
from egile_agent_scheduler.scheduler import AgentScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def create_example_config():
    """Create an example configuration for daily investment reports."""
    
    jobs = [
        {
            "name": "morning_investment_brief",
            "description": "Daily morning investment briefing",
            "schedule": "0 8 * * 1-5",  # Weekdays at 8 AM
            "agent": "investment",
            "task": """
Generate a morning investment briefing with the following sections:

1. Portfolio Overview
   - Current total value
   - Top performers
   - Biggest losers

2. Market Analysis
   - Key market movements overnight
   - Relevant news affecting my holdings
   - Economic indicators to watch

3. Action Items
   - Stocks to consider selling today with reasoning
   - Potential buy opportunities
   - Risk alerts

Keep it concise and actionable.
            """.strip(),
            "output": {
                "type": "pdf",
                "path": "output/daily_briefs",
                "title": "Morning Investment Briefing",
                "filename": "morning_brief",
            },
            "notify_on_error": True,
        },
        {
            "name": "weekly_portfolio_review",
            "description": "Weekly comprehensive portfolio review",
            "schedule": {
                "hour": 18,
                "minute": 0,
                "day_of_week": "fri",  # Friday at 6 PM
            },
            "agent": "investment",
            "task": """
Create a comprehensive weekly portfolio review:

1. Week in Review
   - Overall performance vs market
   - Best and worst performers
   - Notable trades or changes

2. Portfolio Health Check
   - Diversification analysis
   - Risk assessment
   - Sector exposure

3. Looking Ahead
   - Key events next week
   - Earnings reports to watch
   - Strategic recommendations

Provide detailed analysis with charts and data.
            """.strip(),
            "output": {
                "type": "pdf",
                "path": "output/weekly_reviews",
                "title": "Weekly Portfolio Review",
                "filename": "weekly_review",
            },
        },
    ]

    agents = [
        {
            "name": "investment",
            "description": "Investment monitoring and analysis agent",
            "plugin_type": "investment",
            "mcp_port": 8004,
            "instructions": [
                "You are a professional investment advisor and portfolio analyst.",
                "Always provide data-driven recommendations with clear reasoning.",
                "Consider risk, diversification, and long-term investment strategy.",
                "Be specific and actionable in your advice.",
                "Use precise numbers and percentages when available.",
                "Highlight both opportunities and risks clearly.",
            ],
        }
    ]

    return SchedulerConfig(jobs=jobs, agents=agents)


async def run_example():
    """Run the example scheduler."""
    
    print("=" * 70)
    print("Daily Investment Report Scheduler - Example")
    print("=" * 70)
    print()
    
    # Create configuration
    config = create_example_config()
    
    # Create scheduler
    scheduler = AgentScheduler(config)
    
    # Print schedule
    scheduler.print_schedule()
    
    # Ask user what to do
    print("Options:")
    print("  1. Run morning brief now (test)")
    print("  2. Run weekly review now (test)")
    print("  3. Start scheduler daemon")
    print("  4. Exit")
    print()
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == "1":
        print("\n🔄 Running morning brief...\n")
        await scheduler.run_once("morning_investment_brief")
        print("\n✅ Complete! Check output/daily_briefs/ for the PDF report.")
    
    elif choice == "2":
        print("\n🔄 Running weekly review...\n")
        await scheduler.run_once("weekly_portfolio_review")
        print("\n✅ Complete! Check output/weekly_reviews/ for the PDF report.")
    
    elif choice == "3":
        print("\n🚀 Starting scheduler daemon...")
        print("Press Ctrl+C to stop\n")
        await scheduler.run_forever()
    
    else:
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    asyncio.run(run_example())
