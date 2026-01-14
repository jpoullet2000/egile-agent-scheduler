"""Core scheduler for running agent jobs on a schedule.

This module provides the main scheduler that executes agent and team tasks
based on cron-like schedules.
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from croniter import croniter
from dotenv import load_dotenv

from egile_agent_scheduler.config import ConfigError, SchedulerConfig
from egile_agent_scheduler.executor import AgentExecutor
from egile_agent_scheduler.output_handler import OutputHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class AgentScheduler:
    """Main scheduler for agent and team jobs."""

    def __init__(self, config: SchedulerConfig):
        """
        Initialize the scheduler.

        Args:
            config: SchedulerConfig instance
        """
        self.config = config
        self.scheduler = AsyncIOScheduler()
        self.executor = AgentExecutor(config)
        self.output_handler = OutputHandler()
        self._shutdown = False

    def _parse_schedule(self, schedule: str | dict) -> dict:
        """
        Parse schedule configuration into cron parameters.

        Args:
            schedule: Either a cron string or a dict with schedule parameters

        Returns:
            Dictionary with cron trigger parameters
        """
        if isinstance(schedule, str):
            # Validate cron expression
            if not croniter.is_valid(schedule):
                raise ConfigError(f"Invalid cron expression: {schedule}")
            
            # Parse cron string into components
            parts = schedule.split()
            if len(parts) == 5:
                return {
                    "minute": parts[0],
                    "hour": parts[1],
                    "day": parts[2],
                    "month": parts[3],
                    "day_of_week": parts[4],
                }
            else:
                raise ConfigError(f"Cron expression must have 5 parts: {schedule}")
        
        elif isinstance(schedule, dict):
            # Direct cron parameters
            valid_keys = {"minute", "hour", "day", "month", "day_of_week", "week", "second"}
            if not any(key in schedule for key in valid_keys):
                raise ConfigError(f"Schedule dict must contain at least one time field")
            return schedule
        
        else:
            raise ConfigError(f"Schedule must be a cron string or dict, got {type(schedule)}")

    async def _run_job(self, job_config: dict[str, Any]) -> None:
        """
        Execute a scheduled job.

        Args:
            job_config: Job configuration dictionary
        """
        job_name = job_config["name"]
        logger.info(f"Starting job: {job_name}")

        try:
            # Execute the agent/team task
            result = await self.executor.execute_job(job_config)
            
            # Handle output if configured
            if "output" in job_config:
                output_config = job_config["output"]
                await self.output_handler.save_output(
                    job_name=job_name,
                    result=result,
                    output_config=output_config,
                )
            
            logger.info(f"Job '{job_name}' completed successfully")

        except Exception as e:
            logger.error(f"Job '{job_name}' failed: {e}", exc_info=True)
            
            # Optionally send notification on failure
            if job_config.get("notify_on_error"):
                await self._notify_error(job_name, str(e))

    async def _notify_error(self, job_name: str, error: str) -> None:
        """
        Send notification about job failure.

        Args:
            job_name: Name of the failed job
            error: Error message
        """
        # TODO: Implement notification (email, webhook, etc.)
        logger.warning(f"Notification for job '{job_name}' error: {error}")

    def add_jobs(self) -> None:
        """Add all configured jobs to the scheduler."""
        for job_config in self.config.jobs:
            job_name = job_config["name"]
            schedule = job_config["schedule"]
            
            logger.info(f"Adding job: {job_name}")
            
            try:
                # Parse schedule
                cron_params = self._parse_schedule(schedule)
                trigger = CronTrigger(**cron_params)
                
                # Add job to scheduler
                self.scheduler.add_job(
                    self._run_job,
                    trigger=trigger,
                    args=[job_config],
                    id=job_name,
                    name=job_name,
                    replace_existing=True,
                )
                
                logger.info(f"  Schedule: {schedule}")
                
            except Exception as e:
                logger.error(f"Failed to add job '{job_name}': {e}")
                raise

    async def run_once(self, job_name: str) -> None:
        """
        Run a specific job once, immediately.

        Args:
            job_name: Name of the job to run
        """
        job_config = self.config.get_job(job_name)
        if not job_config:
            raise ValueError(f"Job not found: {job_name}")
        
        await self._run_job(job_config)

    def start(self) -> None:
        """Start the scheduler."""
        logger.info("Starting Egile Agent Scheduler...")
        
        # Add all jobs
        self.add_jobs()
        
        # List scheduled jobs
        jobs = self.scheduler.get_jobs()
        logger.info(f"Scheduled {len(jobs)} job(s):")
        for job in jobs:
            logger.info(f"  - {job.name}: {job.next_run_time}")
        
        # Start scheduler
        self.scheduler.start()
        logger.info("Scheduler started")

    def stop(self) -> None:
        """Stop the scheduler gracefully."""
        logger.info("Stopping scheduler...")
        self._shutdown = True
        self.scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped")

    async def run_forever(self) -> None:
        """
        Run the scheduler until interrupted.
        
        This is the main entry point for the daemon.
        """
        # Setup signal handlers
        loop = asyncio.get_event_loop()
        
        def signal_handler(sig):
            logger.info(f"Received signal {sig}, shutting down...")
            self.stop()
        
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))
        
        # Start scheduler
        self.start()
        
        # Keep running until shutdown
        try:
            while not self._shutdown:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.stop()

    def print_schedule(self) -> None:
        """Print the current schedule in a human-readable format."""
        print("\n📅 Scheduled Jobs\n" + "=" * 60)
        
        for job_config in self.config.jobs:
            job_name = job_config["name"]
            schedule = job_config["schedule"]
            target = job_config.get("agent") or job_config.get("team")
            target_type = "Agent" if "agent" in job_config else "Team"
            
            print(f"\nJob: {job_name}")
            print(f"  {target_type}: {target}")
            print(f"  Schedule: {schedule}")
            print(f"  Task: {job_config['task']}")
            
            if "output" in job_config:
                output = job_config["output"]
                print(f"  Output: {output.get('type', 'none')} -> {output.get('path', 'N/A')}")
        
        print("\n" + "=" * 60 + "\n")
