
### Priority 1: Fixing the WebSocket Disconnect (Code 1011)

a classic symptom of an unhandled exception occurring within the server's `handle_connection` method *after* the TCP connection is established but *before* the main message loop (`async for message in websocket:`) begins.

**Diagnosis:**

Looking at `snap_communicator.py`, the entire connection and handshake logic is wrapped in a single `try...except Exception as e:` block. If any error occurs during the token validation, session lookup, or the `connect_ack` message sending, it will be caught by this generic block, print a generic error, and proceed to the `finally` block, which closes the connection.

**Likely Causes:**
1.  **Error in `token_validator` or `find_session_by_display_token`**: These functions perform file I/O (`load_sessions`) and dictionary lookups. If `active_sessions.json` is ever empty, malformed, or if a token doesn't match, an unexpected `KeyError` or other exception could be thrown that isn't handled gracefully.
2.  **Error in `session_connected_callback`**: The `mark_session_connected` function also performs file I/O. A file permission error, a race condition, or a serialization error when writing the datetime object could crash the handler.
3.  **Circular Import or Timing Issue**: The line `from mcp_server.main import find_session_by_display_token` inside `handle_connection` can sometimes cause subtle issues, though it's unlikely to be the primary culprit here.

**Solution:**

add much more specific logging and error handling to pinpoint the exact line that is failing.

#### Recommended Code Changes for `mcp_server/tools/snap_communicator.py`:
need precise logs about where the process is failing.

```python
# In mcp_server/tools/snap_communicator.py

async def handle_connection(self, websocket: ServerConnection):
    """Handle new WebSocket connection from browser extension"""
    session_id = None
    client_ip = websocket.remote_address

    print(f"🔌 New connection attempt from {client_ip}")

    try:
        # 1. Receive and parse the initial message
        print(f"[{client_ip}] Waiting for 'connect' message...")
        connect_msg = await asyncio.wait_for(websocket.recv(), timeout=10.0)
        connect_data = json.loads(connect_msg)
        print(f"[{client_ip}] Received data: {connect_data}")

        # 2. Validate message type
        if connect_data.get("type") != "connect":
            await websocket.close(1002, "Protocol Error: Expected 'connect' message.")
            print(f"[{client_ip}] ❌ Rejected: Did not send 'connect' message first.")
            return

        # 3. Validate token
        token = connect_data.get("token")
        if not token:
            await websocket.close(1002, "Protocol Error: Missing token.")
            print(f"[{client_ip}] ❌ Rejected: Missing token.")
            return

        print(f"[{client_ip}] Validating token: {token[:8]}...")
        if self.token_validator:
            # Here we assume token_validator finds the session_id
            session_id, error_msg = self.token_validator(token)
            if not session_id:
                await websocket.close(1008, f"Invalid Token: {error_msg}")
                print(f"[{client_ip}] ❌ Rejected: Token validation failed - {error_msg}")
                return
        else:
            # Fallback if no validator is provided (not recommended for production)
            session_id = f"sess_dev_{uuid.uuid4().hex[:8]}"

        print(f"[{client_ip}] ✅ Token validated. Session ID: {session_id}")

        # 4. Store connection and notify server
        self.connections[session_id] = websocket
        self.stats["total_connections"] += 1
        print(f"[{client_ip}] Session '{session_id}' connection stored.")

        if self.session_connected_callback:
            print(f"[{client_ip}] Firing session_connected_callback for '{session_id}'...")
            self.session_connected_callback(session_id)
            print(f"[{client_ip}] ✅ session_connected_callback completed.")

        # 5. Send acknowledgment to the client
        print(f"[{client_ip}] Sending 'connect_ack' to client for session '{session_id}'...")
        await websocket.send(json.dumps({
            "type": "connect_ack",
            "status": "accepted",
            "session_id": session_id,
            # ... other fields from your original code
        }))
        print(f"[{client_ip}] ✅ 'connect_ack' sent. Connection fully established for '{session_id}'.")

        # 6. Begin main message handling loop
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
        print(f"[{client_ip}] 🔌 Connection closed normally (Code: {e.code}, Reason: {e.reason})")
    except Exception as e:
        # This will now catch any unexpected errors with a full traceback
        import traceback
        print(f"[{client_ip}] ❌ UNEXPECTED ERROR in connection handler for session '{session_id}': {e}")
        traceback.print_exc()
        await websocket.close(1011, "Internal Server Error")
        self.stats["errors"] += 1
    finally:
        # Cleanup
        if session_id and session_id in self.connections:
            print(f"[{client_ip}] Cleaning up connection for session '{session_id}'...")
            del self.connections[session_id]
            if self.session_disconnected_callback:
                self.session_disconnected_callback(session_id)
            print(f"[{client_ip}] Cleanup complete for session '{session_id}'.")

```
*Also, you will need to modify `validate_token` in `main.py` to return the session ID instead of a boolean.*

```python
# In mcp_server/main.py

def validate_token(display_token: str) -> tuple[Optional[str], Optional[str]]:
    """Validate token and return (session_id, error_message)"""
    session_id = find_session_by_display_token(display_token)
    
    if not session_id:
        return None, "Session not found for this token."
        
    session = active_sessions[session_id]
    
    # Check expiration
    if datetime.utcnow() > session["expires_at"]:
        return None, "Token has expired."

    # The token is valid, return the full session_id
    return session_id, None
```

### Priority 2: Improve Snap! Readiness Detection
simple `setTimeout` loop is unreliable.

**Diagnosis:** The check `typeof SpriteMorph !== 'undefined'` is failing because the script that defines `SpriteMorph` hasn't been parsed and executed by the browser yet when your check runs.

**Solution:** Implement a more robust detection mechanism using a `MutationObserver`. This will allow your script to wait efficiently and react the moment a key part of the Snap! IDE is added to the page, which is a much more reliable signal of readiness.

#### Recommended Code Changes for `browser_extension/content_script.js`:

```javascript
// In browser_extension/content_script.js

/**
 * Wait for Snap! to be fully loaded using a more robust method.
 */
async waitForSnap() {
    return new Promise((resolve, reject) => {
        // First, do a quick check in case it's already loaded
        if (window.world && window.world.children[0] && window.world.children[0].stage) {
            console.log('✅ Snap! was already ready.');
            resolve();
            return;
        }

        const timeout = setTimeout(() => {
            console.warn('⚠️ Snap! readiness detection timed out after 20 seconds. Proceeding anyway.');
            observer.disconnect(); // Stop observing
            resolve();
        }, 20000); // 20 second timeout

        // The 'stage' canvas is one of the last things to be added.
        // We will watch for it to appear in the DOM.
        const observer = new MutationObserver((mutations, obs) => {
            const stageCanvas = document.querySelector('canvas.world');
            if (stageCanvas && window.IDE_Morph) {
                console.log('✅ Snap! is fully ready (detected via MutationObserver).');
                clearTimeout(timeout); // Clear the timeout
                obs.disconnect(); // Stop observing
                resolve();
            }
        });

        console.log('⏳ Waiting for Snap! to load (using MutationObserver)...');
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    });
}
```

This version uses a `MutationObserver` to watch for changes to the web page's body and its descendants. It specifically looks for the Snap! stage canvas (`canvas.world`). When it finds it, it knows the IDE is ready, disconnects the observer, and resolves the promise. This is far more reliable and efficient than polling with `setTimeout`.

### Priority 3: Session State Synchronization
likely a side effect of the WebSocket server errors. When the connection handler crashes, the `mark_session_connected` callback is never reliably called.

By fixing the WebSocket disconnection issue with the improved logging and error handling above, you will ensure that `mark_session_connected` is called correctly upon a successful handshake. The file-based session sharing you've implemented is a solid pattern for this architecture. The key is to ensure the read/write operations are atomic and happen only when the state genuinely changes.

### Summary of Action Plan

1.  **Update `mcp_server/tools/snap_communicator.py`**: Replace the `handle_connection` method with the enhanced version provided above.
2.  **Update `mcp_server/main.py`**: Modify the `validate_token` function to return the `session_id` on success.
3.  **Update `browser_extension/content_script.js`**: Replace the `waitForSnap` method with the more robust `MutationObserver`-based version.
4.  **Restart and Test**: Restart your MCP server. The new server logs should give you a precise, line-by-line trace of the connection handshake, immediately revealing where the process fails if it still does.

By implementing these changes, you will move from a situation where you have a silent failure to one where you have explicit, detailed error reporting, which will lead you directly to the solution.