"""Tests for MCP (Model Context Protocol) integration."""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def test_mcp_client_disabled_by_default():
    """Test that MCP client is disabled by default."""
    from sgpt.mcp_client import MCPClient
    
    with patch("sgpt.mcp_client.cfg.get") as mock_cfg_get:
        mock_cfg_get.return_value = "false"
        client = MCPClient()
        assert not client.enabled


def test_mcp_client_disabled_when_not_installed():
    """Test that MCP client is disabled when mcp package is not installed."""
    from sgpt.mcp_client import MCPClient
    
    with patch("sgpt.mcp_client.cfg.get") as mock_cfg_get:
        mock_cfg_get.return_value = "true"
        # Mock the import to fail
        with patch("builtins.__import__", side_effect=ImportError("No module named 'mcp'")):
            client = MCPClient()
            # The client should be disabled if MCP isn't available
            assert not client.enabled or not client._mcp_available


def test_mcp_config_file_creation(tmp_path):
    """Test that MCP config file is created with default content."""
    from sgpt.mcp_client import MCPClient
    
    config_path = tmp_path / "mcp_servers.json"
    
    with patch("sgpt.mcp_client.cfg.get") as mock_cfg_get:
        mock_cfg_get.side_effect = lambda key: {
            "MCP_ENABLED": "false",
            "MCP_SERVERS_CONFIG_PATH": str(config_path)
        }.get(key, "false")
        
        client = MCPClient()
        config = client._load_servers_config()
        
        # Check that config file was created
        assert config_path.exists()
        
        # Check default config structure
        assert "mcpServers" in config
        assert isinstance(config["mcpServers"], dict)


def test_get_function_with_mcp_disabled():
    """Test that get_function works when MCP is disabled."""
    from sgpt.function import get_function
    
    # Should raise ValueError when function not found and MCP is disabled
    with pytest.raises(ValueError, match="Function nonexistent not found"):
        get_function("nonexistent")


def test_get_openai_schemas_without_mcp():
    """Test that get_openai_schemas works without MCP."""
    from sgpt.function import get_openai_schemas
    
    # Should return empty list when no functions and MCP is disabled
    schemas = get_openai_schemas()
    assert isinstance(schemas, list)


def test_mcp_tool_name_parsing():
    """Test that MCP tool names are parsed correctly."""
    from sgpt.mcp_client import MCPClient
    
    with patch("sgpt.mcp_client.cfg.get") as mock_cfg_get:
        mock_cfg_get.return_value = "false"
        client = MCPClient()
        client.enabled = True
        client._initialized = True
        
        # Test invalid names
        result = client.call_tool("invalid_name", {})
        assert "Error" in result
        
        result = client.call_tool("mcp_only_one_part", {})
        assert "Error" in result


def test_mcp_integration_with_functions():
    """Test that MCP integrates with existing function system."""
    from sgpt.function import get_openai_schemas
    from sgpt.mcp_client import mcp_client
    
    # MCP should be disabled by default, so schemas should only include regular functions
    schemas = get_openai_schemas()
    
    # Verify no MCP tools are included when disabled
    mcp_tools = [s for s in schemas if s.get("function", {}).get("name", "").startswith("mcp_")]
    assert len(mcp_tools) == 0
