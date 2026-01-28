"""
MCP (Model Context Protocol) client integration for ShellGPT.

This module provides functionality to connect to MCP servers and use their tools
as functions within ShellGPT.
"""
import asyncio
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .config import cfg


class MCPClient:
    """Wrapper for MCP client that manages connections to MCP servers."""

    def __init__(self) -> None:
        self.servers: Dict[str, Any] = {}
        self.tools: List[Dict[str, Any]] = []
        self._initialized = False

        # Check if MCP is enabled
        self.enabled = cfg.get("MCP_ENABLED") == "true"
        if not self.enabled:
            return

        # Try to import MCP libraries
        try:
            from mcp.client.session import ClientSession  # noqa: F401
            from mcp.client.stdio import (  # noqa: F401
                StdioServerParameters,
                stdio_client,
            )

            self._mcp_available = True
        except ImportError:
            self._mcp_available = False
            self.enabled = False

    def _load_servers_config(self) -> Dict[str, Any]:
        """Load MCP servers configuration from JSON file."""
        config_path = Path(cfg.get("MCP_SERVERS_CONFIG_PATH"))

        if not config_path.exists():
            # Create default config file
            config_path.parent.mkdir(parents=True, exist_ok=True)
            default_config = {
                "mcpServers": {
                    # Example server configuration (commented out)
                    # "example": {
                    #     "command": "npx",
                    #     "args": ["-y", "@modelcontextprotocol/server-example"],
                    #     "env": {}
                    # }
                }
            }
            with open(config_path, "w") as f:
                json.dump(default_config, f, indent=2)
            return default_config

        with open(config_path, "r") as f:
            return json.load(f)

    async def _initialize_server(
        self, name: str, server_config: Dict[str, Any]
    ) -> None:
        """Initialize a single MCP server connection."""
        from mcp.client.session import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        command = server_config.get("command")
        args = server_config.get("args", [])
        env = server_config.get("env", None)

        if not command:
            return

        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env,
        )

        try:
            # Create stdio client context
            read, write = await stdio_client(server_params)
            session = ClientSession(read, write)

            # Initialize the session
            await session.initialize()

            # Get available tools from this server
            tools_result = await session.list_tools()

            # Store session and tools
            self.servers[name] = {
                "session": session,
                "read": read,
                "write": write,
            }

            # Add tools to our list with server name prefix
            if hasattr(tools_result, "tools"):
                for tool in tools_result.tools:
                    self.tools.append(
                        {
                            "server_name": name,
                            "tool": tool,
                        }
                    )
        except Exception as e:
            # Silently fail for individual servers, but log the error
            # This allows other servers to still work
            pass

    async def _initialize_async(self) -> None:
        """Asynchronously initialize all MCP server connections."""
        if not self.enabled or not self._mcp_available:
            return

        config = self._load_servers_config()
        servers_config = config.get("mcpServers", {})

        # Initialize all servers concurrently
        tasks = [
            self._initialize_server(name, server_config)
            for name, server_config in servers_config.items()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        self._initialized = True

    def initialize(self) -> None:
        """Initialize MCP client and connect to all configured servers."""
        if not self.enabled or self._initialized:
            return

        loop = None
        try:
            # Run async initialization in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._initialize_async())
        except Exception:
            # If initialization fails, disable MCP
            # Silently fail to avoid breaking existing functionality
            self.enabled = False
        finally:
            if loop:
                loop.close()

    def get_tools_schemas(self) -> List[Dict[str, Any]]:
        """Get OpenAI-compatible function schemas for all MCP tools."""
        if not self.enabled or not self._initialized:
            return []

        schemas = []
        for tool_info in self.tools:
            tool = tool_info["tool"]
            server_name = tool_info["server_name"]

            # Convert MCP tool schema to OpenAI function schema
            schema = {
                "type": "function",
                "function": {
                    "name": f"mcp_{server_name}_{tool.name}",
                    "description": tool.description or "",
                    "parameters": tool.inputSchema
                    if hasattr(tool, "inputSchema")
                    else {},
                },
            }
            schemas.append(schema)

        return schemas

    async def _call_tool_async(
        self, server_name: str, tool_name: str, arguments: Dict[str, Any]
    ) -> str:
        """Asynchronously call an MCP tool."""
        if server_name not in self.servers:
            return f"Error: Server {server_name} not found"

        session = self.servers[server_name]["session"]

        try:
            result = await session.call_tool(tool_name, arguments)

            # Extract content from result
            if hasattr(result, "content") and result.content:
                content_parts = []
                for item in result.content:
                    if hasattr(item, "text"):
                        content_parts.append(item.text)
                return "\n".join(content_parts)

            return str(result)
        except Exception as e:
            return f"Error calling tool: {str(e)}"

    def call_tool(self, full_name: str, arguments: Dict[str, Any]) -> str:
        """Call an MCP tool synchronously."""
        if not self.enabled or not self._initialized:
            return "Error: MCP is not enabled or initialized"

        # Parse the full name (format: mcp_<server>_<tool>)
        if not full_name.startswith("mcp_"):
            return "Error: Invalid MCP tool name"

        parts = full_name[4:].split("_", 1)
        if len(parts) != 2:
            return "Error: Invalid MCP tool name format"

        server_name, tool_name = parts

        # Run async call in event loop
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._call_tool_async(server_name, tool_name, arguments)
            )
            return result
        except Exception as e:
            return f"Error: {str(e)}"
        finally:
            if loop:
                loop.close()

    def cleanup(self) -> None:
        """Clean up MCP client connections."""
        # Note: In a production implementation, we would properly close
        # the sessions here, but for simplicity we're letting them be
        # garbage collected
        pass


# Global MCP client instance
mcp_client = MCPClient()
