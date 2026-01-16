# MCP Server Setup Guide

This guide covers how to integrate the `mcplay` MCP server with VS Code and GitHub Copilot.

## Prerequisites

- VS Code 1.99 or later (MCP is GA in 1.102+)
- GitHub Copilot extension installed
- Python 3.10+
- `uv` package manager

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/natekot/mcplay.git
   cd mcplay
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

## VS Code + GitHub Copilot Integration

### Step 1: Create the MCP configuration file

Create `.vscode/mcp.json` in your workspace (or add to an existing one):

```json
{
  "servers": {
    "c-tools": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcplay", "python", "server.py"]
    }
  }
}
```

Replace `/path/to/mcplay` with the actual path to this repository.

### Step 2: Start the MCP server

1. Open the Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`)
2. Run **MCP: List Servers**
3. Select `c-tools` and click **Start**
4. When prompted, confirm you trust the server

### Step 3: Verify it's working

1. Open GitHub Copilot Chat (click the Copilot icon in the sidebar)
2. Switch to **Agent Mode** using the dropdown at the top of the chat
3. Click the **Tools** icon (wrench/hammer) to see available tools
4. Confirm `check_compilation` appears in the list

You can also verify by:
- Running **MCP: List Servers** and checking the status shows "Running"
- Selecting the server and choosing **Show Output** to view logs

### Step 4: Test the tool

In Copilot Chat (Agent Mode), try:

```
Check if samples/valid.c compiles
```

Or:

```
Use the check_compilation tool on samples/invalid.c
```

You can also explicitly reference the tool by typing `#check_compilation`.

## Troubleshooting

### Server not appearing in tools list

- Ensure the server is started (green indicator in MCP: List Servers)
- Check you're in **Agent Mode**, not Ask or Edit mode
- Verify the path in `mcp.json` is correct

### Server fails to start

Check the output logs:
1. Run **MCP: List Servers**
2. Select the server
3. Click **Show Output**

Common issues:
- `uv` not in PATH: Use full path (e.g., `/Users/you/.local/bin/uv`)
- Python not found: Ensure `uv sync` was run in the mcplay directory

### "MCP servers in Copilot" policy error

If you're using Copilot Business/Enterprise, your organization admin must enable the "MCP servers in Copilot" policy.

## Available Tools

| Tool | Description |
|------|-------------|
| `check_compilation` | Verify if a C source file compiles using gcc. Returns success status, compiler output, and exit code. |

### check_compilation parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file_path` | string | Yes | - | Path to the C source file |
| `compiler_flags` | string | No | `-Wall -Wextra` | Compiler flags to pass to gcc |

## References

- [VS Code MCP Server Documentation](https://code.visualstudio.com/docs/copilot/customization/mcp-servers)
- [GitHub Copilot MCP Integration](https://docs.github.com/copilot/customizing-copilot/using-model-context-protocol/extending-copilot-chat-with-mcp)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
