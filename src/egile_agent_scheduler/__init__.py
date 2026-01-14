"""Egile Agent Scheduler - Automate agent and team workflows."""

__version__ = "0.1.0"

from egile_agent_scheduler.config import SchedulerConfig, load_config
from egile_agent_scheduler.scheduler import AgentScheduler

__all__ = ["SchedulerConfig", "load_config", "AgentScheduler"]
