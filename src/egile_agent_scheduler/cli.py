"""Command-line interface for Egile Agent Scheduler."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from egile_agent_scheduler.config import ConfigError, get_default_config_path, load_config
from egile_agent_scheduler.scheduler import AgentScheduler

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Egile Agent Scheduler - Automate agent and team workflows"
    )
    
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default=None,
        help="Path to scheduler configuration file (default: scheduler.yaml)",
    )
    
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List all scheduled jobs",
    )
    
    parser.add_argument(
        "--run",
        "-r",
        type=str,
        metavar="JOB_NAME",
        help="Run a specific job once, immediately",
    )
    
    parser.add_argument(
        "--daemon",
        "-d",
        action="store_true",
        help="Run as daemon (continuously)",
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

    # Load configuration
    config_path = args.config or get_default_config_path()
    
    try:
        config = load_config(config_path)
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Create scheduler
    scheduler = AgentScheduler(config)

    # Handle commands
    try:
        if args.list:
            # List jobs
            scheduler.print_schedule()
        
        elif args.run:
            # Run specific job once
            try:
                asyncio.run(run_job_once(scheduler, args.run))
            finally:
                # Force exit after cleanup - use os._exit for immediate termination
                import os
                logger.info("Forcing exit...")
                os._exit(0)
        
        elif args.daemon:
            # Run as daemon
            asyncio.run(scheduler.run_forever())
        
        else:
            # Default: show help
            parser.print_help()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


async def run_job_once(scheduler: AgentScheduler, job_name: str):
    """Run a specific job once."""
    try:
        await scheduler.run_once(job_name)
        logger.info(f"Job '{job_name}' completed")
    except ValueError as e:
        logger.error(f"Error: {e}")
        raise
    except Exception as e:
        logger.error(f"Job failed: {e}", exc_info=True)
        raise
    finally:
        # Always cleanup resources
        if hasattr(scheduler, 'executor') and hasattr(scheduler.executor, 'cleanup'):
            try:
                await scheduler.executor.cleanup()
            except Exception as e:
                logger.warning(f"Cleanup warning: {e}")