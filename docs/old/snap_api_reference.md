# Snap! API Reference

This document provides a comprehensive reference for the Snap! Educational MCP System APIs.

## Table of Contents

1. [MCP Tools](#mcp-tools)
2. [WebSocket Protocol](#websocket-protocol)
3. [JavaScript Bridge API](#javascript-bridge-api)
4. [Block Generation](#block-generation)
5. [Error Handling](#error-handling)

## MCP Tools

The MCP server provides several tools for interacting with Snap! programmatically.

### start_snap_session

Initiates a new Snap! session with secure token-based authentication.

**Parameters:**
- `user_id` (string): Unique identifier for the user
- `session_config` (object): Configuration options for the session

**Returns:**
```json
{
  "session_id": "sess_abc123",
  "connection_token": "tok_xyz789",
  "websocket_url": "ws://localhost:8765",
  "expires_at": "2024-01-01T12:00:00Z"
}
```

**Example:**
```python
result = await start_snap_session(
    user_id="student_123",
    session_config={
        "difficulty_level": "beginner",
        "enable_tutorials": True,
        "visual_feedback": True
    }
)
```

### generate_snap_blocks

Generates Snap! blocks from natural language descriptions.

**Parameters:**
- `user_request` (string): Natural language description of desired functionality
- `target_sprite` (string, optional): Name of target sprite (default: current sprite)
- `difficulty_level` (string): "beginner", "intermediate", or "advanced"
- `include_explanation` (boolean): Whether to include educational explanations

**Returns:**
```json
{
  "blocks_created": 5,
  "scripts_created": 1,
  "explanation": "Created a jumping game script...",
  "execution_time_ms": 150,
  "created_block_ids": ["block_1", "block_2"],
  "sprite_info": {
    "name": "Sprite1",
    "position": {"x": 0, "y": 0},
    "total_scripts": 3
  }
}
```

**Example:**
```python
result = await generate_snap_blocks(
    description="when space key pressed, move sprite up 50 pixels and wait 0.3 seconds and move sprite down 50 pixels",
    complexity="beginner",
    execution_mode="execute"
)
```

**Note:** The system uses a lightweight parser that expects structured descriptions from Claude/LLM rather than raw user input. This enables fast processing without heavy NLP dependencies.

### explain_snap_concept

Provides educational explanations for programming concepts.

**Parameters:**
- `concept` (string): The concept to explain (e.g., "loops", "variables", "events")
- `difficulty_level` (string): Target difficulty level
- `include_examples` (boolean): Whether to include code examples

**Returns:**
```json
{
  "concept": "loops",
  "explanation": "Loops are like doing the same thing over and over...",
  "key_points": ["Loops save time", "Use repeat blocks"],
  "examples": ["repeat 10 times: move 10 steps"],
  "try_commands": ["make sprite move in a square using loops"],
  "related_concepts": ["repeat blocks", "forever blocks"]
}
```

### create_snap_tutorial

Creates step-by-step tutorials for specific projects.

**Parameters:**
- `tutorial_topic` (string): Topic for the tutorial
- `difficulty_level` (string): Target difficulty level
- `estimated_time` (number): Estimated completion time in minutes

**Returns:**
```json
{
  "tutorial": {
    "title": "Build a Jumping Game",
    "description": "Create a simple game where a sprite jumps...",
    "difficulty": "beginner",
    "estimated_time": 15,
    "steps": [
      {
        "step": 1,
        "title": "Set up your sprite",
        "instructions": ["Look at the sprite area"],
        "success_criteria": "You can see a sprite"
      }
    ]
  }
}
```

### inspect_snap_project

Reads and analyzes the current Snap! project state.

**Parameters:**
- `include` (object): What information to include
  - `sprites` (boolean): Include sprite information
  - `stage` (boolean): Include stage information
  - `variables` (boolean): Include variable information
  - `custom_blocks` (boolean): Include custom block definitions
- `detail_level` (string): "summary", "detailed", or "full"

**Returns:**
```json
{
  "project": {
    "name": "My Project",
    "sprites": [
      {
        "name": "Sprite1",
        "costume_count": 2,
        "script_count": 3,
        "position": {"x": 0, "y": 0}
      }
    ],
    "stage": {
      "costume_count": 1,
      "script_count": 0
    },
    "global_variables": [
      {"name": "score", "value": 0}
    ]
  }
}
```

## WebSocket Protocol

The WebSocket protocol enables real-time communication between the MCP server and the browser extension.

### Connection Flow

1. **Client connects** to `ws://localhost:8765`
2. **Client sends connection request** with authentication token
3. **Server validates token** and responds with acknowledgment
4. **Bidirectional communication** begins

### Message Format

All messages follow this JSON structure:

```json
{
  "type": "message_type",
  "message_id": "unique_id",
  "timestamp": "2024-01-01T12:00:00Z",
  "payload": {}
}
```

### Message Types

#### Connection Messages

**connect**
```json
{
  "type": "connect",
  "version": "1.0.0",
  "token": "authentication_token",
  "client_info": {
    "extension_version": "0.1.0",
    "browser": "Chrome/120.0.0.0",
    "snap_version": "8.2.0"
  }
}
```

**connect_ack**
```json
{
  "type": "connect_ack",
  "status": "accepted",
  "session_id": "sess_abc123",
  "server_info": {
    "version": "1.0.0",
    "capabilities": ["block_creation", "project_inspection"]
  }
}
```

#### Command Messages

**command**
```json
{
  "type": "command",
  "message_id": "cmd_123",
  "command": "create_blocks",
  "payload": {
    "target_sprite": "Sprite1",
    "scripts": [
      {
        "script_id": "script_1",
        "position": {"x": 50, "y": 50},
        "blocks": [
          {
            "opcode": "event_whenflagclicked",
            "category": "events",
            "is_hat_block": true
          }
        ]
      }
    ]
  }
}
```

**response**
```json
{
  "type": "response",
  "message_id": "cmd_123",
  "status": "success",
  "timestamp": "2024-01-01T12:00:00Z",
  "payload": {
    "blocks_created": 3,
    "execution_time_ms": 120
  }
}
```

## JavaScript Bridge API

The JavaScript bridge provides the interface between the WebSocket client and Snap!'s internal APIs.

### SnapBridge Class

Main bridge class that coordinates all communication.

```javascript
const bridge = new SnapBridge();
await bridge.connect(token);
```

#### Methods

**connect(token)**
- Establishes WebSocket connection with authentication token
- Returns: Promise that resolves when connected

**sendCommand(command, payload)**
- Sends a command to the MCP server
- Returns: Promise with command result

**disconnect()**
- Closes WebSocket connection and cleans up resources

### SnapBlockCreator Class

Handles creation and manipulation of Snap! blocks.

```javascript
const creator = new SnapBlockCreator();
const result = await creator.createBlocks(payload);
```

#### Methods

**createBlocks(payload)**
- Creates blocks from specification
- Parameters: Block creation payload
- Returns: Creation result with statistics

**deleteBlocks(payload)**
- Deletes specified blocks
- Parameters: Deletion specification
- Returns: Deletion result

**createCustomBlock(payload)**
- Creates custom block definition
- Parameters: Custom block specification
- Returns: Creation result

### SnapAPIWrapper Class

Provides high-level wrapper for Snap! internal APIs.

```javascript
const wrapper = new SnapAPIWrapper();
const project = await wrapper.readProject(options);
```

#### Methods

**readProject(options)**
- Reads current project state
- Parameters: Options for what to include
- Returns: Project information object

**executeScript(payload)**
- Executes JavaScript code in Snap! context
- Parameters: Script execution options
- Returns: Execution result

**inspectState(query)**
- Inspects specific aspects of project state
- Parameters: Query specification
- Returns: Query results

## Block Generation

### Block Specification Format

Blocks are specified using this JSON format:

```json
{
  "opcode": "forward",
  "category": "motion",
  "inputs": {
    "STEPS": 10
  },
  "description": "Move sprite forward",
  "position": {"x": 50, "y": 50},
  "next_block": "block_id_2",
  "is_hat_block": false
}
```

### Supported Block Categories

- **motion**: Movement and rotation blocks
- **looks**: Appearance and visual effects
- **sound**: Audio playback and recording
- **events**: Event triggers and broadcasting
- **control**: Loops, conditionals, and flow control
- **sensing**: Input detection and collision
- **operators**: Mathematical and logical operations
- **variables**: Data storage and manipulation

### Block Input Types

- **number**: Numeric values
- **string**: Text values
- **boolean**: True/false values
- **color**: Color values (hex or name)
- **dropdown**: Predefined options
- **block**: Nested block inputs

## Error Handling

### Error Response Format

```json
{
  "type": "response",
  "message_id": "cmd_123",
  "status": "error",
  "error": {
    "code": "BLOCK_CREATION_FAILED",
    "message": "Unable to create block with opcode 'invalid_block'",
    "details": {
      "opcode": "invalid_block",
      "reason": "Unknown block type"
    }
  }
}
```

### Common Error Codes

- **INVALID_TOKEN**: Authentication token is invalid or expired
- **BLOCK_CREATION_FAILED**: Block creation encountered an error
- **SPRITE_NOT_FOUND**: Target sprite does not exist
- **INVALID_PARAMETERS**: Command parameters are invalid
- **SNAP_NOT_READY**: Snap! environment is not fully loaded
- **WEBSOCKET_ERROR**: WebSocket communication error
- **TIMEOUT**: Operation timed out
- **PERMISSION_DENIED**: Operation not allowed in current context

### Error Recovery

1. **Retry Logic**: Implement exponential backoff for transient errors
2. **Fallback Options**: Provide alternative approaches when primary method fails
3. **User Feedback**: Show clear, kid-friendly error messages
4. **Logging**: Log errors for debugging while protecting user privacy

### Best Practices

1. **Always validate inputs** before sending commands
2. **Handle async operations** with proper error catching
3. **Provide user feedback** for long-running operations
4. **Implement timeouts** for all network operations
5. **Test error scenarios** thoroughly in development
