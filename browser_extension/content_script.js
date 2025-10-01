// browser_extension/content_script.js - Content Script for Snap! Pages

/**
 * Content Script for Snap! Educational Assistant
 *
 * Runs on Snap! pages and coordinates between the page and the extension.
 * Handles bridge initialization and communication setup.
 */

// Prevent duplicate loading
if (typeof window.SnapContentScript !== 'undefined') {
    console.log('⚠️ SnapContentScript already loaded, skipping...');
} else {

class SnapContentScript {
    constructor() {
        this.bridgeInjected = false;
        this.connectionEstablished = false;
        this.messageQueue = [];
        this.init();
    }

    /**
     * Initialize content script
     */
    async init() {
        console.log('🎯 Snap! Educational Assistant content script loaded');
        
        // Wait for page to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    /**
     * Setup the content script
     */
    async setup() {
        try {
            console.log('🔄 Starting content script setup...');

            // Check if we're on a Snap! page
            if (!this.isSnapPage()) {
                console.log('⚠️ Not on a Snap! page, content script inactive');
                return;
            }

            console.log('✅ On Snap! page, setting up educational assistant');

            // Wait for Snap! to load
            console.log('⏳ Waiting for Snap! to load...');
            await this.waitForSnap();
            console.log('✅ Snap! loaded successfully');

            // Setup communication with background script
            console.log('🔧 Setting up background communication...');
            this.setupBackgroundCommunication();
            console.log('✅ Background communication setup complete');

            // Request bridge injection from background script
            console.log('📞 Requesting bridge injection...');
            this.requestBridgeInjection();
            console.log('✅ Bridge injection requested');

            // Setup page event listeners
            console.log('👂 Setting up page event listeners...');
            this.setupPageEventListeners();
            console.log('✅ Page event listeners setup complete');

            // Show ready indicator
            console.log('🎯 Showing ready indicator...');
            this.showReadyIndicator();
            console.log('✅ Ready indicator shown');

            console.log('🎉 Content script setup completed successfully!');

        } catch (error) {
            console.error('❌ Content script setup error:', error);
            throw error; // Re-throw to be caught by the promise handler
        }
    }

    /**
     * Check if current page is Snap!
     */
    isSnapPage() {
        return window.location.hostname.includes('snap.berkeley.edu') ||
               window.location.hostname.includes('extensions.snap.berkeley.edu');
    }

    /**
     * Wait for Snap! to be fully loaded
     */
    async waitForSnap() {
        return new Promise((resolve, reject) => {
            let attempts = 0;
            const maxAttempts = 20; // 10 seconds max wait

            const checkSnap = () => {
                attempts++;
                console.log(`🔍 Checking Snap! readiness (attempt ${attempts}/${maxAttempts})...`);
                console.log('  - world:', typeof world !== 'undefined');
                console.log('  - SpriteMorph:', typeof SpriteMorph !== 'undefined');
                console.log('  - IDE_Morph:', typeof IDE_Morph !== 'undefined');

                if (typeof world !== 'undefined' &&
                    typeof SpriteMorph !== 'undefined' &&
                    typeof IDE_Morph !== 'undefined' &&
                    world.children &&
                    world.children[0] &&
                    world.children[0].stage) {
                    console.log('✅ Snap! is fully ready');
                    resolve();
                } else if (attempts >= maxAttempts) {
                    console.warn('⚠️ Snap! not fully ready after timeout, proceeding anyway...');
                    resolve(); // Don't fail, just proceed
                } else {
                    setTimeout(checkSnap, 500);
                }
            };
            checkSnap();
        });
    }

    /**
     * Setup communication with background script
     */
    setupBackgroundCommunication() {
        console.log('🔧 Setting up background communication...');

        // Listen for messages from background script
        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            console.log('📨 Content script received message from popup:', message);
            this.handleBackgroundMessage(message, sender, sendResponse);
            return true; // Keep message channel open
        });

        // Setup port connection for real-time communication
        this.port = chrome.runtime.connect({ name: 'snap-content' });
        this.port.onMessage.addListener((message) => {
            this.handlePortMessage(message);
        });

        console.log('✅ Background communication setup complete');

        // Set global flag to indicate content script is ready
        window.snapContentScriptReady = true;
    }

    /**
     * Setup page event listeners
     */
    setupPageEventListeners() {
        // Listen for Snap! events
        document.addEventListener('snapProjectLoaded', () => {
            console.log('📁 Snap! project loaded');
            this.notifyProjectChange();
        });

        // Listen for custom events from bridge
        document.addEventListener('snapBridgeReady', () => {
            console.log('🌉 Snap! bridge is ready');
            this.bridgeInjected = true;
            this.processMessageQueue();
        });

        document.addEventListener('snapBridgeConnected', () => {
            console.log('🔗 Snap! bridge connected to MCP server');
            this.connectionEstablished = true;
        });

        // Listen for page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.handlePageHidden();
            } else {
                this.handlePageVisible();
            }
        });
    }

    /**
     * Handle messages from background script
     */
    async handleBackgroundMessage(message, sender, sendResponse) {
        try {
            console.log('📨 Content script received message:', message.type);

            switch (message.type || message.action) {
                case 'ping':
                    sendResponse({ success: true, ready: true, timestamp: Date.now() });
                    break;

                case 'inject_bridge':
                    await this.injectBridge();
                    sendResponse({ success: true });
                    break;

                case 'connect_bridge':
                case 'connect_with_token':
                    const token = message.token;
                    if (!token) {
                        sendResponse({ success: false, error: 'Token is required' });
                        break;
                    }

                    // Inject bridge first if not already done
                    if (!this.bridgeInjected) {
                        await this.injectBridge();
                    }

                    // Connect with token
                    const result = await this.connectBridge(token);
                    sendResponse({ success: result.success, error: result.error });
                    break;

                case 'send_command':
                    await this.sendCommandToBridge(message.command);
                    sendResponse({ success: true });
                    break;

                case 'get_page_info':
                    const info = this.getPageInfo();
                    sendResponse({ success: true, info: info });
                    break;

                default:
                    console.warn('⚠️ Unknown message type:', message.type || message.action);
                    sendResponse({ success: false, error: 'Unknown message type' });
            }

        } catch (error) {
            console.error('❌ Error handling background message:', error);
            sendResponse({ success: false, error: error.message });
        }
    }

    /**
     * Handle port messages
     */
    handlePortMessage(message) {
        console.log('📨 Port message received:', message);
        
        // Forward to bridge if available
        if (this.bridgeInjected && window.snapBridge) {
            window.snapBridge.handleMessage(message);
        } else {
            // Queue message for later
            this.messageQueue.push(message);
        }
    }

    /**
     * Request bridge injection from background script
     */
    requestBridgeInjection() {
        console.log('📞 Requesting bridge injection from background script...');

        // Send message to background script to inject bridge
        chrome.runtime.sendMessage({
            type: 'inject_bridge_request',
            tabId: null // Background script will determine the tab
        }).catch(error => {
            console.error('❌ Error requesting bridge injection:', error);
        });
    }

    /**
     * Inject bridge into page
     */
    async injectBridge() {
        if (this.bridgeInjected) {
            console.log('🌉 Bridge already injected');
            return;
        }

        try {
            console.log('💉 Waiting for Snap! bridge to be ready...');

            // Wait for bridge scripts to be injected by background script
            await this.waitForBridge();

            this.bridgeInjected = true;
            console.log('✅ Bridge injection complete');

        } catch (error) {
            console.error('❌ Bridge injection error:', error);
            throw error;
        }
    }

    /**
     * Wait for bridge to be ready
     */
    async waitForBridge() {
        return new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('Bridge injection timeout'));
            }, 10000);

            const checkBridge = () => {
                if (window.snapBridge) {
                    clearTimeout(timeout);
                    resolve();
                } else {
                    setTimeout(checkBridge, 100);
                }
            };
            checkBridge();
        });
    }

    /**
     * Connect bridge to MCP server
     */
    async connectBridge(token) {
        if (!this.bridgeInjected || !window.snapBridge) {
            return { success: false, error: 'Bridge not ready. Please refresh the page.' };
        }

        try {
            console.log('🔗 Connecting bridge to MCP server...');
            await window.snapBridge.connect(token);
            this.connectionEstablished = true;
            console.log('✅ Bridge connected');
            return { success: true };

        } catch (error) {
            console.error('❌ Bridge connection error:', error);
            return { success: false, error: error.message || 'Connection failed' };
        }
    }

    /**
     * Send command to bridge
     */
    async sendCommandToBridge(command) {
        if (!this.connectionEstablished || !window.snapBridge) {
            throw new Error('Bridge not connected');
        }

        return window.snapBridge.sendCommand(command);
    }

    /**
     * Get page information
     */
    getPageInfo() {
        const info = {
            url: window.location.href,
            title: document.title,
            snapReady: typeof world !== 'undefined',
            bridgeInjected: this.bridgeInjected,
            connectionEstablished: this.connectionEstablished
        };

        // Add Snap! specific info if available
        if (typeof world !== 'undefined' && world.children[0]) {
            const ide = world.children[0];
            info.snapInfo = {
                version: ide.version || 'unknown',
                projectName: ide.projectName || 'Untitled',
                spriteCount: ide.sprites ? ide.sprites.length() : 0,
                currentSprite: ide.currentSprite ? ide.currentSprite.name : 'none'
            };
        }

        return info;
    }

    /**
     * Process queued messages
     */
    processMessageQueue() {
        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();
            this.handlePortMessage(message);
        }
    }

    /**
     * Notify background script of project changes
     */
    notifyProjectChange() {
        chrome.runtime.sendMessage({
            type: 'project_changed',
            info: this.getPageInfo()
        });
    }

    /**
     * Handle page hidden
     */
    handlePageHidden() {
        console.log('👁️ Page hidden');
        if (window.snapBridge) {
            window.snapBridge.pauseHeartbeat();
        }
    }

    /**
     * Handle page visible
     */
    handlePageVisible() {
        console.log('👁️ Page visible');
        if (window.snapBridge) {
            window.snapBridge.resumeHeartbeat();
        }
    }

    /**
     * Show ready indicator
     */
    showReadyIndicator() {
        // Create a subtle indicator that the assistant is ready
        const indicator = document.createElement('div');
        indicator.id = 'snap-assistant-indicator';
        indicator.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            width: 12px;
            height: 12px;
            background: #4CAF50;
            border-radius: 50%;
            z-index: 10000;
            box-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
            animation: pulse 2s infinite;
        `;

        // Add pulse animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
        `;
        document.head.appendChild(style);
        document.body.appendChild(indicator);

        // Add tooltip
        indicator.title = 'Snap! Educational Assistant is ready';

        // Remove indicator after 5 seconds
        setTimeout(() => {
            if (indicator.parentNode) {
                indicator.style.animation = 'fadeOut 1s ease-out';
                setTimeout(() => {
                    if (indicator.parentNode) {
                        indicator.parentNode.removeChild(indicator);
                    }
                }, 1000);
            }
        }, 5000);

        // Add fade-out animation
        style.textContent += `
            @keyframes fadeOut {
                from { opacity: 1; }
                to { opacity: 0; }
            }
        `;
    }

    /**
     * Show error notification
     */
    showError(message) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #f44336;
            color: white;
            padding: 15px;
            border-radius: 8px;
            font-family: Arial, sans-serif;
            font-size: 14px;
            z-index: 10001;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            max-width: 300px;
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
}

// Initialize content script
console.log('🎯 Snap! Educational Assistant content script loaded');
console.log('🌐 Current URL:', window.location.href);
console.log('📄 Document ready state:', document.readyState);

const snapContentScript = new SnapContentScript();
window.SnapContentScript = SnapContentScript; // Store reference to prevent duplicate loading

// Start the content script setup
snapContentScript.setup().then(() => {
    console.log('✅ Content script setup completed successfully');
}).catch((error) => {
    console.error('❌ Content script setup failed:', error);
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SnapContentScript;
}

} // End of duplicate loading check
