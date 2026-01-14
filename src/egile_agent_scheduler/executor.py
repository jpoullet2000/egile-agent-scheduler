"""Agent and team executor for scheduled jobs.

This module handles the execution of agent and team tasks,
integrating with the Egile Agent Hub when needed.
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

from agno.agent import Agent as AgnoAgent
from agno.db.sqlite import AsyncSqliteDb
from agno.team import Team as AgnoTeam
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class AgentExecutor:
    """Executes agent and team tasks."""

    def __init__(self, config):
        """
        Initialize the executor.

        Args:
            config: SchedulerConfig instance
        """
        self.config = config
        self._agents_cache = {}
        self._teams_cache = {}
        self._plugins_cache = {}  # Cache plugins for direct execution workaround
        self._db = None

    async def _get_database(self) -> AsyncSqliteDb:
        """Get or create the shared database."""
        if self._db is None:
            db_file = os.getenv("SCHEDULER_DB_FILE", "scheduler.db")
            self._db = AsyncSqliteDb(db_file=db_file)
            logger.info(f"Using database: {db_file}")
        return self._db

    async def _create_agent_from_config(self, agent_name: str) -> AgnoAgent:
        """
        Create an Agno agent from configuration.

        Args:
            agent_name: Name of the agent

        Returns:
            AgnoAgent instance
        """
        # Check if agent is in local config
        agent_config = None
        for agent in self.config.agents:
            if agent["name"] == agent_name:
                agent_config = agent
                break
        
        if not agent_config:
            # Try to load from hub config if available
            try:
                from egile_agent_hub.config import load_config as load_hub_config
                hub_config = load_hub_config()
                
                for agent in hub_config.agents:
                    if agent["name"] == agent_name:
                        agent_config = agent
                        break
            except Exception as e:
                logger.warning(f"Could not load agent from hub: {e}")
        
        if not agent_config:
            raise ValueError(f"Agent '{agent_name}' not found in configuration")

        # Import model components
        from egile_agent_core.models import Mistral, OpenAI, XAI
        from egile_agent_core.models.agno_adapter import AgnoModelAdapter

        # Get model configuration
        model_config = self._get_model_config(agent_config)
        model = self._create_model_instance(model_config)
        
        # Load plugin if configured
        tools = []
        plugin = None
        if "plugin_type" in agent_config:
            from egile_agent_hub.plugin_loader import load_plugins_for_agents
            plugins = load_plugins_for_agents([agent_config])
            
            if agent_name in plugins:
                plugin = plugins[agent_name]
                self._plugins_cache[agent_name] = plugin  # Cache for later use
                if hasattr(plugin, "get_tool_functions"):
                    tool_functions = plugin.get_tool_functions()
                    tools = list(tool_functions.values())
                    logger.info(f"Loaded {len(tools)} tools for agent '{agent_name}'")

        # Create Agno adapter
        agno_model = AgnoModelAdapter(model, tools=tools if tools else None)

        # Get shared database
        db = await self._get_database()

        # Create agent
        agent = AgnoAgent(
            name=agent_name,
            model=agno_model,
            db=db,
            instructions=agent_config.get("instructions", []),
            description=agent_config.get("description", ""),
            tools=tools if tools else None,
            markdown=agent_config.get("markdown", True),
        )
        
        # Initialize plugin by calling on_agent_start
        # This is critical for plugins that need to connect to MCP servers
        if plugin and hasattr(plugin, 'on_agent_start'):
            try:
                # Create a dummy Agent-like object with the name for the plugin
                class AgentProxy:
                    def __init__(self, name):
                        self.name = name
                
                await plugin.on_agent_start(AgentProxy(agent_name))
                logger.info(f"Initialized plugin for agent '{agent_name}'")
            except Exception as e:
                logger.error(f"Failed to initialize plugin for '{agent_name}': {e}")
                raise
        
        logger.info(f"Created agent: {agent_name}")
        return agent

    async def _create_team_from_config(self, team_name: str) -> AgnoTeam:
        """
        Create an Agno team from configuration.

        Args:
            team_name: Name of the team

        Returns:
            AgnoTeam instance
        """
        # Check if team is in local config
        team_config = None
        for team in self.config.teams:
            if team["name"] == team_name:
                team_config = team
                break
        
        if not team_config:
            # Try to load from hub config if available
            try:
                from egile_agent_hub.config import load_config as load_hub_config
                hub_config = load_hub_config()
                
                for team in hub_config.teams:
                    if team["name"] == team_name:
                        team_config = team
                        break
            except Exception as e:
                logger.warning(f"Could not load team from hub: {e}")
        
        if not team_config:
            raise ValueError(f"Team '{team_name}' not found in configuration")

        # Create team members
        member_names = team_config["members"]
        members = []
        for member_name in member_names:
            agent = await self._get_or_create_agent(member_name)
            members.append(agent)
        
        # Import model components
        from egile_agent_core.models import Mistral, OpenAI, XAI
        from egile_agent_core.models.agno_adapter import AgnoModelAdapter

        # Get model configuration for team leader
        model_config = self._get_model_config(team_config)
        model = self._create_model_instance(model_config)
        agno_model = AgnoModelAdapter(model)

        # Get shared database
        db = await self._get_database()

        # Create team
        team = AgnoTeam(
            name=team_name,
            model=agno_model,
            db=db,
            members=members,
            instructions=team_config.get("instructions", []),
            description=team_config.get("description", ""),
            markdown=team_config.get("markdown", True),
        )
        
        logger.info(f"Created team: {team_name} with {len(members)} members")
        return team

    async def _get_or_create_agent(self, agent_name: str) -> AgnoAgent:
        """Get cached agent or create new one."""
        if agent_name not in self._agents_cache:
            self._agents_cache[agent_name] = await self._create_agent_from_config(agent_name)
        return self._agents_cache[agent_name]

    async def _get_or_create_team(self, team_name: str) -> AgnoTeam:
        """Get cached team or create new one."""
        if team_name not in self._teams_cache:
            self._teams_cache[team_name] = await self._create_team_from_config(team_name)
        return self._teams_cache[team_name]

    def _get_model_config(self, config: dict) -> dict:
        """Get model configuration from config or environment."""
        if "model_override" in config:
            model_override = config["model_override"]
            if isinstance(model_override, dict):
                return model_override
            else:
                # Just model name, use default provider
                from egile_agent_hub.config import get_default_model_config
                default = get_default_model_config()
                return {"provider": default["provider"], "model": model_override}
        
        # Use default from hub
        from egile_agent_hub.config import get_default_model_config
        return get_default_model_config()

    def _create_model_instance(self, model_config: dict):
        """Create model instance from configuration."""
        from egile_agent_core.models import Mistral, OpenAI, XAI
        
        provider = model_config["provider"]
        model_name = model_config["model"]

        if provider == "mistral":
            return Mistral(model=model_name)
        elif provider == "xai":
            return XAI(model=model_name)
        elif provider == "openai":
            return OpenAI(model=model_name)
        else:
            raise ValueError(f"Unknown model provider: {provider}")

    async def execute_job(self, job_config: dict[str, Any]) -> str:
        """
        Execute a scheduled job.

        Args:
            job_config: Job configuration dictionary

        Returns:
            Result from the agent/team execution
        """
        task = job_config["task"]
        
        # Determine if we're running an agent or team
        if "agent" in job_config:
            agent_name = job_config["agent"]
            logger.info(f"Executing agent '{agent_name}' with task: {task}")
            agent = await self._get_or_create_agent(agent_name)
            
            # Execute the task
            try:
                response = await agent.arun(task)
            except AttributeError as e:
                # Workaround for Agno bug: "'str' object has no attribute 'role'"
                # This occurs when tool results are processed incorrectly
                if "'str' object has no attribute 'role'" in str(e) or "role" in str(e):
                    logger.warning(f"Encountered known Agno bug with tool results, attempting direct execution workaround...")
                    
                    # If this is the investment agent, use direct tool calling
                    if agent_name == "investment" and plugin:
                        try:
                            result = await self._execute_investment_direct(plugin, task)
                            logger.info(f"Direct execution successful, result length: {len(result)} characters")
                            return result
                        except Exception as direct_error:
                            logger.error(f"Direct execution also failed: {direct_error}")
                            raise
                    else:
                        raise
                else:
                    raise
            except Exception as e:
                # Capture full traceback for debugging
                import traceback
                logger.error(f"Exception during agent.arun(): {e}")
                logger.error(f"Full traceback:\n{traceback.format_exc()}")
                raise
                
            # Check if execution had an error status
            if hasattr(response, 'status'):
                from agno.run.agent import RunStatus
                if response.status == RunStatus.error:
                    error_msg = str(response.content) if hasattr(response, 'content') else str(response)
                    
                    # Check for the known Agno bug
                    if "'str' object has no attribute 'role'" in error_msg:
                        logger.warning(f"Encountered known Agno bug: {error_msg}")
                        logger.warning("Attempting direct execution workaround...")
                        
                        # Check if plugin implements execute_task_direct method
                        plugin = self._plugins_cache.get(agent_name)
                        if plugin and hasattr(plugin, 'execute_task_direct'):
                            try:
                                result = await plugin.execute_task_direct(task)
                                logger.info(f"Direct execution successful for {agent_name}, result length: {len(result)} characters")
                                return result
                            except Exception as direct_error:
                                logger.error(f"Direct execution also failed: {direct_error}")
                                raise RuntimeError(f"Both Agno and direct execution failed: {direct_error}")
                        else:
                            logger.warning(f"Plugin for '{agent_name}' does not implement execute_task_direct() method")
                            logger.warning(f"To add Agno bug workaround, implement execute_task_direct(task: str) -> str in the plugin class")
                            raise RuntimeError(f"Agent execution error: {error_msg}")
                    else:
                        logger.error(f"Agent execution failed with error status: {error_msg}")
                        raise RuntimeError(f"Agent execution error: {error_msg}")
            
            
            # Extract content from various response types
            if hasattr(response, 'content'):
                result = response.content
            elif hasattr(response, 'messages') and response.messages:
                # Get the last assistant message
                last_msg = response.messages[-1]
                result = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
            elif isinstance(response, str):
                result = response
            else:
                result = str(response)
            
            logger.info(f"Agent execution completed successfully, result length: {len(result)} characters")
            
            return result
        
        elif "team" in job_config:
            team_name = job_config["team"]
            logger.info(f"Executing team '{team_name}' with task: {task}")
            team = await self._get_or_create_team(team_name)
            
            # Execute the task
            try:
                response = await team.arun(task)
                
                # Extract content from various response types
                if hasattr(response, 'content'):
                    result = response.content
                elif hasattr(response, 'messages') and response.messages:
                    # Get the last assistant message
                    last_msg = response.messages[-1]
                    result = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
                elif isinstance(response, str):
                    result = response
                else:
                    result = str(response)
                
                logger.info(f"Team execution completed, result length: {len(result)} characters")
                return result
                
            except Exception as e:
                logger.error(f"Team execution failed: {e}", exc_info=True)
                raise
        
        else:
            raise ValueError("Job must specify either 'agent' or 'team'")
    
    async def cleanup(self):
        """Clean up resources (database connections, caches, etc.)."""
        logger.info("Cleaning up executor resources...")
        
        # Stop plugins first
        for plugin_name, plugin in self._plugins_cache.items():
            if plugin and hasattr(plugin, 'on_agent_stop'):
                try:
                    # Create dummy agent for plugin cleanup
                    class AgentProxy:
                        def __init__(self, name):
                            self.name = name
                    
                    await plugin.on_agent_stop(AgentProxy(plugin_name))
                    logger.info(f"Stopped plugin: {plugin_name}")
                except Exception as e:
                    logger.warning(f"Error stopping plugin {plugin_name}: {e}")
        
        # Clear caches
        self._agents_cache.clear()
        self._teams_cache.clear()
        self._plugins_cache.clear()
        
        # Close database if it was created
        if self._db is not None:
            # AsyncSqliteDb doesn't have an explicit close method in some versions
            # but we can set it to None to allow garbage collection
            self._db = None
            logger.info("Database connection released")
