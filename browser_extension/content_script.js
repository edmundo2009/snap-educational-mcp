// Gemini Solution: This content script's sole purpose is to inject the necessary
// bridge scripts into the main web page's JavaScript context ("main world").
// This is required to bypass the isolated world security feature of Chrome
// extensions, allowing our scripts to access Snap!'s `world` and `IDE_Morph` objects.

console.log("🎯 Snap! Educational Assistant content script starting...");

/**
 * Creates a <script> tag and injects it into the page's DOM.
 * This forces the browser to load and execute the script in the main world.
 * @param {string} filePath - The path to the script file within the extension's folder.
 */
function injectScript(filePath) {
  try {
    const script = document.createElement("script");
    // chrome.runtime.getURL() converts the local extension path to a full, accessible URL.
    script.src = chrome.runtime.getURL(filePath);

    // Appending to the <head> or <html> ensures the script is executed.
    (document.head || document.documentElement).appendChild(script);
    console.log(`💉 Injected script: ${filePath}`);

    // Optional: Clean up the script tag from the DOM after it has been loaded.
    script.onload = () => {
      script.remove();
    };
  } catch (e) {
    console.error(`❌ Failed to inject script: ${filePath}`, e);
  }
}

// An array of all bridge components that need to run in the main world.
// The order is important: dependencies must be loaded before the scripts that use them.
const scriptsToInject = [
  // 1. The API Wrapper: Provides foundational access to Snap! objects. No dependencies.
  "snap_bridge/snap_api_wrapper.js",

  // 2. Visual Feedback: Helper for UI effects. Largely independent.
  "snap_bridge/visual_feedback.js",

  // 3. Block Creator: Depends on the SnapAPIWrapper.
  "snap_bridge/block_creator.js",

  // 4. WebSocket Client: Independent networking logic.
  "snap_bridge/websocket_client.js",

  // 5. Main Bridge: The orchestrator. Depends on all of the above. Must be last.
  "snap_bridge/bridge.js",
];

// --- SCRIPT INJECTION PROCESS ---

// 1. First, inject the readiness checker. This script will listen for Snap!'s
//    core objects to be loaded and then fire a custom event ('SnapIsReadyEvent').
console.log(" injecting readiness checker...");
injectScript("snap_bridge/page_world_script.js");

// 2. Inject all the bridge components. They will be loaded by the browser and
//    will wait for the 'SnapIsReadyEvent' before initializing.
console.log(" injecting bridge components...");
scriptsToInject.forEach(injectScript);

console.log("✅ All bridge scripts have been queued for injection.");

// --- MESSAGE RELAY ---
// This listener runs in the content script's isolated world. Its job is to
// receive messages from the popup/background and securely relay them to the
// injected scripts running in the main world.

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Check for the specific message from the popup to connect.
  if (message.action === "connect_with_token" && message.token) {
    console.log(
      `📨 Relaying token [${message.token.substring(
        0,
        4
      )}...] to the injected bridge...`
    );

    // Use window.postMessage to send the data across the isolated world boundary.
    // The injected bridge.js script has a listener for this specific message format.
    window.postMessage(
      {
        type: "FROM_CONTENT_SCRIPT",
        action: "connect",
        token: message.token,
      },
      "*"
    ); // '*' is acceptable here as we're on a specific, trusted page.

    // We can optionally send a response back to the popup if needed.
    if (sendResponse) {
      sendResponse({ success: true, message: "Token relayed to the page." });
    }
  }

  // Return true to indicate you might send a response asynchronously.
  return true;
});
