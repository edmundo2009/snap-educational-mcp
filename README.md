# Snap! Educational MCP System

**"describe programs in English, LLM translates intent, MCP orchestrates execution, and Snap! blocks appear automatically in the browser."**

## Quick Start

1. **Start a session:**
   ```bash
   llm "start a snap session"
   ```

2. **Open Snap! and connect:**
   - Go to https://snap.berkeley.edu/snap/snap.html
   - Install browser extension
   - Enter connection code

3. **Create programs with natural language:**
   ```bash
   llm "make the sprite jump when space is pressed"
   llm "create a bouncing ball game"
   llm "explain first-class functions for beginners"
   ```

## Architecture

```
Terminal (llm CLI) ←→ MCP Server (Python) ←→ Browser Extension (JavaScript) ←→ Snap! IDE
```

## Features

- **Real-time block creation** - Blocks appear instantly in browser
- **Educational explanations** - Kid-friendly concept explanations
- **Step-by-step tutorials** - Guided learning experiences
- **Advanced Snap! features** - First-class functions, custom blocks
- **Secure communication** - Token-based authentication
- **Debugging assistance** - Help with common programming issues
- **Lightweight architecture** - Fast startup, minimal dependencies (~50MB vs 500MB+)



## Project Structure

```
snap-llm-mcp/
├── mcp_server/          # MCP server and tools
├── snap_bridge/         # JavaScript bridge for Snap!
├── browser_extension/   # Chrome extension
├── knowledge/           # Educational content and block definitions
├── tests/              # Test files
├── examples/           # Sample projects and tutorials
└── docs/               # Documentation
```

