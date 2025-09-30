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
| Feature | Scratch | Snap! | Impact |
|---------|---------|-------|--------|
| **JavaScript API** | ❌ No scripting | ✅ Full DOM access | Direct block creation |
| **Programmatic Control** | ❌ File export only | ✅ Real-time manipulation | Live automation |
| **First-Class Functions** | ❌ Limited | ✅ Full lambda support | Advanced concepts |
| **Custom Blocks** | ❌ Manual only | ✅ Scriptable creation | Dynamic curriculum |
| **XML Manipulation** | ❌ Limited | ✅ Direct DOM access | Precise control |
| **Extension System** | ❌ Restricted | ✅ Open architecture | Easy integration |

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

## Success Metrics

### Technical Metrics
- **Response Time**: <2s from terminal input to block creation
- **Accuracy**: >95% correct block generation for common patterns
- **Reliability**: >99% uptime for bridge connection
- **Coverage**: 100+ Snap! blocks supported

### Educational Metrics
- **Comprehension**: Kids understand generated code 90%+ of time
- **Independence**: Can create programs without adult help
- **Progression**: Advance through curriculum at appropriate pace
- **Engagement**: Return to use system repeatedly

### User Experience Metrics
- **Setup Time**: <5 minutes from install to first block
- **Error Recovery**: Kids can resolve issues without frustration
- **Delight Factor**: "Wow!" moments when blocks appear
- **Learning Transfer**: Skills apply to manual Snap! programming

---

## Risk Mitigation

### Technical Risks
| Risk                  | Impact | Probability | Mitigation                         |
|-----------------------|--------|-------------|------------------------------------|
| Snap! API changes     | High   | Medium      | Version locking, abstraction layer |
| WebSocket instability | Medium | Low         | HTTP fallback, reconnection logic  |
| Browser compatibility | Medium | Medium      | Test on Chrome, Firefox, Safari    |
| Performance issues    | Low    | Low         | Throttling, batch operations       |

### Educational Risks
| Risk                      | Impact | Probability | Mitigation                                       |
|---------------------------|--------|-------------|--------------------------------------------------|
| Too complex for kids      | High   | Medium      | Progressive disclosure, age-appropriate language |
| Bypasses learning         | High   | Medium      | Explanations mandatory, tutorial mode            |
| Incorrect code generation | Medium | Medium      | Validation, preview mode                         |
| Frustration from errors   | Medium | High        | Clear error messages, examples                   |

---

## Competitive Advantages

### vs. Traditional Scratch
- ✅ Real-time block creation (no export/import)
- ✅ Advanced programming concepts
- ✅ Scriptable automation
- ✅ Academic rigor

### vs. Text-Based Programming
- ✅ Visual feedback
- ✅ No syntax errors
- ✅ Immediate gratification
- ✅ Kid-friendly

### vs. Other Block Platforms
- ✅ Natural language interface
- ✅ LLM-powered assistance
- ✅ Personalized learning
- ✅ Terminal-based (appealing to older kids)

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