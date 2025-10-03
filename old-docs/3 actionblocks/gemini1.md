# Snap! Block Automation System - Debugging Document

### Summary of the Debugging Process: From Connection to Execution

Our goal has been to establish a stable connection between a Python backend (`rovodev`) and the Snap! IDE via a Chrome browser extension, allowing the server to create blocks based on natural language commands. We successfully navigated and solved a series of increasingly complex issues.

**Phase 1: The Initial Crash (`TypeError`)**

*   **Problem:** The first error was a `TypeError: Cannot read properties of undefined (reading 'currentSprite')`.
*   **Discovery:** The extension's code was executing before the Snap! IDE was fully loaded into the browser page, meaning the `ide` object it tried to access was `undefined`.
*   **Solution:** We implemented an initial "readiness check" to wait for the IDE to exist before attempting to use it.

**Phase 2: The Race Condition (`Timeout Error`)**

*   **Problem:** The readiness check began timing out. Commands from the server were arriving almost instantly after connection, but the Snap! IDE's internal components took several seconds longer to become fully interactive.
*   **Discovery:** A race condition existed between the fast WebSocket connection and the slow-loading IDE.
*   **Solution:** We implemented a **command queue** in the browser extension. The bridge would accept commands at any time but would hold them until a more robust readiness check confirmed the IDE was fully interactive, at which point it would process the queued commands.

**Phase 3: The JavaScript Context Abyss (`IDE_Morph not found`)**

*   **Problem:** The readiness check *still* failed, perpetually unable to find the core `IDE_Morph` instance, even though it was visible on the page.
*   **Discovery:** This was the critical breakthrough. Our scripts were running in the **content script's isolated world**, a secure sandbox that is prevented from accessing the page's native JavaScript variables like `world` and `IDE_Morph`.
*   **Solution:** We re-architected the extension. The `content_script.js` was transformed into a simple **injector** that injects all the bridge scripts directly into the main page's context ("main world"). This gave them the necessary access to the Snap! API.

**Phase 4: API and Data Structure Mismatches (`TypeError: is not a function/iterable`)**

*   **Problem:** With the connection stable, we encountered a series of `TypeError` messages related to specific API calls.
*   **Discovery:**
    1.  The Python server was incorrectly nesting the data payload it sent.
    2.  The client-side code was using a non-standard `.detect()` method on Snap!'s sprite list instead of the correct `.asArray().find()` pattern.
*   **Solution:** We fixed the data structure in the Python `snap_communicator.py` and corrected the API calls in the JavaScript `block_creator.js`.

---
