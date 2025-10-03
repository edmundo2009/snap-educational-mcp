# Manual Snap! MCP Server Setup Tutorial

This guide explains how to manually run the Snap! Educational MCP server, understand the connection process, and troubleshoot common issues.

## Quick Start

### 1. Manual Server Startup
```bash
# Navigate to your project directory
cd C:\Users\Administrator\CODE\snap-educational-mcp

# Activate virtual environment
venv\Scripts\activate

# Start the server manually
python -m mcp_server.main
```

### 2. Get Connection Token
Once the server starts, you'll see output like:
```
🚀 Snap! Educational MCP Server starting...
📡 WebSocket server listening on ws://localhost:8765
⚡ Server ready! Use start_snap_session to get connection tokens.
```

To get a connection token, you need to call the MCP tool (this is what I do when you ask me to start a session):
- **Token expires in**: 30 minutes (1800 seconds) 
- **WebSocket URL**: ws://localhost:8765
- **Display token**: 8-character code for browser extension

## Understanding the Connection Architecture

### How It Works
```
[Claude/You] ←→ [MCP Server] ←→ [Browser Extension] ←→ [Snap! IDE]
     ↑              ↑                    ↑              ↑
   MCP Tools    WebSocket Server    Content Script   JavaScript API
```

### Connection Flow
1. **You ask me** to start a Snap! session
2. **I call** `start_snap_session` MCP tool
3. **MCP Server** generates a token and starts WebSocket server
4. **You enter token** in browser extension
5. **Browser extension** connects to WebSocket server


## Server Configuration in Claude Desktop

Your current configuration is correct:

### config.yml (allowedMcpServers)
```yaml
allowedMcpServers:
  - C:\Users\Administrator\CODE\snap-educational-mcp\run_mcp.bat
```

### claude_desktop_config.json (mcpServers)
```json
{
  "mcpServers": {
    "snap-automation": {
      "command": "C:\\Users\\Administrator\\CODE\\snap-educational-mcp\\run_mcp.bat"
    }
  }
}
```

## Manual vs Automatic Server Management

### When I Start the Server (Automatic)
- ✅ I can control the server through MCP tools
- ✅ I can generate tokens on demand
- ✅ I can check connection status
- ✅ Seamless integration

### When You Start Manually
- ⚠️ I can still use MCP tools if the server is running
- ⚠️ You need to manually get tokens (see below)
- ⚠️ If you restart, I might lose connection temporarily

## Getting Tokens When Running Manually

### Option 1: Ask Me (Recommended)
Even if you started the server manually, you can still ask me:
```
"Can you start a new Snap! session and give me the connection token?"
```
I'll call the MCP tools and provide the token.

### Option 2: Direct HTTP Request
```bash
# Get a token directly
curl -X POST http://localhost:8765/api/session \
  -H "Content-Type: application/json" \
  -d '{"user_id": "manual_user"}'
```

### Option 3: Server Logs
When the server starts, it will show:
```
📡 WebSocket server listening on ws://localhost:8765
⚡ Server ready! Use start_snap_session to get connection tokens.
```

But tokens are only generated on demand, not at startup.

## Automatic Token Display Solution

Let me create an enhanced version that shows tokens automatically:

### Enhanced Startup Script
```batch
@echo off
chcp 65001 >nul
cd /d "C:\Users\Administrator\CODE\snap-educational-mcp"
call venv\Scripts\activate.bat
set PYTHONIOENCODING=utf-8
echo.
echo ================================
echo Snap! Educational MCP Server
echo ================================
echo.
echo Server starting...
python -m mcp_server.main --auto-token
echo.
echo Server stopped. Press any key to exit...
pause >nul
```

## Reconnection Behavior

### If You Restart the Server Manually:

1. **My MCP connection**: Will automatically reconnect when you ask me to use Snap! tools
2. **Browser extension**: Will show "Connection lost" and need a new token
3. **WebSocket port**: Always stays on 8765 (unless you change it)

### Reconnection Steps:
1. Restart server: `python -m mcp_server.main`
2. Ask me: "Start a new Snap! session"
3. I'll provide new token
4. Enter token in browser extension


## Troubleshooting

### Server Won't Start
```bash
# Check if port is in use
netstat -an | findstr :8765

# Kill existing process if needed
taskkill /f /im python.exe
```

### Can't Get Tokens
```bash
# Check server status
curl http://localhost:8765/health

# Expected response: {"status": "healthy", "version": "1.0.0"}
```

## Best Practices

### For Development
1. **Use manual startup** when debugging server code
2. **Use automatic startup** (through me) for normal usage
3. **Keep server running** to avoid reconnection delays

### For Production Use
1. **Always use automatic startup** through Claude Desktop
2. **Let me manage tokens** for seamless experience
3. **Ask for new sessions** if connection is lost

## Quick Reference

### Common Commands
```bash
# Start server manually
venv\Scripts\activate && python -m mcp_server.main

# Check if server is running
curl http://localhost:8765/health

# Get server status through me
"Check the Snap! MCP connection status"
```

### Connection Info
- **WebSocket URL**: ws://localhost:8765
- **Token Lifetime**: 30 minutes
- **Port**: 8765 (configurable in server code)
- **Protocol**: WebSocket with JSON messages

