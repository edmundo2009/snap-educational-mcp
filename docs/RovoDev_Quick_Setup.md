# RovoDev CLI Quick Setup - Snap! MCP Integration

## 🚀 Quick Start (5 Minutes)

### 1. Create Startup Script

**Windows (`run_mcp.bat`):**
```batch
@echo off
cd /d "C:\Users\Administrator\CODE\snap-educational-mcp"
call venv\Scripts\activate
python -m mcp_server.main
pause
```

**Linux/Mac (`run_mcp.sh`):**
```bash
#!/bin/bash
cd "/path/to/snap-educational-mcp"
source venv/bin/activate
python -m mcp_server.main
```

### 2. Configure RovoDev

**config.yml:**
```yaml
allowedMcpServers: 
  - C:\Users\Administrator\CODE\snap-educational-mcp\run_mcp.bat
```

**mcp.json:**
```json
{
  "mcpServers": {
    "snap-automation": {
      "command": "C:\\Users\\Administrator\\CODE\\snap-educational-mcp\\run_mcp.bat"
    }
  }
}
```

### 3. Test Connection

```bash
# Start MCP server
./run_mcp.bat

# In another terminal, start RovoDev
rovodev chat

# Test with Claude
You: Can you help me create a Snap! program where the sprite moves when I press arrow keys?
```

---

## 📁 File Locations

### Windows
- **RovoDev Config**: `%APPDATA%\rovodev\config.yml`
- **MCP Config**: `%APPDATA%\rovodev\mcp.json`
- **Project Path**: `C:\Users\[Username]\CODE\snap-educational-mcp\`

### Linux/Mac
- **RovoDev Config**: `~/.config/rovodev/config.yml`
- **MCP Config**: `~/.config/rovodev/mcp.json`
- **Project Path**: `/home/[username]/snap-educational-mcp/`

---

## 🔧 Advanced Configuration

### Multiple Environments

**Development (`mcp-dev.json`):**
```json
{
  "mcpServers": {
    "snap-dev": {
      "command": "C:\\path\\to\\snap-mcp\\run_mcp.bat",
      "env": {
        "DEBUG": "1",
        "LOG_LEVEL": "debug"
      }
    }
  }
}
```

**Production (`mcp-prod.json`):**
```json
{
  "mcpServers": {
    "snap-prod": {
      "command": "C:\\path\\to\\snap-mcp\\run_mcp.bat",
      "env": {
        "LOG_LEVEL": "info",
        "MAX_CONNECTIONS": "10"
      }
    }
  }
}
```

### Classroom Setup

**Teacher Config:**
```json
{
  "mcpServers": {
    "snap-teacher": {
      "command": "C:\\classroom\\snap-mcp\\run_mcp.bat",
      "env": {
        "COMPLEXITY": "advanced",
        "ENABLE_ADMIN": "true"
      }
    }
  }
}
```

**Student Config:**
```json
{
  "mcpServers": {
    "snap-student": {
      "command": "C:\\classroom\\snap-mcp\\run_mcp.bat",
      "env": {
        "COMPLEXITY": "beginner",
        "SAFE_MODE": "true"
      }
    }
  }
}
```

---

## 🐛 Troubleshooting

### Common Issues

**"MCP server not found"**
- Check file paths in `mcp.json`
- Use double backslashes `\\` in Windows paths
- Verify the batch file exists and is executable

**"Connection refused"**
- Ensure MCP server is running first
- Check port 8765 is not blocked
- Verify firewall settings

**"No MCP tools available"**
- Restart RovoDev CLI after config changes
- Check `config.yml` has correct `allowedMcpServers`
- Verify MCP server starts without errors

### Debug Commands

**Test MCP Server:**
```bash
# Check if server is running
netstat -an | findstr 8765  # Windows
netstat -an | grep 8765     # Linux/Mac
```

**Test RovoDev Config:**
```bash
rovodev config show
rovodev mcp list
```

**Validate JSON:**
```bash
# Check JSON syntax
python -m json.tool mcp.json
```

---

## 📋 Checklist

- [ ] MCP server starts without errors
- [ ] `config.yml` includes correct path
- [ ] `mcp.json` has valid JSON syntax
- [ ] File paths use correct format for OS
- [ ] RovoDev CLI can see MCP tools
- [ ] Claude responds to Snap! requests
- [ ] Browser extension connects successfully

---

## 🎯 Example Commands

Once everything is set up, try these with Claude:

```
"Create a Snap! program where the sprite draws a square"

"Make the sprite follow the mouse pointer"

"When I press space, make the sprite jump up and down"

"Create a simple game where the sprite catches falling objects"

"Make the sprite change colors when I click it"
```

---

## 📞 Quick Support

**Config Issues:**
1. Check file paths are correct
2. Verify JSON syntax is valid
3. Restart RovoDev after changes

**Connection Issues:**
1. Start MCP server first
2. Check firewall/antivirus
3. Verify port 8765 is available

**Runtime Issues:**
1. Check Python version (3.8+)
2. Verify all dependencies installed
3. Look at server console for errors

---

**Ready to go?** Start with: `rovodev chat` and ask Claude to create your first Snap! program! 🎉
