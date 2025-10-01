# mcp_server/tools/snap_communicator.py - WebSocket Bridge Communication

import asyncio
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import websockets
from websockets import ServerConnection


class SnapBridgeCommunicator:
  """
  Manages WebSocket communication with Snap! browser extension.
  Handles message routing, connection management, and response handling.
  """

  def __init__(self, host: str = "localhost", port: int = 8765, token_validator=None,
               session_connected_callback=None, session_disconnected_callback=None):
    self.host = host
    self.port = port
    self.server = None
    self.token_validator = token_validator  # Function to validate tokens
    self.session_connected_callback = session_connected_callback  # Called when session connects
    self.session_disconnected_callback = session_disconnected_callback  # Called when session disconnects

    # Connection management
    # session_id -> websocket connection
    self.connections: Dict[str, ServerConnection] = {}
    # message_id -> future
    self.pending_responses: Dict[str, asyncio.Future] = {}

    # Statistics
    self.stats = {
      "total_connections": 0,
      "total_messages": 0,
      "total_commands": 0,
      "errors": 0
    }

  async def start_server(self):
    """Start WebSocket server"""
    self.server = await websockets.serve(
      self.handle_connection,
      self.host,
      self.port,
      ping_interval=20,
      ping_timeout=10,
      close_timeout=10,
      max_size=2**20,  # 1MB max message size
      max_queue=32,    # Max queued messages
      compression=None  # Disable compression for debugging
    )
    print(f"📡 WebSocket server started on ws://{self.host}:{self.port}")

  async def handle_connection(self, websocket: ServerConnection):
    """Handle new WebSocket connection from browser extension"""
    session_id = None

    try:
      # Wait for connection message with token
      print(f"🔍 Waiting for connection message from client...")
      connect_msg = await asyncio.wait_for(
        websocket.recv(),
        timeout=10.0
      )

      print(f"📨 Received message: {connect_msg}")
      connect_data = json.loads(connect_msg)
      print(f"📋 Parsed data: {connect_data}")

      if connect_data.get("type") != "connect":
        await websocket.send(json.dumps({
          "type": "connect_error",
          "status": "rejected",
          "error": {
            "code": "INVALID_MESSAGE",
            "message": "Expected connection message"
          }
        }))
        return

      # Validate token using the provided validator function
      token = connect_data.get("token")
      if not token:
        await websocket.send(json.dumps({
          "type": "connect_error",
          "status": "rejected",
          "error": {
            "code": "MISSING_TOKEN",
            "message": "Connection token required"
          }
        }))
        return

      # Validate token
      if self.token_validator:
        is_valid, error_msg = self.token_validator(token)
        if not is_valid:
          await websocket.send(json.dumps({
            "type": "connect_error",
            "status": "rejected",
            "error": {
              "code": "INVALID_TOKEN",
              "message": error_msg or "Token validation failed"
            }
          }))
          return

      # Extract session ID from token data
      session_id = connect_data.get("session_id")
      if not session_id:
        # Try to find session by display token
        from mcp_server.main import find_session_by_display_token
        session_id = find_session_by_display_token(token)

        if not session_id:
          # If still no session found, create a new one (fallback)
          session_id = f"sess_{uuid.uuid4().hex[:12]}"
          print(f"⚠️ No session found for token {token[:8]}, created new session: {session_id}")

      # Store connection
      self.connections[session_id] = websocket
      self.stats["total_connections"] += 1

      # Notify main server that session is connected
      if self.session_connected_callback:
        self.session_connected_callback(session_id)

      # Send acknowledgment
      await websocket.send(json.dumps({
        "type": "connect_ack",
        "status": "accepted",
        "session_id": session_id,
        "server_capabilities": {
          "max_message_size": 1048576,
          "supported_commands": [
            "create_blocks",
            "read_project",
            "execute_script",
            "inspect_state",
            "delete_blocks",
            "create_custom_block",
            "highlight_blocks",
            "export_project"
          ],
          "protocol_version": "1.0.0"
        },
        "keep_alive_interval": 30000
      }))

      print(f"✓ Browser connected: {session_id}")

      # Handle messages
      async for message in websocket:
        # Convert bytes to string if needed
        if isinstance(message, bytes):
          message_str = message.decode('utf-8')
        else:
          message_str = str(message)
        await self.handle_message(session_id, message_str)

    except asyncio.TimeoutError:
      print("⚠ Connection timeout")
    except websockets.exceptions.ConnectionClosed:
      print(f"✓ Connection closed: {session_id}")
    except Exception as e:
      print(f"✗ Connection error: {e}")
      self.stats["errors"] += 1
    finally:
      # Cleanup
      if session_id and session_id in self.connections:
        del self.connections[session_id]

        # Notify main server that session is disconnected
        if self.session_disconnected_callback:
          self.session_disconnected_callback(session_id)

  async def handle_message(self, session_id: str, message: str):
    """Handle incoming message from browser extension"""
    try:
      data = json.loads(message)
      self.stats["total_messages"] += 1

      message_type = data.get("type")
      message_id = data.get("message_id")

      if message_type == "response":
        # This is a response to a command we sent
        if message_id in self.pending_responses:
          future = self.pending_responses[message_id]
          future.set_result(data)
          del self.pending_responses[message_id]

      elif message_type == "event":
        # Unsolicited event from browser
        await self.handle_event(session_id, data)

      elif message_type == "ping":
        # Heartbeat - respond with pong
        websocket = self.connections.get(session_id)
        if websocket:
          await websocket.send(json.dumps({
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat(),
            "latency_ms": 0  # Calculate if needed
          }))

    except json.JSONDecodeError:
      print(f"✗ Invalid JSON from {session_id}")
      self.stats["errors"] += 1
    except Exception as e:
      print(f"✗ Error handling message: {e}")
      self.stats["errors"] += 1

  async def handle_event(self, session_id: str, event_data: Dict[str, Any]):
    """Handle unsolicited events from browser (e.g., user actions)"""
    event_type = event_data.get("event_type")
    print(f"📢 Event from {session_id}: {event_type}")

    # Could store events, trigger callbacks, etc.
    # For now, just log

  def is_connected(self, session_id: str) -> bool:
    """Check if session is connected"""
    return session_id in self.connections

  async def check_snap_ready(self, session_id: str) -> bool:
    """Check if Snap! IDE is loaded and ready"""
    try:
      result = await self.send_command(
        session_id,
        "inspect_state",
        {"query": {"type": "snap_ready"}}
      )
      return result.get("status") == "success"
    except:
      return False

  async def send_command(
    self,
    session_id: str,
    command: str,
    payload: Dict[str, Any],
    timeout: float = 5.0
  ) -> Dict[str, Any]:
    """
    Send command to browser extension and wait for response.
    
    Args:
      session_id: Target session
      command: Command name
      payload: Command payload
      timeout: Response timeout in seconds
    
    Returns:
      Response from browser extension
    """
    if session_id not in self.connections:
      raise ConnectionError(f"Session {session_id} not connected")

    websocket = self.connections[session_id]
    message_id = f"msg_{uuid.uuid4().hex[:12]}"

    # Create future for response
    future = asyncio.Future()
    self.pending_responses[message_id] = future

    # Send command
    command_message = {
      "message_id": message_id,
      "type": "command",
      "timestamp": datetime.utcnow().isoformat(),
      "session_id": session_id,
      "command": command,
      "payload": payload,
      "options": {
        "timeout_ms": int(timeout * 1000),
        "retry_on_failure": False,
        "require_confirmation": False
      }
    }

    await websocket.send(json.dumps(command_message))
    self.stats["total_commands"] += 1

    # Wait for response
    try:
      response = await asyncio.wait_for(future, timeout=timeout)
      return response
    except asyncio.TimeoutError:
      # Cleanup
      if message_id in self.pending_responses:
        del self.pending_responses[message_id]
      raise TimeoutError(f"Command {command} timed out")

  # ========================================================================
  # High-level command methods
  # ========================================================================

  async def create_blocks(
    self,
    session_id: str,
    snap_spec: Dict[str, Any],
    animate: bool = True
  ) -> Dict[str, Any]:
    """Create blocks in Snap! IDE"""
    payload = {
      **snap_spec,
      "visual_feedback": {
        "animate_creation": animate,
        "highlight_duration_ms": 2000,
        "show_explanation": True
      }
    }

    response = await self.send_command(session_id, "create_blocks", payload)
    return response.get("payload", {})

  async def read_project(
    self,
    session_id: str,
    detail_level: str = "summary"
  ) -> Dict[str, Any]:
    """Read current Snap! project state"""
    payload = {
      "include": {
        "sprites": True,
        "scripts": True,
        "variables": True,
        "custom_blocks": True,
        "stage": True
      },
      "detail_level": detail_level
    }

    response = await self.send_command(session_id, "read_project", payload)
    return response.get("payload", {}).get("project", {})

  async def execute_javascript(
    self,
    session_id: str,
    code: str,
    sandbox: bool = True
  ) -> Dict[str, Any]:
    """Execute JavaScript code in Snap! context"""
    payload = {
      "javascript_code": code,
      "return_result": True,
      "sandbox_mode": sandbox
    }

    response = await self.send_command(session_id, "execute_script", payload)
    return response.get("payload", {})

  async def inspect_state(
    self,
    session_id: str,
    query: Dict[str, Any]
  ) -> Dict[str, Any]:
    """Inspect specific Snap! IDE state"""
    payload = {"query": query}

    response = await self.send_command(session_id, "inspect_state", payload)
    return response.get("payload", {})

  async def delete_blocks(
    self,
    session_id: str,
    target_sprite: str,
    selection: Dict[str, Any]
  ) -> Dict[str, Any]:
    """Delete blocks or scripts"""
    payload = {
      "target_sprite": target_sprite,
      "selection": selection,
      "options": {
        "confirm_before_delete": False,
        "create_undo_snapshot": True
      }
    }

    response = await self.send_command(session_id, "delete_blocks", payload)
    return response.get("payload", {})

  async def create_custom_block(
    self,
    session_id: str,
    block_spec: Dict[str, Any]
  ) -> Dict[str, Any]:
    """Create custom Snap! block"""
    response = await self.send_command(session_id, "create_custom_block", block_spec)
    return response.get("payload", {})

  async def highlight_blocks(
    self,
    session_id: str,
    block_ids: List[str],
    duration_ms: int = 2000,
    tooltip: Optional[str] = None
  ) -> Dict[str, Any]:
    """Highlight specific blocks for visual feedback"""
    payload = {
      "block_ids": block_ids,
      "highlight_style": {
        "color": "#FFD700",
        "duration_ms": duration_ms,
        "pulse": True
      }
    }

    if tooltip:
      payload["show_tooltip"] = {
        "text": tooltip,
        "position": "above"
      }

    response = await self.send_command(session_id, "highlight_blocks", payload)
    return response.get("payload", {})

  async def export_project(
    self,
    session_id: str,
    format: str = "xml",
    include_media: bool = False
  ) -> Dict[str, Any]:
    """Export current Snap! project"""
    payload = {
      "format": format,
      "include_media": include_media,
      "compress": False
    }

    response = await self.send_command(session_id, "export_project", payload)
    return response.get("payload", {})

  def get_stats(self) -> Dict[str, Any]:
    """Get communication statistics"""
    return {
      **self.stats,
      "active_connections": len(self.connections),
      "pending_responses": len(self.pending_responses)
    }


# ============================================================================
# Example Usage
# ============================================================================

async def example_usage():
  """Example of how to use the communicator"""

  # Initialize communicator
  communicator = SnapBridgeCommunicator()

  # Start server
  await communicator.start_server()

  # Wait for connection (in real usage, this happens automatically)
  print("Waiting for browser connection...")
  await asyncio.sleep(5)

  # Assume session_id from connection
  session_id = "sess_example123"

  if communicator.is_connected(session_id):
    # Create blocks
    snap_spec = {
      "target_sprite": "Sprite",
      "scripts": [
        {
          "script_id": "script_001",
          "position": {"x": 50, "y": 50},
          "blocks": [
            {
              "block_id": "block_001",
              "opcode": "receiveKey",
              "category": "events",
              "inputs": {"KEY": "space"},
              "is_hat_block": True,
              "next": "block_002"
            },
            {
              "block_id": "block_002",
              "opcode": "changeYBy",
              "category": "motion",
              "inputs": {"DY": 50},
              "next": None
            }
          ]
        }
      ]
    }

    result = await communicator.create_blocks(session_id, snap_spec)
    print(f"Created {result.get('blocks_created')} blocks!")

    # Read project state
    project = await communicator.read_project(session_id)
    print(f"Project has {len(project.get('sprites', []))} sprites")

    # Get stats
    stats = communicator.get_stats()
    print(f"Total commands: {stats['total_commands']}")


if __name__ == "__main__":
  asyncio.run(example_usage())
