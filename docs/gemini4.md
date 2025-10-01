

### The Solution: Injecting the Bridge into the Main World

The solution is to use the content script's privileged position to inject our bridge scripts directly into the web page. This will make them run in the same context as Snap!'s own code, giving them access to the `world` object.

#### Step 1: Update `manifest.json` for Script Access

First, you must tell Chrome that it's okay for the web page to access your extension's script files. This is a mandatory security step.

**File:** `manifest.json` (in your extension's root directory)

```json
{
  "name": "Snap! Educational Assistant",
  "version": "1.0",
  "manifest_version": 3,
  // ... other keys like "description", "permissions", "content_scripts" ...

  "web_accessible_resources": [
    {
      "resources": [
        "snap_bridge/snap_api_wrapper.js",
        "snap_bridge/visual_feedback.js",
        "snap_bridge/block_creator.js",
        "snap_bridge/websocket_client.js",
        "snap_bridge/bridge.js",
        "snap_bridge/page_world_script.js"
      ],
      "matches": ["https://snap.berkeley.edu/*"]
    }
  ]
}
```

#### Step 2: Modify the Content Script to be an "Injector"

The `content_script.js` will now have one primary job: inject the other scripts into the page.

**File:** `browser_extension/content_script.js`

```javascript
// REPLACE the entire content of content_script.js with this.

console.log('🎯 Snap! Educational Assistant content script starting...');

/**
 * Injects a script into the main page's context.
 * @param {string} filePath - The path to the script file within the extension.
 */
function injectScript(filePath) {
    try {
        const script = document.createElement('script');
        script.src = chrome.runtime.getURL(filePath);
        // Append to head or documentElement to ensure it runs
        (document.head || document.documentElement).appendChild(script);
        console.log(`💉 Injected script: ${filePath}`);
    } catch (e) {
        console.error(`❌ Failed to inject script: ${filePath}`, e);
    }
}

// These are the scripts that need to access Snap!'s 'world' object.
// The order matters: dependencies must be loaded before the scripts that use them.
const scriptsToInject = [
    'snap_bridge/snap_api_wrapper.js',
    'snap_bridge/visual_feedback.js',
    'snap_bridge/block_creator.js',
    'snap_bridge/websocket_client.js',
    'snap_bridge/bridge.js' // The main bridge should be last as it uses the others.
];

// We still need the readiness checker.
injectScript('snap_bridge/page_world_script.js');

// Inject all the necessary bridge components.
scriptsToInject.forEach(injectScript);

console.log('✅ All bridge scripts have been injected into the page.');

// The content script will now primarily act as a message bus if needed
// between the popup/background script and the injected page scripts.
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'connect_with_token') {
        console.log('📨 Relaying token to the injected bridge...');
        // Use window.postMessage to communicate safely with the page world scripts
        window.postMessage({
            type: 'FROM_CONTENT_SCRIPT',
            action: 'connect',
            token: message.token
        }, '*');
    }
});
```

#### Step 3: Modify the Bridge to Initialize on the Correct Signal

Finally, we need to change how the main `SnapBridge` starts. It should not run immediately. Instead, it must wait for the `SnapIsReadyEvent` fired by `page_world_script.js`.

**File:** `browser_extension/snap_bridge/bridge.js`

```javascript
// --- LEAVE THE ENTIRE SnapBridge CLASS DEFINITION AS IS ---
// The class logic is fine. We are only changing HOW and WHEN it gets created.


// --- DELETE OR COMMENT OUT THE OLD INITIALIZATION LOGIC AT THE BOTTOM ---
/*
if (document.readyState === 'loading') { ... } else { ... }
*/

// --- ADD THIS NEW INITIALIZATION LOGIC AT THE VERY END OF THE FILE ---

console.log('🔧 Bridge script parsed. Waiting for Snap initialization signal...');

/**
 * This function will be called when the Snap! environment is confirmed to be ready.
 */
function initializeBridge() {
    console.log('✅ SnapIsReadyEvent received. Initializing the SnapBridge.');
    
    // Use a global flag to prevent re-initialization.
    if (!window.snapBridgeInstance) {
        window.snapBridgeInstance = new SnapBridge();

        // Listen for connection requests relayed from the content script.
        window.addEventListener('message', (event) => {
            // Basic security: only accept messages from this window.
            if (event.source !== window || !event.data) {
                return;
            }

            const { type, action, token } = event.data;
            if (type === 'FROM_CONTENT_SCRIPT' && action === 'connect') {
                console.log('🔌 Bridge received connection token from content script.');
                window.snapBridgeInstance.connect(token);
            }
        });
    }
}

// Listen for the custom event fired by page_world_script.js
window.addEventListener('SnapIsReadyEvent', initializeBridge, { once: true });
```

### Why This Will Work

1.  **Correct Context:** By injecting the scripts, all the bridge code will run in the "main world," where `world` and `IDE_Morph` exist and are accessible.
2.  **Perfect Timing:** The bridge will now only attempt to initialize *after* `page_world_script.js` has confirmed that Snap!'s core classes (`IDE_Morph`) are loaded.
3.  **Robust Communication:** The `content_script.js` now serves its proper role as a secure message broker between the extension's UI (popup) and the code running inside the web page.

After you apply these changes, reload your extension and hard-refresh the Snap! page. You should see the injection logs, followed by the readiness checks finally passing and your queued commands executing successfully.