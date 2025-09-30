# Snap! Educational MCP System - Installation & Setup Tutorial

## 🎯 Overview

This tutorial will guide you through setting up the **Snap! Educational MCP System** - a revolutionary tool that lets children create Snap! programs using natural language through Claude or other LLMs.

### What You'll Learn:
- Install and configure the browser extension
- Set up the MCP server
- Connect with Claude via RovoDev CLI
- Create your first Snap! program with natural language

---

## 📋 Prerequisites

- **Windows 10/11** (Linux/Mac support coming soon)
- **Chrome or Firefox** browser
- **Python 3.8+** installed
- **Claude access** (via Anthropic or RovoDev CLI)

---

## 🚀 Part 1: Install Browser Extension

### Chrome Installation

1. **Download Extension Files**
   ```bash
   # Clone or download the project
   git clone https://github.com/your-repo/snap-educational-mcp.git
   cd snap-educational-mcp
   ```

2. **Load Extension in Chrome**
   - Open Chrome and go to `chrome://extensions/`
   - Enable **"Developer mode"** (toggle in top-right)
   - Click **"Load unpacked"**
   - Select the `browser_extension/` folder
   - The Snap! MCP extension should appear in your extensions list

3. **Verify Installation**
   - Look for the Snap! MCP icon in your browser toolbar
   - Click it to see the connection status (should show "Disconnected" initially)

### Firefox Installation

1. **Prepare Extension for Firefox**
   ```bash
   cd browser_extension/
   # Firefox uses manifest v2, Chrome uses v3
   # The extension supports both automatically
   ```

2. **Load Extension in Firefox**
   - Open Firefox and go to `about:debugging`
   - Click **"This Firefox"**
   - Click **"Load Temporary Add-on"**
   - Select `browser_extension/manifest.json`
   - The extension will be loaded temporarily

3. **For Permanent Installation** (Optional)
   - Package the extension: `web-ext build` (requires web-ext tool)
   - Install the generated `.xpi` file

---

## 🔧 Part 2: Set Up MCP Server

### Install Dependencies

1. **Create Virtual Environment**
   ```bash
   cd snap-educational-mcp
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

2. **Install Requirements**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Installation**
   ```bash
   python -c "from mcp_server.main import initialize_snap_system; print('✅ MCP Server ready!')"
   ```

### Create Startup Script

Create `run_mcp.bat` (Windows) or `run_mcp.sh` (Linux/Mac):

**Windows (`run_mcp.bat`):**
```batch
@echo off
cd /d "C:\Users\Administrator\CODE\snap-educational-mcp"
call venv\Scripts\activate
python -m mcp_server.main
```

**Linux/Mac (`run_mcp.sh`):**
```bash
#!/bin/bash
cd "/path/to/snap-educational-mcp"
source venv/bin/activate
python -m mcp_server.main
```

Make it executable:
```bash
chmod +x run_mcp.sh
```

---

## 🌐 Part 3: RovoDev CLI Integration

### Install RovoDev CLI

### Configure MCP Server

1. **Create/Edit `config.yml`**
   ```yaml
   # config.yml
   allowedMcpServers: 
     - C:\Users\Administrator\CODE\snap-educational-mcp\run_mcp.bat
   ```

2. **Create/Edit `mcp.json`**
   ```json
   {
     "mcpServers": {
       "snap-automation": {
         "command": "C:\\Users\\Administrator\\CODE\\snap-educational-mcp\\run_mcp.bat",
         "args": [],
         "env": {}
       }
     }
   }
   ```

3. **Update Paths**
   - Replace `C:\Users\Administrator\CODE\snap-educational-mcp\` with your actual project path
   - Use forward slashes `/` for Linux/Mac paths
   - Use double backslashes `\\` for Windows paths in JSON

### Test MCP Connection

1. **Start RovoDev CLI**
   ```bash
   rovodev chat
   ```

2. **Test MCP Tools**
   ```
   You: Can you list the available MCP tools?
   Claude: I can see the Snap! Educational MCP tools are available...
   ```

---

## 🔗 Part 4: Connect Browser Extension

### Generate Connection Token

1. **Start the MCP Server**
   ```bash
   # Run your startup script
   ./run_mcp.bat  # Windows
   ./run_mcp.sh   # Linux/Mac
   ```

2. **Get Connection Token**
   - The server will display a connection token in the console
   - Look for: `🔑 Connection Token: snap_token_abc123...`
   - Copy this token (it expires in 5 minutes)

### Connect Extension

1. **Open Snap! IDE**
   - Go to [https://snap.berkeley.edu/snap/snap.html](https://snap.berkeley.edu/snap/snap.html)
   - Wait for Snap! to fully load

2. **Activate Extension**
   - Click the Snap! MCP extension icon in your browser
   - Paste the connection token
   - Click **"Connect"**
   - Status should change to **"Connected ✅"**

3. **Verify Connection**
   - Check the browser console (F12) for connection messages
   - Check the MCP server console for "Browser connected" message

---

## 🎮 Part 5: Your First Natural Language Program

### Using Claude with RovoDev

1. **Start a Chat Session**
   ```bash
   rovodev chat
   ```

2. **Create Your First Program**
   ```
   You: Create a Snap! program where when I press the space key, the sprite jumps up and down

   Claude: I'll create a jumping sprite program for you! Let me use the Snap! MCP tools...

   [Claude will use the MCP tools to generate and send blocks to your browser]
   ```

3. **Watch the Magic**
   - Blocks will automatically appear in your Snap! IDE
   - The sprite will be programmed to jump when space is pressed
   - Click the green flag to test!

### Example Commands to Try

```
"Make the sprite move in a square when the flag is clicked"

"Create a program where the sprite follows the mouse pointer"

"When I press the arrow keys, move the sprite in that direction"

"Make the sprite change colors every second"

"Create a simple drawing program where the sprite draws when I move the mouse"
```

---

## 🔧 Part 6: Troubleshooting

### Common Issues

**Extension Not Connecting:**
- Check if MCP server is running
- Verify the connection token hasn't expired
- Check browser console for error messages
- Ensure WebSocket port 8765 is not blocked

**MCP Server Won't Start:**
- Check Python version: `python --version` (needs 3.8+)
- Verify all dependencies installed: `pip list`
- Check for port conflicts (default: 8765)

**Claude Can't See MCP Tools:**
- Verify `mcp.json` configuration
- Check file paths in config
- Restart RovoDev CLI
- Ensure MCP server is running before starting Claude

**Blocks Not Appearing in Snap!:**
- Refresh the Snap! page
- Reconnect the extension
- Check browser console for JavaScript errors
- Verify Snap! is fully loaded before connecting

### Debug Mode

Enable debug logging:

1. **MCP Server Debug**
   ```bash
   # Add to run_mcp.bat/sh
   set DEBUG=1  # Windows
   export DEBUG=1  # Linux/Mac
   ```

2. **Browser Extension Debug**
   - Open browser console (F12)
   - Look for Snap! MCP messages
   - Check Network tab for WebSocket connections

---

## 🎓 Part 7: Educational Usage

### For Teachers

**Classroom Setup:**
1. Install extension on all classroom computers
2. Run MCP server on teacher's machine
3. Share connection tokens with students
4. Use Claude to demonstrate programming concepts

**Lesson Ideas:**
- "Create a sprite that draws geometric shapes"
- "Make an interactive story with multiple characters"
- "Build a simple game with scoring"
- "Animate a sprite to show mathematical concepts"

### For Students

**Getting Started:**
1. Describe what you want your sprite to do in plain English
2. Watch as Claude converts your ideas into Snap! blocks
3. Run your program and see it work!
4. Modify and experiment with the generated code

**Learning Progression:**
- Start with simple movements and sounds
- Progress to interactive programs with key presses
- Learn about loops and conditions through natural language
- Create complex projects combining multiple concepts

---

## 📚 Next Steps

- Explore the [Snap! API Reference](snap_api_reference.md)
- Read about [Educational Philosophy](educational_philosophy.md)
- Check out [Advanced Usage Examples](advanced_examples.md)
- Join the community discussions

---

## ⚙️ Part 8: Advanced Configuration

### Custom MCP Server Settings

Create `mcp_server/config.json` for custom settings:

```json
{
  "server": {
    "host": "localhost",
    "port": 8765,
    "token_expiry_minutes": 5
  },
  "education": {
    "default_complexity": "beginner",
    "enable_explanations": true,
    "max_blocks_per_script": 50
  },
  "security": {
    "require_token": true,
    "allowed_origins": ["https://snap.berkeley.edu"]
  }
}
```

### Multiple RovoDev Profiles

For different users or classrooms:

**Teacher Profile (`teacher_mcp.json`):**
```json
{
  "mcpServers": {
    "snap-teacher": {
      "command": "C:\\path\\to\\snap-mcp\\run_mcp.bat",
      "env": {
        "SNAP_MODE": "teacher",
        "COMPLEXITY": "advanced"
      }
    }
  }
}
```

**Student Profile (`student_mcp.json`):**
```json
{
  "mcpServers": {
    "snap-student": {
      "command": "C:\\path\\to\\snap-mcp\\run_mcp.bat",
      "env": {
        "SNAP_MODE": "student",
        "COMPLEXITY": "beginner"
      }
    }
  }
}
```

### Network Configuration

**For School Networks:**
- Open firewall port 8765 for WebSocket connections
- Add `snap.berkeley.edu` to allowed sites
- Configure proxy settings if needed

**For Remote Access:**
```yaml
# config.yml - Allow remote connections
server:
  host: "0.0.0.0"  # Listen on all interfaces
  port: 8765
  ssl_cert: "/path/to/cert.pem"  # Optional SSL
  ssl_key: "/path/to/key.pem"
```

---

## 🔍 Part 9: Verification Checklist

### ✅ Installation Checklist

- [ ] Python 3.8+ installed and working
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Browser extension loaded in Chrome/Firefox
- [ ] RovoDev CLI installed and configured
- [ ] MCP server starts without errors
- [ ] Extension connects to server successfully
- [ ] Claude can see and use MCP tools
- [ ] Blocks appear in Snap! IDE when requested

### ✅ Connection Test

Run this test sequence:

1. **Start MCP Server**
   ```bash
   ./run_mcp.bat
   # Should show: "🚀 Snap! MCP Server running on ws://localhost:8765"
   ```

2. **Connect Extension**
   - Copy token from server console
   - Paste in extension popup
   - Should show: "Connected ✅"

3. **Test with Claude**
   ```
   You: Use the Snap! MCP tools to create a simple program
   Claude: I'll help you create a Snap! program...
   ```

4. **Verify in Snap!**
   - Blocks should appear automatically
   - Scripts should be executable
   - Green flag should work

---

## 🆘 Support & Resources

### Documentation
- **[Snap! API Reference](snap_api_reference.md)** - Complete block reference
- **[Educational Philosophy](educational_philosophy.md)** - Teaching approach
- **[WebSocket Protocol](../WebSocket%20Protocol%20Specification%20-%20SnapBridge.md)** - Technical details

### Community
- **GitHub Issues**: Report bugs and request features
- **Discussions**: Share ideas and get help
- **Wiki**: Community-contributed guides and examples

### Quick Help Commands

**Check MCP Server Status:**
```bash
curl -I http://localhost:8765/health
```

**Test WebSocket Connection:**
```javascript
// In browser console
const ws = new WebSocket('ws://localhost:8765');
ws.onopen = () => console.log('✅ WebSocket connected');
ws.onerror = (e) => console.log('❌ WebSocket error:', e);
```

**Validate Extension:**
```javascript
// In Snap! console
console.log('SnapBridge:', window.SnapBridge ? '✅ Loaded' : '❌ Missing');
```

---

## 🎯 Success Metrics

You'll know everything is working when:

- ✅ **Extension shows "Connected"** status
- ✅ **Claude responds** with "I can help you create Snap! programs..."
- ✅ **Blocks appear automatically** in Snap! IDE
- ✅ **Programs run correctly** when you click the green flag
- ✅ **Natural language commands** generate appropriate code
- ✅ **Students can create programs** without writing code

---

**🎉 Congratulations!** You've successfully set up the Snap! Educational MCP System.

**Ready to revolutionize programming education?** Start with simple commands like:
- *"Make the sprite say hello when I click it"*
- *"Create a program that draws a rainbow"*
- *"When I press space, make the sprite jump"*

The future of programming education is here! 🚀
