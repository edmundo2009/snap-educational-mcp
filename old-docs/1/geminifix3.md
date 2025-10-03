
# 3

### The Problem: Content Script Isolation

The error `ReferenceError: IDE_Morph is not defined` is the key. This happens because of a fundamental security feature in Chrome Extensions called **"Isolated Worlds."**

*   **Page's World:** The Snap! website runs its JavaScript (`Morph`, `IDE_Morph`, `world`, etc.) in the main page's context. Its `window` object contains all of these Snap! globals.
*   **Content Script's World:** Your `content_script.js` runs in a separate, isolated context. It can see and manipulate the page's DOM (the HTML), but it **cannot** directly access the page's JavaScript variables like `window.IDE_Morph`.

My previous recommendation (`instanceof IDE_Morph`) was logically correct for code running *inside* Snap's world, but it fails in a content script because `IDE_Morph` simply doesn't exist in that scope.

### The Solution: Injecting a Script into the Page's World

To solve this, the content script must inject a tiny piece of code directly into the main page. This new script *will* have access to Snap's variables. It will act as a scout, check if Snap is ready, and then send a message back to our waiting content script.

This is the standard and correct pattern for interacting with a page's JavaScript environment from an extension.

#### Recommended Code Update for `browser_extension/content_script.js`

Replace the entire `waitForSnap` function with this new version. It performs the necessary injection.

```javascript
// In browser_extension/content_script.js

/**
 * Wait for Snap! to be fully loaded by injecting a script into the page's context.
 */
async waitForSnap() {
    return new Promise((resolve) => {
        // This is the code that will be injected into the actual webpage.
        // It runs in the "Page's World" and can access 'IDE_Morph'.
        const checkerScript = `
            const snapChecker = setInterval(() => {
                // Check for the most reliable signals of a fully loaded Snap! IDE
                const isReady = window.world && 
                                window.IDE_Morph && 
                                window.world.children[0] instanceof window.IDE_Morph &&
                                document.querySelector('canvas[is="snap-stage"]');

                if (isReady) {
                    clearInterval(snapChecker);
                    // Dispatch a custom event to signal to the content script that we're ready
                    window.dispatchEvent(new CustomEvent('SnapIsReadyEvent'));
                }
            }, 100); // Check every 100ms
        `;

        // 1. Listen for the custom event from our injected script.
        window.addEventListener('SnapIsReadyEvent', function(e) {
            console.log('✅ Snap! is ready (detected via injected script).');
            resolve();
        }, { once: true }); // Use {once: true} to automatically remove the listener after it fires.

        // 2. Create a <script> tag to hold our checker code.
        const scriptElement = document.createElement('script');
        scriptElement.textContent = checkerScript;

        // 3. Inject the script into the page's DOM (the <head> is a good place).
        (document.head || document.documentElement).appendChild(scriptElement);

        // 4. Clean up the injected script tag once it has served its purpose.
        scriptElement.remove();
        
        console.log('⏳ Waiting for Snap! to load (using injected script)...');
    });
}
```

### Why This Works

1.  **`checkerScript`**: This string contains the logic. It uses `setInterval` to poll for the existence of `window.IDE_Morph` and other ready signals. Because this code will be executed by the page itself, it has full access to the page's `window` object.
2.  **`dispatchEvent`**: Once the injected script confirms Snap is ready, it fires a custom DOM event named `SnapIsReadyEvent`. This is the signal from the page's world to the content script's world.
3.  **`addEventListener`**: Before injecting the script, our content script sets up a listener for that specific event.
4.  **Injection**: We create a `<script>` element, put our checker code inside it, and append it to the page. The browser immediately executes it.
5.  **`resolve()`**: When the content script's listener hears the `SnapIsReadyEvent`, it knows its job is done and resolves the promise, allowing the rest of the `setup` function to proceed.

### Your Next Steps

1.  **Replace the Code:** Replace the `waitForSnap` function in `browser_extension/content_script.js` with the new version above.
2.  **Reload the Extension:** Go to `chrome://extensions`, find your extension, and click the "Reload" button.
3.  **Refresh the Snap! Page:** Do a hard refresh (Ctrl+Shift+R or Cmd+Shift+R) on the Snap! tab to ensure all the new scripts are loaded.

The console should now show a clean startup sequence, the "Extension not ready" error should disappear, and you will be able to connect using the token. This was the final hurdle in the browser-side setup.


---
# 4


### The Problem: Content Security Policy (CSP)

As the error message clearly states, the Snap! website has a **Content Security Policy (CSP)**. This is a security header the website sends to your browser that says, "Only execute scripts from sources I explicitly trust."

Their policy *disallows* "inline scripts"—which is exactly what we created when we did `scriptElement.textContent = ...`. This prevents a class of attacks called cross-site scripting (XSS).

### The Solution: Use a Web Accessible Resource

The CSP *does*, however, allow scripts loaded from your extension's own files (`chrome-extension://...`). So, instead of injecting the *text* of the script, we need to:

1.  Put the script's code into its own file within your extension.
2.  Tell Chrome that this file is "web accessible."
3.  Inject a `<script>` tag that uses the `src` attribute to load that file.

This is the secure, CSP-compliant way to inject code into the page's world.

---

### Your Action Plan (3 Steps)

#### Step 1: Create a New Script File

Create a new file in your extension directory at `browser_extension/page_world_script.js`.

Place the following code inside this new file. This is the same logic as before, just in its own file.

**File: `browser_extension/page_world_script.js`**
```javascript
const snapChecker = setInterval(() => {
    // Check for the most reliable signals of a fully loaded Snap! IDE
    const isReady = window.world && 
                    window.IDE_Morph && 
                    window.world.children[0] instanceof window.IDE_Morph &&
                    document.querySelector('canvas[is="snap-stage"]');

    if (isReady) {
        clearInterval(snapChecker);
        // Dispatch a custom event to signal to the content script that we're ready
        window.dispatchEvent(new CustomEvent('SnapIsReadyEvent'));
    }
}, 100); // Check every 100ms
```

#### Step 2: Update Your `manifest.json`

You must explicitly tell Chrome that this new file is allowed to be accessed by web pages. Add the `web_accessible_resources` key to your `manifest.json`.

**File: `browser_extension/manifest.json`**
```json
{
  "manifest_version": 3,
  "name": "Snap! Educational Assistant",
  "version": "1.0",
  "description": "...",
  "permissions": [
    "scripting",
    "activeTab",
    "storage",
    "notifications"
  ],
  "content_scripts": [
    {
      "matches": ["*://snap.berkeley.edu/*", "*://extensions.snap.berkeley.edu/*"],
      "js": ["content_script.js"]
    }
  ],
  "background": {
    "service_worker": "background.js"
  },
  "action": {},
  // ... any other keys you have ...

  // ADD THIS ENTIRE SECTION
  "web_accessible_resources": [
    {
      "resources": ["page_world_script.js"],
      "matches": ["*://snap.berkeley.edu/*", "*://extensions.snap.berkeley.edu/*"]
    }
  ]
}
```
**Important:** Make sure the `matches` pattern here is the same as your `content_scripts` `matches` pattern.

#### Step 3: Modify `content_script.js` to Load the File

Now, update your `waitForSnap` function in `content_script.js` one last time. Instead of injecting text, it will now create a script tag that points to the file you just made.

**File: `browser_extension/content_script.js`**
```javascript
/**
 * Wait for Snap! to be fully loaded by injecting a script file into the page's context.
 */
async waitForSnap() {
    return new Promise((resolve) => {
        // 1. Listen for the custom event from our injected script.
        window.addEventListener('SnapIsReadyEvent', function(e) {
            console.log('✅ Snap! is ready (detected via web_accessible_resource script).');
            resolve();
        }, { once: true });

        // 2. Create a <script> tag.
        const scriptElement = document.createElement('script');

        // 3. Set its source to the web-accessible script file.
        scriptElement.src = chrome.runtime.getURL('page_world_script.js');

        // 4. Inject the script into the page's DOM.
        (document.head || document.documentElement).appendChild(scriptElement);

        // 5. Clean up the injected script tag.
        scriptElement.onload = function() {
            this.remove();
        };

        console.log('⏳ Waiting for Snap! to load (injecting checker script)...');
    });
}
```

### Summary of Next Steps

1.  **Create** `page_world_script.js` with the provided code.
2.  **Update** `manifest.json` to include the `web_accessible_resources` section.
3.  **Replace** the `waitForSnap` function in `content_script.js` with the final version above.
4.  **Reload the Extension and Refresh the Page:** This is critical. Go to `chrome://extensions`, reload your unpacked extension, and then hard-refresh the Snap! page.

You have successfully navigated a key piece of modern web security. This final change aligns your extension with best practices and should resolve the startup error for good.

---
# 5

The error message is extremely specific and tells us exactly what is wrong:

> Denying load of `chrome-extension://.../page_world_script.js`. Resources must be listed in the `web_accessible_resources` manifest key...

This error has one primary cause: **The extension was not properly reloaded after you edited the `manifest.json` file.**

Changes to `manifest.json` are fundamental. The browser only reads this file when the extension is first installed or when you explicitly click the "Reload" button on the `chrome://extensions` page. Simply refreshing the Snap! page will not work, as it will continue to use the old manifest's rules.

### The Fix: The "Hard Reload" Procedure

Let's perform a full, clean reload of the extension and the page to ensure all your latest changes are active.

**1. Go to the Extensions Page:**
   *   Open a new tab and navigate to `chrome://extensions`.

**2. Find Your Extension:**
   *   Locate your "Snap! Educational Assistant" in the list.

**3. Check for Errors (Optional but Recommended):**
   *   Look for a red "Errors" button on your extension's card. If you see one, click it. It might point to a syntax error (like a missing comma) in your `manifest.json`.

**4. The Most Important Step: Reload the Extension:**
   *   Click the circular arrow "Reload" icon on your extension's card. The extension will quickly disable and re-enable. This forces Chrome to read your updated `manifest.json`.



**5. Close the Old Snap! Tab:**
   *   Completely close the tab that has the Snap! website open. This is important to clear out any old scripts or states.

**6. Open a New Snap! Tab:**
   *   Open a brand new tab and navigate to the Snap! URL again.

**7. Test:**
   *   Open the developer console and check the logs. The "Denying load" error should now be gone, and you should see the message "✅ Snap! is ready (detected via web_accessible_resource script)."

---

### Verification Checklist

If the error persists after following those steps exactly, please double-check these two things:

**1. `manifest.json` Syntax:**
   *   Make sure you added the `web_accessible_resources` key correctly. It should look exactly like this. Pay close attention to the commas and brackets.

   ```json
   {
     "manifest_version": 3,
     "name": "Snap! Educational Assistant",
     "version": "1.0",
     // ... other keys
     "action": {},

     "web_accessible_resources": [
       {
         "resources": ["page_world_script.js"],
         "matches": ["*://snap.berkeley.edu/*", "*://extensions.snap.berkeley.edu/*"]
       }
     ]
   }
   ```
   *(Ensure there is a comma after the `"action": {}` block if there are keys after it).*

**2. File Location:**
   *   Confirm that the file `page_world_script.js` exists directly inside the `browser_extension/` folder, at the same level as `content_script.js` and `manifest.json`.

You have fixed all the complex logic. This final hurdle is just a configuration step to tell Chrome to allow your fix to run. Once you complete the "Hard Reload" procedure, it should work.s

# 6
This is the final piece of the puzzle, and it's a very subtle one specific to Manifest V3 extensions. Congratulations, you have successfully debugged your way through multiple layers of the system to find a non-obvious root cause.

The error log is the key:

> `The FetchEvent for "chrome-extension://..." resulted in a network error...`
> `sw.js:1 Uncaught (in promise) TypeError: Failed to convert value to 'Response'.`

This tells us something new and important: your **background service worker (`background.js`)** is intercepting the request.

### The Problem: The Service Worker is Blocking Its Own Resources

In Manifest V3, your `background.js` is a service worker. A common feature of service workers is to add a `fetch` event listener (`self.addEventListener('fetch', ...)`) to handle network requests, often for caching or offline capabilities.

Here's the chain of events causing the error:
1.  Your `content_script.js` correctly requests the file: `GET chrome-extension://.../page_world_script.js`.
2.  Your extension's own `background.js` service worker intercepts this `fetch` event.
3.  The logic inside your service worker's `fetch` handler is likely designed to handle standard web requests (`http`/`https`) and doesn't know how to properly handle a request for its own internal `chrome-extension://` files.
4.  It fails to process the request and returns an invalid response (or nothing at all), which causes the `TypeError` and the generic `net::ERR_FAILED`.

In short, your background script is accidentally blocking the web page from loading a script from your own extension.

### The Solution: Tell the Service Worker to Ignore Its Own Files

The fix is to add a simple "guard clause" at the very beginning of your service worker's `fetch` listener. This clause will check the protocol of the request and, if it's a `chrome-extension://` request, it will simply do nothing, allowing the browser to handle it with its default, correct behavior.

#### Recommended Code Change for `browser_extension/background.js`

Open your `background.js` file. Find the `fetch` event listener (it will look something like `self.addEventListener('fetch', event => { ... });`). Add the check at the very top of the handler.

**File: `browser_extension/background.js`**
```javascript
// It is highly likely you have a fetch listener in your service worker.
// It might be from a template or a library you are using.
// Find this listener.
self.addEventListener('fetch', event => {
    // THIS IS THE FIX:
    // Create a new URL object from the request URL
    const url = new URL(event.request.url);

    // If the request is for one of the extension's own files,
    // do not intercept it. Let the browser handle it natively.
    if (url.protocol === 'chrome-extension:') {
        return; // Exit the handler immediately
    }

    // Your existing fetch handler logic for web requests would continue here.
    // For example, it might look like this:
    // event.respondWith(
    //     caches.match(event.request)
    //         .then(response => {
    //             return response || fetch(event.request);
    //         })
    // );
});

// NOTE: If you cannot find a 'fetch' listener, then there might be a library
// included in your service worker that adds one. In that case, adding this
// code block should still work as it will be registered as another listener.
```

### Why This Works

*   By checking `url.protocol === 'chrome-extension:'`, we identify any request that is trying to access a file packaged within the extension itself.
*   The simple `return;` statement immediately stops our custom `fetch` handler from running.
*   When the handler doesn't call `event.respondWith()`, the browser falls back to its default network behavior. The browser's default behavior *knows* how to correctly load a file listed in `web_accessible_resources`, so the request succeeds.

---

### Your Final, Final Action Plan

1.  **Modify `background.js`:** Add the guard clause to the top of the `fetch` event listener in `browser_extension/background.js`.
2.  **Perform the "Hard Reload" Procedure:** This is **absolutely critical** for service workers, as they can be difficult to unregister.
    *   Go to `chrome://extensions`.
    *   Click the **"Reload"** button for your extension.
    *   Go to the Snap! website tab.
    *   **Close the tab completely.**
    *   **Open a new tab** and navigate to Snap!.
    *   Check the console.

You have done an amazing job of systematically eliminating every variable. This is the last and most subtle configuration issue. Once you tell the service worker to ignore its own files, the entire chain will connect successfully.

# 7

# 8
This is the final, subtle race condition. Your analysis is perfect, and we are extremely close. The console logs tell the complete story.

**You have correctly identified the core issue:** The `waitForSnap` promise is never resolving.

Let's break down the evidence:
1.  **The Log:** `⏳ Waiting for Snap! to load (injecting checker script)...` appears, but the success message `✅ Snap! is ready...` **never does**.
2.  **The Consequence:** Because the `await this.waitForSnap()` line in your `setup()` function never completes, the rest of the content script's initialization (like setting up message listeners for the popup) never runs.
3.  **The Symptom:** When you click the popup, it sends a message to the content script. Since the content script's setup is stalled, it can't respond, and the popup correctly tells you, "Extension not ready."

### The Root Cause: A Too-Strict Readiness Check

The problem is that the readiness check inside `page_world_script.js` is too strict. It requires all four conditions to be true at the exact same moment:

```javascript
const isReady = window.world && 
                window.IDE_Morph && 
                window.world.children[0] instanceof window.IDE_Morph &&
                document.querySelector('canvas[is="snap-stage"]');
                
```

It's very likely that Snap! initializes these things in a slightly staggered order. Our script checks, finds one is missing, and waits... but the duplicate script injection issue you already solved shows that the page is complex. Let's simplify and make the check more resilient.

The single most reliable indicator that the Snap! JavaScript environment is ready is the existence of the main `IDE_Morph` object on the global `window`. Once that exists, everything else is guaranteed to follow shortly after.

### The Solution: Simplify and Fortify the Scripts

We will make two final adjustments: one to the injected script to simplify its check, and one to the content script to make its initialization logic even more robust.

#### Step 1: Make the Injected Script (`page_world_script.js`) More Resilient

This new version uses a simpler, more reliable check and adds a timeout as a safety measure to prevent it from running forever.

**File: `browser_extension/snap_bridge/page_world_script.js`**
```javascript
// Use a global flag to ensure this logic only runs once.
if (!window.snapIsReadyChecker) {
    window.snapIsReadyChecker = true;

    let attempts = 0;
    const maxAttempts = 200; // 20 seconds max wait

    const checkerInterval = setInterval(() => {
        attempts++;
        // The most crucial object is IDE_Morph. If it exists, Snap's JS is loaded.
        if (window.IDE_Morph) {
            console.log('PAGE_WORLD_SCRIPT: Snap environment ready! Firing event.');
            clearInterval(checkerInterval);
            window.dispatchEvent(new CustomEvent('SnapIsReadyEvent'));
        } else if (attempts > maxAttempts) {
            console.error('PAGE_WORLD_SCRIPT: Timed out waiting for Snap environment.');
            clearInterval(checkerInterval);
        }
    }, 100);
}
```

#### Step 2: Finalize the Content Script (`content_script.js`)

This version ensures the `setup` logic is clean and that the promise from `waitForSnap` is correctly handled before the script considers itself "ready."

**File: `browser_extension/content_script.js`**
```javascript
// Main guard to prevent the script from running multiple times on the same page
if (window.hasSnapContentScriptInitialized) {
    console.warn("⚠️ SnapContentScript is already initialized. Skipping duplicate execution.");
} else {
    window.hasSnapContentScriptInitialized = true;

    class SnapContentScript {
        constructor() {
            this.isReady = false; // Flag to track if setup is complete
            // This 'init' pattern ensures setup only runs after the DOM is ready.
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.init());
            } else {
                this.init();
            }
        }

        async init() {
            console.log('🎯 Snap! Educational Assistant content script starting...');
            
            // Check if we are on a Snap! page before proceeding
            if (!this.isSnapPage()) {
                console.log('
I am not on a Snap! page. Content script inactive.');
                return;
            }
            
            try {
                console.log('✅ On Snap! page, beginning setup...');
                await this.waitForSnap();
                
                // At this point, Snap! is ready. Now we can inject the main bridge.
                // NOTE: This assumes your background.js is injecting the bridge scripts.
                // If not, you would inject them here.
                
                console.log('✅ Setup complete. Content script is now ready.');
                this.isReady = true;
                
                // Example of how to listen for popup messages
                chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
                    if (message.type === 'GET_STATUS') {
                        sendResponse({ success: true, isReady: this.isReady });
                    }
                    // Add other message handlers here
                    return true;
                });

            } catch (error) {
                console.error('❌ Content script setup failed:', error);
                this.isReady = false;
            }
        }

        isSnapPage() {
            return window.location.hostname.includes('snap.berkeley.edu');
        }

        async waitForSnap() {
            console.log('⏳ Waiting for Snap! environment to be ready...');
            return new Promise((resolve, reject) => {
                // Set a timeout for the entire process
                const timeout = setTimeout(() => {
                    reject(new Error('Timed out after 20 seconds waiting for Snap!'));
                }, 20000);

                // Listen for the success event from our injected script
                window.addEventListener('SnapIsReadyEvent', () => {
                    clearTimeout(timeout); // Success, clear the timeout
                    resolve();
                }, { once: true });

                // Inject the checker script into the page's world
                const scriptElement = document.createElement('script');
                scriptElement.src = chrome.runtime.getURL('snap_bridge/page_world_script.js');
                (document.head || document.documentElement).appendChild(scriptElement);
                scriptElement.onload = () => scriptElement.remove();
            });
        }
    }

    // Instantiate the class to start the process
    new SnapContentScript();
}
```

### Final Action Plan

1.  **Replace `page_world_script.js`:** Use the new, more resilient version from Step 1.
2.  **Replace `content_script.js`:** Use the final, robust version from Step 2.
3.  **Perform the Hard Reload Procedure:**
    *   Go to `chrome://extensions`.
    *   Click **Reload** on your extension.
    *   Go to the Snap! page and **Hard Refresh** (`Ctrl+Shift+R`).

**Expected Console Output:**
You should now see a clean sequence in the console:
> 🎯 Snap! Educational Assistant content script starting...
> ✅ On Snap! page, beginning setup...
> ⏳ Waiting for Snap! environment to be ready...
> PAGE_WORLD_SCRIPT: Snap environment ready! Firing event.
> ✅ Setup complete. Content script is now ready.

After this, the popup will no longer show the "Extension not ready" message, and you will be able to enter the token to establish the final connection.