"""Configuration loader for Egile Agent Scheduler.

This module loads and validates scheduler job configurations from YAML files.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Raised when configuration is invalid."""
    pass


class SchedulerConfig:
    """Container for scheduler configuration."""

    def __init__(
        self,
        jobs: list[dict[str, Any]],
        agents: list[dict[str, Any]] | None = None,
        teams: list[dict[str, Any]] | None = None,
    ):
        """
        Initialize scheduler configuration.

        Args:
            jobs: List of scheduled job configurations
            agents: Optional list of agent configurations (if not using hub)
            teams: Optional list of team configurations (if not using hub)
        """
        self.jobs = jobs
        self.agents = agents or []
        self.teams = teams or []
        self._validate()

    def _validate(self) -> None:
        """Validate the configuration."""
        if not self.jobs:
            raise ConfigError("At least one job must be defined")

        # Validate jobs
        job_names = set()
        for job in self.jobs:
            if "name" not in job:
                raise ConfigError("All jobs must have a 'name' field")
            
            name = job["name"]
            if name in job_names:
                raise ConfigError(f"Duplicate job name: {name}")
            job_names.add(name)

            # Validate schedule
            if "schedule" not in job:
                raise ConfigError(f"Job '{name}' must have a 'schedule' field")

            # Validate target (agent or team)
            if "agent" not in job and "team" not in job:
                raise ConfigError(f"Job '{name}' must specify either 'agent' or 'team'")
            
            if "agent" in job and "team" in job:
                raise ConfigError(f"Job '{name}' cannot specify both 'agent' and 'team'")

            # Validate task
            if "task" not in job:
                raise ConfigError(f"Job '{name}' must have a 'task' field describing what to do")

            # Validate output (optional but recommended)
            if "output" in job:
                output = job["output"]
                if "type" not in output:
                    raise ConfigError(f"Job '{name}' output must have a 'type' field")
                
                output_type = output["type"]
                valid_types = ["pdf", "markdown", "html", "json", "text"]
                if output_type not in valid_types:
                    raise ConfigError(
                        f"Job '{name}' output type must be one of: {', '.join(valid_types)}"
                    )

        logger.info(f"Validated {len(self.jobs)} job(s)")

    def get_job(self, name: str) -> dict[str, Any] | None:
        """Get a job configuration by name."""
        for job in self.jobs:
            if job["name"] == name:
                return job
        return None

    def list_jobs(self) -> list[str]:
        """List all job names."""
        return [job["name"] for job in self.jobs]


def load_config(config_file: str | Path = "scheduler.yaml") -> SchedulerConfig:
    """
    Load scheduler configuration from YAML file.

    Args:
        config_file: Path to YAML configuration file

    Returns:
        SchedulerConfig instance

    Raises:
        ConfigError: If configuration is invalid or file not found
    """
    config_path = Path(config_file)
    
    if not config_path.exists():
        raise ConfigError(f"Configuration file not found: {config_path}")

    logger.info(f"Loading configuration from: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {config_path}: {e}")
    except Exception as e:
        raise ConfigError(f"Failed to read {config_path}: {e}")

    if not isinstance(data, dict):
        raise ConfigError(f"Configuration file must contain a YAML dictionary")

    # Extract sections
    jobs = data.get("jobs", [])
    agents = data.get("agents", [])
    teams = data.get("teams", [])

    if not jobs:
        raise ConfigError("Configuration must contain a 'jobs' section")

    return SchedulerConfig(jobs=jobs, agents=agents, teams=teams)


def get_default_config_path() -> Path:
    """Get the default configuration file path."""
    # Check current directory first
    local_config = Path("scheduler.yaml")
    if local_config.exists():
        return local_config
    
    # Check user's home directory
    home_config = Path.home() / ".egile" / "scheduler.yaml"
    if home_config.exists():
        return home_config
    
    # Return local path as default
    return local_config
