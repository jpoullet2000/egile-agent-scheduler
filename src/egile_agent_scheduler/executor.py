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

    async def _create_agent_from_config(self, agent_name: str, additional_tools: list = None) -> AgnoAgent:
        """
        Create an Agno agent from configuration.

        Args:
            agent_name: Name of the agent
            additional_tools: Optional list of additional tool functions to add

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
        
        # Add additional tools if provided (e.g., from reporter plugin)
        if additional_tools:
            tools.extend(additional_tools)
            logger.info(f"Added {len(additional_tools)} additional tools to agent '{agent_name}'")

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

    async def _get_or_create_agent(self, agent_name: str, additional_tools: list = None) -> AgnoAgent:
        """Get cached agent or create new one."""
        # Create cache key that includes additional tools
        cache_key = agent_name
        if additional_tools:
            cache_key = f"{agent_name}_with_tools"
        
        if cache_key not in self._agents_cache:
            self._agents_cache[cache_key] = await self._create_agent_from_config(
                agent_name, additional_tools=additional_tools
            )
        return self._agents_cache[cache_key]

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

    async def _load_additional_plugins(self, plugin_names: list) -> list:
        """Load additional plugins and return their tool functions.
        
        Args:
            plugin_names: List of plugin names to load (e.g., ['reporter'])
            
        Returns:
            List of tool functions from all loaded plugins
        """
        all_tools = []
        
        # Load each plugin from the hub
        try:
            from egile_agent_hub.config import load_config as load_hub_config
            from egile_agent_hub.plugin_loader import load_plugins_for_agents
            import os
            from pathlib import Path
            
            # Try to find hub config in typical locations
            hub_config = None
            config_locations = [
                os.environ.get("HUB_CONFIG_PATH"),  # Environment variable
                Path.home() / ".egile" / "agents.yaml",  # User home
                Path.cwd().parent / "egile-agent-hub" / "agents.yaml",  # Sibling directory
            ]
            
            for config_path in config_locations:
                if config_path and Path(config_path).exists():
                    hub_config = load_hub_config(config_file=str(config_path))
                    logger.info(f"Loaded hub config from: {config_path}")
                    break
            
            if not hub_config:
                # Fall back to package installation location
                hub_config = load_hub_config()
            
            # Find agent configs for the requested plugins
            agent_configs = []
            for plugin_name in plugin_names:
                for agent in hub_config.agents:
                    if agent["name"] == plugin_name:
                        agent_configs.append(agent)
                        break
            
            if agent_configs:
                plugins = load_plugins_for_agents(agent_configs)
                
                # Extract tools from each plugin
                for plugin_name, plugin in plugins.items():
                    # Initialize the plugin
                    if hasattr(plugin, 'on_agent_start'):
                        class AgentProxy:
                            def __init__(self, name):
                                self.name = name
                        await plugin.on_agent_start(AgentProxy(plugin_name))
                        logger.info(f"Initialized additional plugin: {plugin_name}")
                    
                    # Get tools
                    if hasattr(plugin, "get_tool_functions"):
                        tool_functions = plugin.get_tool_functions()
                        tools = list(tool_functions.values())
                        all_tools.extend(tools)
                        logger.info(f"Loaded {len(tools)} tools from plugin '{plugin_name}'")
                        
                        # Cache plugin for cleanup
                        self._plugins_cache[plugin_name] = plugin
        
        except Exception as e:
            logger.error(f"Failed to load additional plugins {plugin_names}: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return all_tools
    
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

    async def _run_agent_streaming(self, agent, task: str) -> str:
        """
        Run agent in streaming mode to avoid Agno bug.
        
        In streaming mode, our AgnoModelAdapter.ainvoke_stream() handles tool execution
        and properly wraps results, avoiding the "'str' has no attribute 'role'" bug.
        
        Args:
            agent: Agno Agent instance
            task: Task to execute
            
        Returns:
            Complete response content
        """
        from agno.models.base import Message
        
        # Create message for the task
        message = Message(role="user", content=task)
        
        # Get tools from agent
        tools = agent.tools if hasattr(agent, 'tools') else None
        
        # Run agent's model in streaming mode with tools
        # This will call our AgnoModelAdapter.ainvoke_stream()
        # which executes tools properly and wraps results
        accumulated_content = []
        
        # Pass tools to the model so it knows they're available
        async for chunk in agent.model.ainvoke_stream([message], tools=tools):
            if hasattr(chunk, 'content'):
                accumulated_content.append(chunk.content)
            elif isinstance(chunk, str):
                accumulated_content.append(chunk)
        
        result = "".join(accumulated_content)
        logger.info(f"Streaming execution completed, result length: {len(result)} characters")
        return result

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
            
            # Load additional plugins if specified (e.g., reporter for formatting)
            additional_tools = []
            if "additional_plugins" in job_config:
                additional_plugins = job_config["additional_plugins"]
                if isinstance(additional_plugins, str):
                    additional_plugins = [additional_plugins]
                
                logger.info(f"Loading additional plugins: {additional_plugins}")
                additional_tools = await self._load_additional_plugins(additional_plugins)
                logger.info(f"Loaded {len(additional_tools)} tools from additional plugins")
            
            agent = await self._get_or_create_agent(agent_name, additional_tools=additional_tools)
            
            # Use streaming mode to avoid Agno bug with tool results
            # In streaming mode, our AgnoModelAdapter.ainvoke_stream() executes tools
            # and wraps results properly, avoiding the "'str' has no attribute 'role'" bug
            try:
                logger.info(f"Executing agent in streaming mode to properly handle tool results")
                response_content = await self._run_agent_streaming(agent, task)
                return response_content
            except Exception as e:
                # Capture full traceback for debugging
                import traceback
                logger.error(f"Exception during streaming agent execution: {e}")
                logger.error(f"Full traceback:\n{traceback.format_exc()}")
                
                # Fall back to direct execution if available
                logger.warning("Streaming execution failed, attempting direct execution workaround...")
                plugin = self._plugins_cache.get(agent_name)
                if plugin and hasattr(plugin, 'execute_task_direct'):
                    try:
                        result = await plugin.execute_task_direct(task)
                        logger.info(f"Direct execution successful for {agent_name}, result length: {len(result)} characters")
                        return result
                    except Exception as direct_error:
                        logger.error(f"Direct execution also failed: {direct_error}")
                        raise RuntimeError(f"Both streaming and direct execution failed: {direct_error}")
                else:
                    raise
        
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
