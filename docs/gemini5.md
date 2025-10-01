# Gemini Fix 5 Implementation - Correcting the Payload Structure

The new error, `TypeError: scripts is not iterable`, is a much simpler problem. It's a data structure mismatch between what the server is sending and what the browser extension expects to receive.

### Root Cause Analysis

Let's look at the clues:

1.  **Error:** `TypeError: scripts is not iterable` at `block_creator.js:84`. This means your JavaScript code is trying to loop over a variable named `scripts` that isn't an array (it's likely `undefined`).
2.  **Code Flow:** The error happens inside `SnapBlockCreator.createBlocks(payload)`. The `payload` argument is what comes directly from your Python server.
3.  **The Culprit:** The issue is in `mcp_server/tools/snap_communicator.py`. The `create_blocks` method incorrectly wraps the data, creating a "payload inside a payload."

Here's the faulty logic in your Python file:

**File:** `mcp_server/tools/snap_communicator.py`

```python
# The current, incorrect code
async def create_blocks(
  self,
  session_id: str,
  snap_spec: Dict[str, Any], #<-- snap_spec is {"command": "...", "payload": {...}}
  animate: bool = True
) -> Dict[str, Any]:
  
  # This creates a NEW dictionary containing the OLD dictionary.
  payload = {
    **snap_spec,
    "visual_feedback": { ... }
  }

  # The server then sends a message where message.payload is the `payload` variable above.
  response = await self.send_command(session_id, "create_blocks", payload)
  return response.get("payload", {})
```

When the JavaScript `createBlocks` function receives this, it gets an object like `{ "command": "create_blocks", "payload": { "scripts": [...] } }`. When it tries to access `scripts` directly on this object, it finds nothing, leading to the error.

---

### The Solution

We need to fix the Python code to extract the *correct* payload and send only that.

#### Step 1: Apply the Primary Fix (Python Server)

This is the essential fix that corrects the data structure.

**File:** `mcp_server/tools/snap_communicator.py`

```python
# REPLACE the existing create_blocks method with this corrected version.

async def create_blocks(
    self,
    session_id: str,
    snap_spec: Dict[str, Any],
    animate: bool = True
) -> Dict[str, Any]:
    """Create blocks in Snap! IDE"""

    # --- THE FIX ---
    # The snap_spec dictionary from the block_generator already contains the 'payload' key.
    # We must extract this inner payload to send it to the client.

    if "payload" not in snap_spec:
        raise ValueError("Invalid snap_spec: dictionary is missing the 'payload' key.")

    # This is the actual payload that the JavaScript `createBlocks` function expects.
    payload_to_send = snap_spec["payload"]

    # The block_generator.py already adds a visual_feedback section.
    # We can simply update the 'animate_creation' flag on it.
    if "visual_feedback" in payload_to_send:
        payload_to_send["visual_feedback"]["animate_creation"] = animate
    
    # Send the correct command name and the UNWRAPPED payload.
    response = await self.send_command(session_id, "create_blocks", payload_to_send)
    return response.get("payload", {})

```

#### Step 2: (Recommended) Add a Defensive Check (JavaScript Client)

To make your client more robust, you can add a small check to handle this specific malformed payload, just in case.

**File:** `browser_extension/snap_bridge/block_creator.js`

```javascript
// In the createBlocks method...

async createBlocks(payload) {
    if (!this.apiWrapper.isReady()) {
        throw new Error('Snap! environment is not ready.');
    }

    // --- DEFENSIVE CHECK ---
    // This handles the server sending a double-nested payload.
    let finalPayload = payload;
    if (payload && payload.payload && payload.command === 'create_blocks') {
        console.warn('⚠️ Detected double-nested payload. Unwrapping it. Please fix the server-side logic in snap_communicator.py.');
        finalPayload = payload.payload;
    }

    // Now, destructure from the corrected payload.
    const { target_sprite, scripts, visual_feedback } = finalPayload;

    // A more specific check for the error you saw.
    if (!scripts || typeof scripts[Symbol.iterator] !== 'function') {
        console.error('❌ createBlocks error: The `scripts` property in the payload is missing or not an array.', finalPayload);
        throw new Error('Invalid payload: `scripts` is not iterable.');
    }

    try {
        // ... the rest of your function logic continues here ...
        // The loop should now work correctly.
        for (const script of scripts) {
            // ...
        }

    } catch (error) {
        console.error('Block creation error:', error);
        throw error; // Re-throw the error to be caught by the bridge
    }
}
```

