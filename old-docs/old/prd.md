# Snap! Block Automation System - PRD

## Executive Summary

Create an educational programming system where children can describe what they want in natural language via terminal LLM, which uses MCP tools to generate and execute Snap! blocks programmatically. Unlike Scratch, Snap! has full JavaScript scripting capabilities, enabling true automation of block creation.

## Vision Statement

**"Kids describe programs in English, LLM translates intent, MCP orchestrates execution, and Snap! blocks appear automatically in the browser."**

This leverages Snap!'s superior scripting capabilities to create a seamless natural language → visual programming pipeline.

---

## Product Architecture

### High-Level Flow
```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER WORKFLOW                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Child in Terminal              LLM Processing           Snap! IDE   │
│  ┌──────────────┐              ┌──────────────┐         ┌─────────┐ │
│  │ "Make cat    │──────────────→│  Claude/GPT │────────→│ Blocks  │ │
│  │  jump when   │   Natural     │   analyzes  │  MCP    │ appear! │ │
│  │  space key"  │   Language    │   intent    │  tools  │         │ │
│  └──────────────┘              └──────────────┘         └─────────┘ │
│         ↓                              ↓                      ↑      │
│    llm cli                      Structured                   │      │
│    (terminal)                   Intent Data                  │      │
│                                       ↓                       │      │
│                              ┌────────────────┐              │      │
│                              │  MCP Server    │              │      │
│                              │  (Python)      │              │      │
│                              │  - Parse       │              │      │
│                              │  - Validate    │              │      │
│                              │  - Generate    │              │      │
│                              │  - Format      │              │      │
│                              └────────┬───────┘              │      │
│                                       ↓                      │      │
│                              ┌────────────────┐              │      │
│                              │ Snap! Bridge   │──────────────┘      │
│                              │ (JavaScript)   │   WebSocket/HTTP    │
│                              │ - Execute JS   │                     │
│                              │ - Create blocks│                     │
│                              │ - Manipulate   │                     │
│                              │   IDE          │                     │
│                              └────────────────┘                     │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Why Snap! Instead of Scratch?

### Technical Superiority
| Feature                   | Scratch            | Snap!                    | Impact                |
|---------------------------|--------------------|--------------------------|-----------------------|
| **JavaScript API**        | ❌ No scripting     | ✅ Full DOM access        | Direct block creation |
| **Programmatic Control**  | ❌ File export only | ✅ Real-time manipulation | Live automation       |
| **First-Class Functions** | ❌ Limited          | ✅ Full lambda support    | Advanced concepts     |
| **Custom Blocks**         | ❌ Manual only      | ✅ Scriptable creation    | Dynamic curriculum    |
| **XML Manipulation**      | ❌ Limited          | ✅ Direct DOM access      | Precise control       |
| **Extension System**      | ❌ Restricted       | ✅ Open architecture      | Easy integration      |

### Educational Advantages
- **Berkeley pedigree**: Created by CS education experts
- **Higher-order functions**: Teaches advanced concepts
- **Data structures**: Real lists, tables, objects
- **Metaprogramming**: Create blocks that create blocks
- **Academic rigor**: Used in university CS courses

---

## System Components

### 1. Terminal Interface (User Layer)
**Technology**: `llm` CLI by Simon Willison

```bash
# Child types natural language
$ llm -m claude-3.5-sonnet "make the cat jump when I press space"

# LLM uses MCP to process request
# Snap! browser automatically updates with blocks
```

**Key Features**:
- Simple command-line interface for kids
- Conversation history for iterative development
- Error messages in kid-friendly language
- Visual feedback in terminal + browser

### 2. MCP Server (Orchestration Layer)
**Technology**: Python FastMCP

**Core Responsibilities**:
- Parse natural language intents
- Validate requests against curriculum
- Generate Snap! block specifications
- Communicate with Snap! bridge
- Provide educational feedback

**MCP Tools** (similar to our Scratch design):
```python
@mcp.tool()
def generate_snap_blocks(description: str, complexity: str = "beginner")
    """Convert natural language to Snap! block specifications"""

@mcp.tool()
def explain_snap_concept(concept: str, age_level: str = "beginner")
    """Explain programming concepts for Snap!"""

@mcp.tool()
def create_snap_tutorial(goal: str, difficulty: str = "beginner")
    """Generate step-by-step Snap! tutorials"""

@mcp.tool()
def execute_snap_script(block_spec: dict, target_sprite: str = "Sprite")
    """Send block specifications to Snap! for execution"""

@mcp.tool()
def inspect_snap_project()
    """Read current Snap! project state"""

@mcp.tool()
def debug_snap_blocks(error_description: str)
    """Help debug Snap! programming issues"""
```

### 3. Snap! Bridge (Execution Layer)
**Technology**: JavaScript (runs in browser with Snap!)

**Core Capabilities**:
```javascript
// Snap! Bridge API
class SnapBridge {
    // Block creation
    createBlock(opcode, inputs, position)
    createCustomBlock(definition, category)
    
    // Block manipulation
    connectBlocks(block1, block2)
    moveBlock(block, x, y)
    deleteBlock(block)
    
    // Script management
    createScript(blockSequence, sprite)
    getScripts(sprite)
    exportProject()
    
    // IDE control
    selectSprite(name)
    createSprite(name, costume)
    setStageSize(width, height)
    
    // Real-time feedback
    highlightBlock(block)
    showExplanation(text, position)
    animateBlockCreation(block)
}
```

### 4. Knowledge Base (Data Layer)
**Technology**: JSON (Snap!-specific definitions)

**Structure**:
```json
{
  "snap_blocks": {
    "motion": {
      "forward": {
        "xml_template": "<block s=\"forward\"><l>10</l></block>",
        "javascript_api": "sprite.forward(10)",
        "kid_explanation": "Makes your sprite move forward!",
        "parameters": ["steps"],
        "category": "motion"
      }
    }
  },
  "snap_features": {
    "first_class_functions": {...},
    "custom_blocks": {...},
    "list_operations": {...}
  }
}
```

---

## Technical Architecture

### Communication Protocol

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   llm CLI   │         │ MCP Server  │         │ Snap! IDE   │
│  (Terminal) │         │  (Python)   │         │ (Browser)   │
└─────┬───────┘         └──────┬──────┘         └──────┬──────┘
      │                        │                       │
      │ 1. Natural Language    │                       │
      │────────────────────────→                       │
      │                        │                       │
      │                   2. Parse & Generate          │
      │                        │                       │
      │                        │ 3. Block Specs        │
      │                        │      (JSON)           │
      │                        ├───────────────────────→
      │                        │                       │
      │                        │                  4. Execute
      │                        │                   JavaScript
      │                        │                   Create Blocks
      │                        │                       │
      │                        │ 5. Confirmation       │
      │                        │←──────────────────────┤
      │                        │                       │
      │ 6. Success + Next Steps│                       │
      │←───────────────────────┤                       │
      │                        │                       │
```

### Bridge Communication Options

#### Option A: WebSocket (Recommended)
```javascript
// In Snap! IDE
const bridge = new WebSocket('ws://localhost:8765');

bridge.onmessage = (event) => {
    const command = JSON.parse(event.data);
    executeSnapCommand(command);
    bridge.send(JSON.stringify({status: 'success', blocks_created: 3}));
};
```

**Pros**: Real-time, bidirectional, perfect for live updates
**Cons**: Requires WebSocket server

#### Option B: HTTP Server in Browser
```javascript
// Simple HTTP server embedded in Snap! page
const server = new SimpleHTTPServer(3000);
server.on('/execute', (req, res) => {
    const blocks = createBlocksFromSpec(req.body);
    res.json({success: true, blocks: blocks.length});
});
```

**Pros**: Simple, stateless, easier debugging
**Cons**: Polling required for updates

#### Option C: Browser Extension
```javascript
// Chrome extension injects bridge into Snap! page
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'CREATE_BLOCKS') {
        const result = createSnapBlocks(request.blocks);
        sendResponse({success: true, result: result});
    }
});
```

**Pros**: Clean separation, secure, no CORS issues
**Cons**: Requires extension installation

---

## Snap! JavaScript API Deep Dive

### Block Creation Examples

```javascript
// Example 1: Create simple motion block
function createForwardBlock(steps) {
    const ide = world.children[0];
    const sprite = ide.currentSprite;
    
    // Create block programmatically
    const block = SpriteMorph.prototype.blockForSelector('forward');
    block.setSpec('move %n steps');
    block.inputs()[0].setContents(steps);
    
    // Add to sprite's scripts
    sprite.scripts.add(block);
    block.setPosition(new Point(50, 50));
}

// Example 2: Create event-triggered script
function createKeyPressScript(key, action) {
    const whenKeyBlock = SpriteMorph.prototype.blockForSelector('receiveKey');
    whenKeyBlock.inputs()[0].setContents(key);
    
    const actionBlock = createBlockFromSpec(action);
    whenKeyBlock.nextBlock(actionBlock);
    
    sprite.scripts.add(whenKeyBlock);
}

// Example 3: Create custom block
function createCustomBlock(name, definition, category) {
    const customBlock = new CustomBlockDefinition(
        name,
        sprite,
        true // make it global
    );
    
    customBlock.body = new Context(null, definition);
    customBlock.category = category;
    
    sprite.customBlocks.push(customBlock);
    ide.flushBlocksCache();
    ide.refreshPalette();
}
```

### Reading Snap! State

```javascript
// Get all blocks in current sprite
function getAllBlocks() {
    const sprite = ide.currentSprite;
    const scripts = sprite.scripts.children;
    return scripts.map(script => {
        return {
            position: {x: script.position().x, y: script.position().y},
            blocks: script.allChildren().filter(m => m instanceof BlockMorph)
        };
    });
}

// Export project as XML
function exportProject() {
    const ide = world.children[0];
    const xml = ide.serializer.serialize(ide.stage);
    return xml;
}

// Get sprite information
function getSpriteInfo(spriteName) {
    const sprite = ide.sprites.find(s => s.name === spriteName);
    return {
        name: sprite.name,
        position: {x: sprite.xPosition(), y: sprite.yPosition()},
        costume: sprite.costume.name,
        scriptCount: sprite.scripts.children.length
    };
}
```

---

## Data Flow Specifications

### Intent → Block Specification
```json
{
  "intent": {
    "user_input": "make the cat jump when space is pressed",
    "parsed": {
      "trigger": "key_press",
      "key": "space",
      "action": "jump",
      "subject": "sprite",
      "parameters": {
        "jump_height": 50
      }
    }
  },
  "block_specification": {
    "scripts": [
      {
        "trigger": {
          "type": "event",
          "selector": "receiveKey",
          "inputs": ["space"]
        },
        "blocks": [
          {
            "type": "motion",
            "selector": "changeYBy",
            "inputs": [50]
          },
          {
            "type": "control",
            "selector": "doWait",
            "inputs": [0.3]
          },
          {
            "type": "motion",
            "selector": "changeYBy",
            "inputs": [-50]
          }
        ],
        "position": {"x": 50, "y": 50},
        "sprite": "Sprite"
      }
    ],
    "explanation": "When you press space, the sprite jumps up and comes back down!",
    "difficulty": "beginner"
  }
}
```

### MCP → Snap! Bridge Communication
```json
{
  "command": "create_blocks",
  "target_sprite": "Sprite",
  "scripts": [
    {
      "blocks": [
        {
          "opcode": "receiveKey",
          "inputs": {"KEY": "space"},
          "next": "block_2"
        },
        {
          "id": "block_2",
          "opcode": "changeYBy",
          "inputs": {"Y": 50},
          "next": "block_3"
        },
        {
          "id": "block_3",
          "opcode": "doWait",
          "inputs": {"DURATION": 0.3},
          "next": "block_4"
        },
        {
          "id": "block_4",
          "opcode": "changeYBy",
          "inputs": {"Y": -50},
          "next": null
        }
      ],
      "position": {"x": 50, "y": 50}
    }
  ],
  "visual_feedback": {
    "animate": true,
    "highlight_duration": 2000,
    "show_explanation": true
  }
}
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
**Goal**: Establish basic communication between terminal and Snap!

**Deliverables**:
- MCP server with basic intent parsing
- Snap! bridge with WebSocket connection
- Simple block creation (forward, turn, say)
- Terminal → Browser → Block creation working

**Success Criteria**:
- "make sprite move forward" creates a forward block in Snap!
- Kid can see block appear in real-time
- Basic error handling works

### Phase 2: Core Features (Week 3-4)
**Goal**: Implement educational block generation

**Deliverables**:
- Complete knowledge base (Snap! blocks, patterns)
- Event-driven scripts (key press, click)
- Concept explanations
- Step-by-step tutorials

**Success Criteria**:
- 20+ common patterns working
- "when space pressed jump" creates complete script
- Educational explanations appear in terminal

### Phase 3: Advanced Features (Week 5-6)
**Goal**: Leverage Snap!'s advanced capabilities

**Deliverables**:
- Custom block creation
- First-class function examples
- List manipulation
- Project templates

**Success Criteria**:
- "create a custom jump block" works
- Can teach higher-order functions
- Generate complete game templates

### Phase 4: Polish & UX (Week 7-8)
**Goal**: Make it delightful for kids

**Deliverables**:
- Visual feedback animations
- Progressive curriculum
- Error recovery
- Parent/teacher dashboard

**Success Criteria**:
- Kids can use independently
- Clear learning progression
- Handles mistakes gracefully

---

## Technical Stack

### Terminal Layer
- **llm CLI**: Simon Willison's LLM tool
- **MCP Client**: Built into llm via plugins
- **Rich**: Terminal UI enhancements

### MCP Server Layer
- **Python 3.10+**: Core language
- **FastMCP**: MCP server framework
- **Pydantic**: Data validation
- **asyncio**: Async communication
- **websockets**: Real-time communication

### Snap! Bridge Layer
- **Vanilla JavaScript**: No frameworks needed
- **WebSocket API**: Browser native
- **Snap! Internal APIs**: Direct DOM manipulation
- **Service Worker** (optional): Background processing

### Knowledge Base
- **JSON**: Block definitions
- **YAML** (optional): Tutorials and curricula
- **Git**: Version control for educational content

---

## Directory Structure

```
snap-llm-mcp/
├── README.md
├── requirements.txt
├── setup.py
│
├── mcp_server/
│   ├── main.py                      # MCP server entry
│   ├── tools/
│   │   ├── block_generator.py       # Core generation logic
│   │   ├── concept_explainer.py     # Educational content
│   │   ├── tutorial_creator.py      # Step-by-step guides
│   │   └── snap_communicator.py     # Bridge communication
│   ├── parsers/
│   │   ├── intent_parser.py         # NL → Intent
│   │   └── validators.py            # Input validation
│   └── knowledge/
│       ├── snap_blocks.json         # Block definitions
│       ├── patterns.json            # Common patterns
│       └── curriculum.json          # Learning progression
│
├── snap_bridge/
│   ├── bridge.js                    # Main bridge code
│   ├── block_creator.js             # Block manipulation
│   ├── snap_api_wrapper.js          # Snap! API helpers
│   ├── websocket_client.js          # Communication
│   └── visual_feedback.js           # Animations & UI
│
├── browser_extension/               # Optional
│   ├── manifest.json
│   ├── background.js
│   └── content_script.js
│
├── tests/
│   ├── test_mcp_tools.py
│   ├── test_intent_parsing.py
│   ├── test_block_generation.py
│   └── test_integration.py
│
├── examples/
│   ├── sample_queries.md
│   ├── generated_snap_projects/
│   └── tutorial_sequences/
│
└── docs/
    ├── snap_api_reference.md
    ├── mcp_tool_docs.md
    ├── deployment_guide.md
    └── educational_philosophy.md
```

---

## Future Enhancements

### Short Term (Months 3-6)
- Multi-sprite coordination
- Voice input via speech-to-text
- Mobile app integration
- Collaborative programming

### Long Term (6-12 Months)
- AI tutoring system
- Curriculum generator
- Assessment tools
- Teacher dashboard

### Research Directions
- Optimal teaching strategies
- Personalized learning paths
- Cognitive load optimization
- Transfer to text-based languages

---

## Appendix

### Snap! vs Scratch Technical Comparison

```javascript
// Snap! - Direct JavaScript Manipulation
const sprite = ide.currentSprite;
const block = sprite.blockForSelector('forward');
block.inputs()[0].setContents(100);
sprite.scripts.add(block);

// Scratch - No JavaScript API
// Must export/import .sb3 files
// No real-time manipulation
```

### MCP Tool Signatures

```python
# Detailed MCP tool specifications
@mcp.tool()
async def generate_snap_blocks(
    description: str,
    complexity: Literal["beginner", "intermediate", "advanced"] = "beginner",
    output_format: Literal["execute", "preview", "explain"] = "execute",
    target_sprite: str = "Sprite",
    animate: bool = True
) -> SnapBlockResponse:
    """
    Generate and optionally execute Snap! blocks from natural language.
    
    Args:
        description: Natural language description of desired program
        complexity: Difficulty level for educational appropriateness
        output_format: Whether to execute, preview, or just explain
        target_sprite: Which sprite to add blocks to
        animate: Show visual feedback during creation
    
    Returns:
        SnapBlockResponse with blocks, explanations, and execution status
    """
```

This PRD provides a comprehensive blueprint for building an educational programming system that leverages Snap!'s JavaScript capabilities while maintaining the kid-friendly educational approach from our Scratch POC.

---

## Current Implementation Status

### Actual Architecture (As Implemented)

The system has evolved from the original PRD design into a more complex architecture that handles both MCP client communication and browser extension integration:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ACTUAL SYSTEM ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  RovoDev CLI                    MCP Server                    Browser Extension  │
│  ┌──────────────┐              ┌──────────────┐              ┌─────────────────┐ │
│  │ config.yml   │              │ main.py      │              │ Chrome Extension│ │
│  │ mcp.json     │──────────────→│ STDIO Mode   │              │ + Content Script│ │
│  │ run_mcp.bat  │   MCP/STDIO  │ + WebSocket  │              │ + Popup         │ │
│  └──────────────┘              │ Server       │              └─────────────────┘ │
│         ↓                       └──────┬───────┘                      ↓          │
│    Creates Session                     │                        Connects with    │
│    via MCP Tools                       │                        Token            │
│                                        │                              ↓          │
│                              ┌─────────┴─────────┐              ┌─────────────┐  │
│                              │ File-Based        │              │ Snap! IDE   │  │
│                              │ Session Storage   │              │ (Browser)   │  │
│                              │ active_sessions   │              │ - Bridge    │  │
│                              │ .json             │              │ - WebSocket │  │
│                              └───────────────────┘              │ - Block API │  │
│                                        ↑                        └─────────────┘  │
│                              Shared between processes                            │
│                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Key Implementation Files

#### Core MCP Server
- **`mcp_server/main.py`**: Main server with dual STDIO+WebSocket mode
- **`mcp_server/tools/snap_communicator.py`**: WebSocket server for browser communication
- **`run_mcp.bat`**: Entry point for RovoDev CLI integration

#### Browser Extension
- **`browser_extension/manifest.json`**: Chrome extension configuration
- **`browser_extension/content_script.js`**: Injected into Snap! pages
- **`browser_extension/popup.js`**: Extension UI for token entry
- **`browser_extension/snap_bridge/`**: Bridge scripts injected into Snap!

#### Bridge Components (Injected into Snap!)
- **`browser_extension/snap_bridge/bridge.js`**: Main coordination layer
- **`browser_extension/snap_bridge/websocket_client.js`**: WebSocket communication
- **`browser_extension/snap_bridge/block_creator.js`**: Snap! block manipulation
- **`browser_extension/snap_bridge/snap_api_wrapper.js`**: Snap! API helpers

#### Session Management
- **`active_sessions.json`**: File-based session sharing between processes
- **Token system**: 8-character display tokens mapped to full session IDs

### RovoDev Integration

#### Configuration Files
```yaml
# config.yml
allowedMcpServers:
  - C:\Users\Administrator\CODE\snap-educational-mcp\run_mcp.bat
```

```json
// mcp.json
{
  "mcpServers": {
    "snap-automation": {
      "command": "C:\\Users\\Administrator\\CODE\\snap-educational-mcp\\run_mcp.bat"
    }
  }
}
```

#### Entry Point
```batch
@echo off
chcp 65001 >nul
cd /d "C:\Users\Administrator\CODE\snap-educational-mcp"
call venv\Scripts\activate.bat
set PYTHONIOENCODING=utf-8
python -m mcp_server.main
```

### Current Working Features

✅ **MCP Server Initialization**: Loads knowledge base, starts dual servers
✅ **Session Creation**: `start_snap_session()` creates tokens and sessions
✅ **File-Based Session Sharing**: Sessions persist across process boundaries
✅ **WebSocket Server**: Runs on `ws://localhost:8765`
✅ **Browser Extension**: Injects bridge into Snap! pages
✅ **Token Authentication**: Browser connects with 8-character tokens
✅ **Duplicate Loading Protection**: Prevents script conflicts

### Current Issues

❌ **Connection Instability**: WebSocket connects but immediately disconnects (code 1011)
❌ **Snap! Readiness Detection**: Extension can't detect when Snap! is fully loaded
❌ **Session State Synchronization**: Connection status not properly updated
❌ **Error Recovery**: Poor handling of connection failures

---

## Connection Troubleshooting History

This section documents the extensive trial-and-error process to establish reliable communication between RovoDev CLI and the Chrome browser extension through the MCP server.

### Problem Statement

**Original Issue**: RovoDev CLI creates MCP sessions, but the browser extension cannot connect to those sessions because they run in separate processes with isolated memory spaces.

**User's Use Case**:
1. RovoDev CLI starts MCP server and creates a session
2. CLI shows "Waiting for browser connection..." with token (e.g., `BE1B1223`)
3. User enters token in browser extension
4. Browser should connect to the same session created by CLI
5. CLI should show "Connected: Yes" when browser connects

### Architecture Challenge: Process Isolation

#### The Core Problem
- **RovoDev CLI Process**: Runs `python -m mcp_server.main --stdio`
- **WebSocket Server Process**: Needs to run simultaneously for browser connections
- **Memory Isolation**: Each Python process has its own `active_sessions` dictionary
- **Session Mismatch**: Sessions created in CLI process not visible to WebSocket server process

#### Initial Assumptions (Incorrect)
1. **Assumption**: RovoDev CLI and WebSocket server could share memory
   - **Reality**: Separate processes cannot share Python objects
2. **Assumption**: STDIO mode would keep server running indefinitely
   - **Reality**: STDIO server exits when input stream ends
3. **Assumption**: WebSocket connections were failing due to network issues
   - **Reality**: Server process was terminating, killing WebSocket server

### Attempted Solutions and Failures

#### Attempt 1: Separate Server Processes
**Files Modified**: None (testing approach)
**Assumption**: Run WebSocket server separately from RovoDev CLI
**Implementation**: Started standalone WebSocket server in separate terminal
**Result**: ❌ **FAILED** - Sessions created by CLI not visible to separate server
**Lesson**: Confirmed process isolation was the root cause

#### Attempt 2: Combined STDIO + WebSocket Server (Threading)
**Files Modified**: `mcp_server/main.py` (lines 968-1008)
**Assumption**: Run both servers in same process using threading
**Implementation**:
```python
# Added threading approach
import threading
import asyncio

def run_websocket_server():
    """Run WebSocket server in separate thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(bridge_communicator.start_server())
        loop.run_forever()
    except Exception as e:
        print(f"❌ WebSocket server error: {e}")

# Start WebSocket server in background thread
websocket_thread = threading.Thread(target=run_websocket_server, daemon=True)
websocket_thread.start()

# Run STDIO server in main thread
mcp.run(transport="stdio")
```
**Result**: ❌ **FAILED** - STDIO server still exited immediately after processing input
**Issue**: When RovoDev CLI finished sending commands, STDIO server terminated, killing entire process
**Lesson**: Need to keep STDIO server alive or handle its termination gracefully

#### Attempt 3: File-Based Session Storage
**Files Modified**: `mcp_server/main.py` (lines 34-78, 166-175, 180-192, 243-268)
**Assumption**: Share session data between processes using JSON file
**Implementation**:
```python
# Added file-based session persistence
SESSIONS_FILE = Path("active_sessions.json")

def load_sessions():
    """Load sessions from file"""
    if SESSIONS_FILE.exists():
        try:
            with open(SESSIONS_FILE, 'r') as f:
                data = json.load(f)
                # Convert datetime strings back to datetime objects
                for session_id, session_data in data.items():
                    if 'created_at' in session_data:
                        session_data['created_at'] = datetime.fromisoformat(session_data['created_at'])
                return data
        except Exception as e:
            print(f"⚠️ Error loading sessions: {e}")
    return {}

def save_sessions():
    """Save sessions to file"""
    try:
        data_to_save = {}
        for session_id, session_data in active_sessions.items():
            session_copy = session_data.copy()
            if 'created_at' in session_copy:
                session_copy['created_at'] = session_copy['created_at'].isoformat()
            data_to_save[session_id] = session_copy

        with open(SESSIONS_FILE, 'w') as f:
            json.dump(data_to_save, f, indent=2)
    except Exception as e:
        print(f"⚠️ Error saving sessions: {e}")
```
**Result**: ✅ **PARTIALLY SUCCESSFUL** - Sessions now shared between processes
**Issue**: Server still terminated after STDIO client disconnected
**Lesson**: File-based sharing works, but server persistence still needed

#### Attempt 4: Server Persistence After STDIO Termination
**Files Modified**: `mcp_server/main.py` (lines 1009-1038)
**Assumption**: Keep process alive after STDIO server ends to maintain WebSocket server
**Implementation**:
```python
try:
    # Run STDIO server in main thread (blocking)
    mcp.run(transport="stdio")
except KeyboardInterrupt:
    print("\n👋 Servers stopped by user")
except Exception as e:
    print(f"\n❌ Server error: {e}")
    sys.exit(1)

# If STDIO server exits normally, keep WebSocket server running
try:
    print("\n🔄 STDIO client disconnected, but WebSocket server continues running...")
    print("🌐 Browser extension can still connect on ws://localhost:8765")

    # Keep the process alive so WebSocket server continues running
    while True:
        import time
        time.sleep(1)
except KeyboardInterrupt:
    print("\n👋 All servers stopped")
```
**Result**: ✅ **SUCCESSFUL** - Server now stays alive after STDIO client disconnects
**Issue**: I/O errors when trying to print after stdout is closed
**Lesson**: Need proper I/O handling when pipe is closed

#### Attempt 5: Proper I/O Handling for Closed Pipes
**Files Modified**: `mcp_server/main.py` (lines 1010-1038)
**Assumption**: Handle stdout closure gracefully when pipe ends
**Implementation**:
```python
# Handle case where stdout is closed
try:
    print("\n🔄 STDIO client disconnected, but WebSocket server continues running...")
except (ValueError, OSError):
    # stdout is closed, redirect to stderr or log file
    import sys
    try:
        sys.stderr.write("\n🔄 STDIO client disconnected, but WebSocket server continues running...\n")
        sys.stderr.flush()
    except:
        # If stderr is also closed, write to log file
        with open("server.log", "a") as f:
            f.write("\n🔄 STDIO client disconnected, but WebSocket server continues running...\n")
```
**Result**: ✅ **SUCCESSFUL** - Server persistence now works without I/O errors
**Testing**: WebSocket connections now succeed after STDIO server ends

### Browser Extension Connection Issues

#### Issue 1: Duplicate Script Loading
**Files Modified**:
- `browser_extension/snap_bridge/bridge.js` (lines 1-6)
- `browser_extension/snap_bridge/websocket_client.js` (lines 1-6)
- `browser_extension/snap_bridge/visual_feedback.js` (lines 1-6)
- `browser_extension/snap_bridge/snap_api_wrapper.js` (lines 1-6)
- `browser_extension/snap_bridge/block_creator.js` (lines 1-6)

**Problem**: Scripts being injected multiple times causing conflicts
**Solution**: Added duplicate loading protection
```javascript
// Prevent duplicate loading
if (typeof window.SnapBridge !== 'undefined') {
    console.log('⚠️ SnapBridge already loaded, skipping...');
} else {
    // Script content here
}
```
**Result**: ✅ **RESOLVED** - No more duplicate loading errors

#### Issue 2: WebSocket Connection State Management
**Files Modified**:
- `browser_extension/snap_bridge/websocket_client.js` (lines 50-60, 293-297)
- `browser_extension/snap_bridge/bridge.js` (lines 167-178)

**Problem**: Multiple connection attempts causing conflicts
**Solution**: Added connection state checks
```javascript
async connect(token) {
    // Prevent duplicate connections
    if (this.isConnected || this.websocket) {
        console.log('⚠️ Already connected or connecting, skipping connection attempt');
        return;
    }
    // Connection logic here
}
```
**Result**: ✅ **RESOLVED** - No more duplicate connection attempts

#### Issue 3: Missing Heartbeat Methods
**Files Modified**:
- `browser_extension/snap_bridge/websocket_client.js` (lines 247-251, 293-297)
- `browser_extension/snap_bridge/bridge.js` (heartbeat methods)

**Problem**: Missing pong handler and heartbeat control methods
**Solution**: Added complete heartbeat implementation
```javascript
// Added pong handler
case 'pong':
    this.handlePong(message);
    break;

// Added heartbeat methods
pauseHeartbeat() {
    if (this.heartbeatInterval) {
        clearInterval(this.heartbeatInterval);
        this.heartbeatInterval = null;
    }
}

resumeHeartbeat() {
    this.startHeartbeat();
}
```
**Result**: ✅ **RESOLVED** - Heartbeat system now complete

### Current Connection Flow Analysis

#### What Works ✅
1. **Server Startup**: RovoDev CLI starts combined STDIO+WebSocket server
2. **Session Creation**: `start_snap_session()` creates session and saves to file
3. **File Sharing**: Sessions accessible across processes via `active_sessions.json`
4. **Server Persistence**: WebSocket server continues after STDIO client disconnects
5. **Browser Extension**: Successfully injects bridge scripts into Snap! pages
6. **WebSocket Connection**: Browser can establish WebSocket connection to server
7. **Token Authentication**: Server accepts and validates display tokens

#### What Fails ❌
1. **Connection Stability**: WebSocket connects but immediately disconnects (code 1011)
2. **Snap! Detection**: Extension cannot detect when Snap! IDE is fully loaded
3. **Session Synchronization**: Connection status not properly updated in session file
4. **Error Recovery**: Poor handling of connection failures and retries

### Current Error Analysis

#### Browser Console Errors
```javascript
// Connection succeeds initially
VM54 websocket_client.js:68 ✅ WebSocket connected

// But immediately disconnects
VM54 websocket_client.js:100 🔌 WebSocket disconnected: 1011

// Reconnection attempts fail
VM54 websocket_client.js:327 🔄 Reconnection attempt 1/5
VM54 websocket_client.js:169 📊 Connection state: {isConnected: false, readyState: 3, OPEN: 1}
VM54 websocket_client.js:179 ⏳ Queueing message for later (readyState: 3)
```

#### Snap! Readiness Detection Issues
```javascript
// Extension cannot detect Snap! components
content_script.js:104   - world: true
content_script.js:105   - SpriteMorph: false  // Should be true
content_script.js:106   - IDE_Morph: false    // Should be true
content_script.js:117 ⚠️ Snap! not fully ready after timeout, proceeding anyway...
```

### Suspected Root Causes

#### 1. WebSocket Disconnect (Code 1011)
**Suspected Files**:
- `mcp_server/tools/snap_communicator.py` (WebSocket server implementation)
- `browser_extension/snap_bridge/websocket_client.js` (client connection handling)

**Suspected Issues**:
- Server may be closing connection due to authentication failure
- Message format mismatch between client and server
- Timing issue with connection establishment

#### 2. Snap! Readiness Detection
**Suspected Files**:
- `browser_extension/content_script.js` (lines 103-120, readiness detection)
- `browser_extension/snap_bridge/snap_api_wrapper.js` (Snap! API access)

**Suspected Issues**:
- Snap! components not fully loaded when extension checks
- Incorrect detection logic for Snap! internal objects
- Timing issue with Snap! initialization

#### 3. Session State Synchronization
**Suspected Files**:
- `mcp_server/main.py` (session management functions)
- `mcp_server/tools/snap_communicator.py` (connection callbacks)

**Suspected Issues**:
- `mark_session_connected()` not being called properly
- File I/O timing issues with session updates
- Connection state not persisting correctly

### Next Steps for Resolution

#### Priority 1: Fix WebSocket Disconnect (Code 1011)
1. **Debug server-side connection handling** in `snap_communicator.py`
2. **Add detailed logging** to WebSocket server connection events
3. **Verify message format compatibility** between client and server
4. **Test connection with minimal message exchange**

#### Priority 2: Improve Snap! Readiness Detection
1. **Research Snap! initialization sequence** and timing
2. **Implement more robust detection logic** with longer timeouts
3. **Add fallback mechanisms** for when detection fails
4. **Test on different Snap! page load scenarios**

#### Priority 3: Fix Session State Synchronization
1. **Add comprehensive logging** to session state changes
2. **Verify file I/O operations** are completing successfully
3. **Test session updates** from both CLI and WebSocket server sides
4. **Implement retry mechanisms** for failed state updates

### Files Requiring Investigation

#### High Priority
- `mcp_server/tools/snap_communicator.py` - WebSocket server connection handling
- `browser_extension/snap_bridge/websocket_client.js` - Client connection management
- `browser_extension/content_script.js` - Snap! readiness detection logic

#### Medium Priority
- `mcp_server/main.py` - Session management and file I/O
- `browser_extension/snap_bridge/bridge.js` - Connection coordination
- `browser_extension/snap_bridge/snap_api_wrapper.js` - Snap! API access

#### Low Priority
- `browser_extension/popup.js` - UI token handling
- `browser_extension/background.js` - Extension lifecycle
- `active_sessions.json` - Session data format and integrity

This comprehensive analysis documents the complete journey from initial connection failures to the current partially-working state, providing a roadmap for final resolution of the remaining issues.