# mcp_server/tools/snap_communicator.py - WebSocket Bridge Communication

import asyncio
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import websockets
from websockets import ServerConnection

# NEW: Import the Jinja2 library
from jinja2 import Environment, FileSystemLoader


# NEW: Helper function for XML generation.
# This is kept outside the class to separate concerns: this function's job is
# template rendering, while the class's job is communication.
def create_project_xml(problem_data: Dict[str, Any]) -> str:
    """
    Generates a complete Snap! project XML string from a Jinja2 template.

    Args:
        problem_data (dict): A dictionary containing the data for the template.

    Returns:
        str: The fully rendered XML string.
    """
    # Set up the Jinja2 environment to load templates from the 'templates' folder.
    # The path is relative to where the script is run.
    env = Environment(loader=FileSystemLoader('mcp_server/tools/templates/'))

    # Load the template file
    template = env.get_template('project_template.xml')

    # Render the template with the provided data
    xml_string = template.render(problem_data)

    return xml_string


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
    self.token_validator = token_validator
    self.session_connected_callback = session_connected_callback
    self.session_disconnected_callback = session_disconnected_callback
    self.connections: Dict[str, ServerConnection] = {}
    self.pending_responses: Dict[str, asyncio.Future] = {}
    self.stats = {
        "total_connections": 0,
        "total_messages": 0,
        "total_commands": 0,
        "errors": 0
    }

  async def start_server(self):
    """Start WebSocket server"""
    # ... (rest of the __init__ and start_server methods are unchanged) ...
    self.server = await websockets.serve(
        self.handle_connection,
        self.host,
        self.port,
        ping_interval=20,
        ping_timeout=10,
        close_timeout=10,
        max_size=2**20,
        max_queue=32,
        compression=None
    )
    print(f"📡 WebSocket server started on ws://{self.host}:{self.port}")

  async def handle_connection(self, websocket: ServerConnection):
    # ... (This entire method remains unchanged) ...
    session_id = None
    client_ip = websocket.remote_address
    print(f"🔌 New connection attempt from {client_ip}")
    try:
      print(f"[{client_ip}] Waiting for 'connect' message...")
      connect_msg = await asyncio.wait_for(websocket.recv(), timeout=10.0)
      connect_data = json.loads(connect_msg)
      print(f"[{client_ip}] Received data: {connect_data}")
      if connect_data.get("type") != "connect":
        await websocket.close(1002, "Protocol Error: Expected 'connect' message.")
        print(f"[{client_ip}] ❌ Rejected: Did not send 'connect' message first.")
        return
      token = connect_data.get("token")
      if not token:
        await websocket.close(1002, "Protocol Error: Missing token.")
        print(f"[{client_ip}] ❌ Rejected: Missing token.")
        return
      print(f"[{client_ip}] Validating token: {token[:8]}...")
      if self.token_validator:
        session_id, error_msg = self.token_validator(token)
        if not session_id:
          await websocket.close(1008, f"Invalid Token: {error_msg}")
          print(f"[{client_ip}] ❌ Rejected: Token validation failed - {error_msg}")
          return
      else:
        import uuid
        session_id = f"sess_dev_{uuid.uuid4().hex[:8]}"
      print(f"[{client_ip}] ✅ Token validated. Session ID: {session_id}")
      self.connections[session_id] = websocket
      self.stats["total_connections"] += 1
      print(f"[{client_ip}] Session '{session_id}' connection stored.")
      if self.session_connected_callback:
        print(
            f"[{client_ip}] Firing session_connected_callback for '{session_id}'...")
        self.session_connected_callback(session_id)
        print(f"[{client_ip}] ✅ session_connected_callback completed.")
      print(
          f"[{client_ip}] Sending 'connect_ack' to client for session '{session_id}'...")
      await websocket.send(json.dumps({
          "type": "connect_ack",
          "status": "accepted",
          "session_id": session_id,
          "server_capabilities": {
              "max_message_size": 1048576,
              "supported_commands": [
                  "load_project",  # NEW: Add our new command here
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
      print(
          f"[{client_ip}] ✅ 'connect_ack' sent. Connection fully established for '{session_id}'.")
      async for message in websocket:
        if isinstance(message, bytes):
          message_str = message.decode('utf-8')
        else:
          message_str = str(message)
        await self.handle_message(session_id, message_str)
    except json.JSONDecodeError:
      print(f"[{client_ip}] ❌ Connection closed: Invalid JSON.")
      await websocket.close(1002, "Protocol Error: Invalid JSON")
    except asyncio.TimeoutError:
      print(f"[{client_ip}] ❌ Connection closed: Timeout waiting for connect message.")
      await websocket.close(1008, "Timeout")
    except websockets.exceptions.ConnectionClosed as e:
      print(
          f"[{client_ip}] 🔌 Connection closed normally (Code: {e.code}, Reason: {e.reason})")
    except Exception as e:
      import traceback
      print(f"[{client_ip}] ❌ UNEXPECTED ERROR in connection handler for session '{session_id}': {e}")
      traceback.print_exc()
      await websocket.close(1011, "Internal Server Error")
      self.stats["errors"] += 1
    finally:
      if session_id and session_id in self.connections:
        print(f"[{client_ip}] Cleaning up connection for session '{session_id}'...")
        del self.connections[session_id]
        if self.session_disconnected_callback:
          self.session_disconnected_callback(session_id)
        print(f"[{client_ip}] Cleanup complete for session '{session_id}'.")

  async def handle_message(self, session_id: str, message: str):
    # ... (This entire method remains unchanged) ...
    try:
      data = json.loads(message)
      self.stats["total_messages"] += 1
      message_type = data.get("type")
      message_id = data.get("message_id")
      if message_type == "response":
        if message_id in self.pending_responses:
          future = self.pending_responses[message_id]
          future.set_result(data)
          del self.pending_responses[message_id]
      elif message_type == "event":
        await self.handle_event(session_id, data)
      elif message_type == "ping":
        websocket = self.connections.get(session_id)
        if websocket:
          await websocket.send(json.dumps({
              "type": "pong",
              "timestamp": datetime.utcnow().isoformat(),
              "latency_ms": 0
          }))
    except json.JSONDecodeError:
      print(f"✗ Invalid JSON from {session_id}")
      self.stats["errors"] += 1
    except Exception as e:
      print(f"✗ Error handling message: {e}")
      self.stats["errors"] += 1

  async def handle_event(self, session_id: str, event_data: Dict[str, Any]):
    # ... (This entire method remains unchanged) ...
    event_type = event_data.get("event_type")
    print(f"📢 Event from {session_id}: {event_type}")

  def is_connected(self, session_id: str) -> bool:
    # ... (This entire method remains unchanged) ...
    return session_id in self.connections

  async def check_snap_ready(self, session_id: str) -> bool:
    # ... (This entire method remains unchanged) ...
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
    # ... (This entire method remains unchanged) ...
    if session_id not in self.connections:
      raise ConnectionError(f"Session {session_id} not connected")
    websocket = self.connections[session_id]
    message_id = f"msg_{uuid.uuid4().hex[:12]}"
    future = asyncio.Future()
    self.pending_responses[message_id] = future
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
    try:
      response = await asyncio.wait_for(future, timeout=timeout)
      return response
    except asyncio.TimeoutError:
      if message_id in self.pending_responses:
        del self.pending_responses[message_id]
      raise TimeoutError(f"Command {command} timed out")

  # ========================================================================
  # High-level command methods
  # ========================================================================

  # NEW: Add the high-level method for our new XML workflow
  async def load_project_from_xml(
      self,
      session_id: str,
      xml_string: str,
      project_name: str = "Generated Project"
  ) -> Dict[str, Any]:
    """
    Loads a complete project into Snap! using a full XML string.
    This is the new, preferred method for setting up complex scenes.
    """
    payload = {
        'xml': xml_string,
        'project_name': project_name
    }

    # This command name must match the one handled by the JavaScript side.
    response = await self.send_command(session_id, "load_project", payload)
    return response.get("payload", {})

  async def create_blocks(
      self,
      session_id: str,
      snap_spec: Dict[str, Any],
      animate: bool = True
  ) -> Dict[str, Any]:
    """Create blocks in Snap! IDE"""
    # ... (This method remains unchanged, but will be used less often) ...
    if "payload" not in snap_spec:
        raise ValueError(
            "Invalid snap_spec: dictionary is missing the 'payload' key.")
    payload_to_send = snap_spec["payload"]
    if "visual_feedback" in payload_to_send:
        payload_to_send["visual_feedback"]["animate_creation"] = animate
    response = await self.send_command(session_id, "create_blocks", payload_to_send)
    return response.get("payload", {})

  # ... (All other high-level command methods like read_project, etc., remain unchanged) ...
  async def read_project(self, session_id: str, detail_level: str = "summary") -> Dict[str, Any]:
    payload = {"include": {"sprites": True, "scripts": True, "variables": True,
                           "custom_blocks": True, "stage": True}, "detail_level": detail_level}
    response = await self.send_command(session_id, "read_project", payload)
    return response.get("payload", {}).get("project", {})

  async def execute_javascript(self, session_id: str, code: str, sandbox: bool = True) -> Dict[str, Any]:
    payload = {"javascript_code": code,
               "return_result": True, "sandbox_mode": sandbox}
    response = await self.send_command(session_id, "execute_script", payload)
    return response.get("payload", {})

  async def inspect_state(self, session_id: str, query: Dict[str, Any]) -> Dict[str, Any]:
    payload = {"query": query}
    response = await self.send_command(session_id, "inspect_state", payload)
    return response.get("payload", {})

  async def delete_blocks(self, session_id: str, target_sprite: str, selection: Dict[str, Any]) -> Dict[str, Any]:
    payload = {"target_sprite": target_sprite, "selection": selection, "options": {
        "confirm_before_delete": False, "create_undo_snapshot": True}}
    response = await self.send_command(session_id, "delete_blocks", payload)
    return response.get("payload", {})

  async def create_custom_block(self, session_id: str, block_spec: Dict[str, Any]) -> Dict[str, Any]:
    response = await self.send_command(session_id, "create_custom_block", block_spec)
    return response.get("payload", {})

  async def highlight_blocks(self, session_id: str, block_ids: List[str], duration_ms: int = 2000, tooltip: Optional[str] = None) -> Dict[str, Any]:
    payload = {"block_ids": block_ids, "highlight_style": {
        "color": "#FFD700", "duration_ms": duration_ms, "pulse": True}}
    if tooltip:
      payload["show_tooltip"] = {"text": tooltip, "position": "above"}
    response = await self.send_command(session_id, "highlight_blocks", payload)
    return response.get("payload", {})

  async def export_project(self, session_id: str, format: str = "xml", include_media: bool = False) -> Dict[str, Any]:
    payload = {"format": format,
               "include_media": include_media, "compress": False}
    response = await self.send_command(session_id, "export_project", payload)
    return response.get("payload", {})

  def get_stats(self) -> Dict[str, Any]:
    """Get communication statistics"""
    return {
        **self.stats,
        "active_connections": len(self.connections),
        "pending_responses": len(self.pending_responses)
    }

# mcp_server/tools/snap_communicator.py - WebSocket Bridge Communication
# ... (all the code from before remains the same, down to the get_stats method) ...

# ============================================================================
# Main Server Execution Block
# ============================================================================


async def main():
    """
    Main function to initialize and run the WebSocket server indefinitely.
    """
    # In a real application, you would pass a real token_validator
    # and session callback functions. For this POC, we'll use a simple one.
    def simple_token_validator(token):
        if token:
            return f"sess_{token}", None
        return None, "No token provided."

    communicator = SnapBridgeCommunicator(
        token_validator=simple_token_validator
    )

    await communicator.start_server()

    # This will keep the server running forever until you stop it with Ctrl+C
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        print("--- Starting Snap! Bridge WebSocket Server ---")
        print("--- Press Ctrl+C to stop the server ---")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n--- Server shut down by user. ---")
