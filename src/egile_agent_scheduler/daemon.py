"""Daemon mode for running the scheduler continuously."""

from __future__ import annotations

import asyncio
import logging
import sys

from egile_agent_scheduler.config import ConfigError, get_default_config_path, load_config
from egile_agent_scheduler.scheduler import AgentScheduler

logger = logging.getLogger(__name__)


def main():
    """Main entry point for daemon mode."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Load configuration
    config_path = get_default_config_path()
    
    logger.info(f"Loading configuration from: {config_path}")
    
    try:
        config = load_config(config_path)
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Create and run scheduler
    scheduler = AgentScheduler(config)
    
    try:
        asyncio.run(scheduler.run_forever())
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
