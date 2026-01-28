# MCP (Model Context Protocol) Integration Testing Guide

This guide explains how to test the MCP server integration with ShellGPT.

## Prerequisites

1. Install ShellGPT with MCP support:
```bash
pip install shell-gpt[mcp]
```

2. Have Node.js and npm/npx installed (for most MCP servers)

## Basic Testing

### 1. Enable MCP in Configuration

Edit `~/.config/shell_gpt/.sgptrc` and add:
```
MCP_ENABLED=true
```

### 2. Configure MCP Servers

Create or edit `~/.config/shell_gpt/mcp_servers.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
      "env": {}
    }
  }
}
```

### 3. Test with sgpt

Run a query that would use the MCP tools:
```bash
sgpt "List files in /tmp directory using the available tools"
```

## Example MCP Servers

### Filesystem Server
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/directory"],
      "env": {}
    }
  }
}
```

### Memory Server
```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {}
    }
  }
}
```

### GitHub Server
```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your_github_token_here"
      }
    }
  }
}
```

## Troubleshooting

### MCP Not Working

1. **Check if MCP is enabled:**
   ```bash
   grep MCP_ENABLED ~/.config/shell_gpt/.sgptrc
   ```

2. **Verify mcp package is installed:**
   ```bash
   pip show mcp
   ```

3. **Check server configuration:**
   ```bash
   cat ~/.config/shell_gpt/mcp_servers.json
   ```

4. **Test server command manually:**
   ```bash
   npx -y @modelcontextprotocol/server-filesystem /tmp
   ```

### Debugging

Enable function output to see what tools are being called:
```
SHOW_FUNCTIONS_OUTPUT=true
```

Add this to your `.sgptrc` file.

## Notes

- MCP servers run as separate processes and communicate with ShellGPT via stdio
- Each server provides tools that become available as functions to the LLM
- Tool names are prefixed with `mcp_<server_name>_` to avoid conflicts
- MCP is disabled by default to avoid unexpected behavior
- The LLM will automatically choose when to use MCP tools vs built-in functions
