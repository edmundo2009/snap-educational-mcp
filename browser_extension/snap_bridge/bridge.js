// snap_bridge/bridge.js - Main Snap! Bridge for MCP Communication
// Prevent duplicate loading
if (typeof window.SnapBridge !== 'undefined') {
    console.log('⚠️ SnapBridge already loaded, skipping...');
} else {

/**
 * Snap! Educational Bridge
 *
 * This is the main bridge that connects the MCP server to the Snap! IDE.
 * It handles WebSocket communication, block creation, and visual feedback.
 */

class SnapBridge {
    constructor() {
        this.websocketClient = null;
        this.isConnected = false;
        this.sessionId = null;
        this.messageHandlers = new Map();
        this.pendingMessages = new Map();
        this.messageId = 0;

        // Command queue and readiness flag
        this.isSnapFullyReady = false;
        this.commandQueue = [];

        // Initialize components
        this.apiWrapper = new SnapAPIWrapper();
        this.blockCreator = new SnapBlockCreator(this.apiWrapper);
        this.visualFeedback = new VisualFeedback();

        this.init();
    }

    /**
     * Initialize the bridge
     */
    init() {
        console.log('🚀 Initializing Snap! Educational Bridge...');

        // Wait for Snap! environment to be ready
        this.waitForSnapEnvironment().then(() => {
            console.log('✅ Snap! environment detected');

            // Set up message handlers
            this.setupMessageHandlers();

            // Start polling for true readiness
            this.pollForSnapReadiness();

            // Show the UI immediately so the user can connect in parallel
            this.showConnectionUI();

        }).catch((error) => {
            console.error('❌ Failed to detect Snap! environment:', error);
        });
    }

    // Poll for Snap readiness using the unified check
    pollForSnapReadiness() {
        const readinessInterval = setInterval(() => {
            if (this.apiWrapper.isReady()) {
                clearInterval(readinessInterval);
                console.log('✅✅ Snap! IDE is fully loaded and ready for commands.');
                this.isSnapFullyReady = true;
                this.processCommandQueue();
            } else {
                console.log('⏳ Snap! not fully ready, checking again in 200ms...');
            }
        }, 200);

        // Add a timeout to prevent infinite loops
        setTimeout(() => {
            if (!this.isSnapFullyReady) {
                clearInterval(readinessInterval);
                console.error('❌ Timed out waiting for Snap! to become fully ready.');
            }
        }, 45000); // 45-second timeout
    }

    // Process queued commands
    processCommandQueue() {
        console.log(`⚙️ Processing ${this.commandQueue.length} queued commands...`);
        while (this.commandQueue.length > 0) {
            const commandMessage = this.commandQueue.shift();
            this.executeCommand(commandMessage);
        }
    }

    // Execute a command (logic from handleCommand)
    async executeCommand(message) {
        try {
            let result;
            switch (message.command) {
                case 'create_blocks':
                    result = await this.blockCreator.createBlocks(message.payload);
                    break;
                case 'read_project':
                    result = await this.apiWrapper.readProject(message.payload);
                    break;
                case 'execute_script':
                    result = await this.apiWrapper.executeScript(message.payload);
                    break;
                case 'inspect_state':
                    result = await this.apiWrapper.inspectState(message.payload);
                    break;
                case 'delete_blocks':
                    result = await this.blockCreator.deleteBlocks(message.payload);
                    break;
                case 'create_custom_block':
                    result = await this.blockCreator.createCustomBlock(message.payload);
                    break;
                case 'highlight_blocks':
                    result = await this.visualFeedback.highlightBlocks(message.payload);
                    break;
                case 'export_project':
                    result = await this.apiWrapper.exportProject(message.payload);
                    break;
                default:
                    throw new Error(`Unknown command: ${message.command}`);
            }
            this.sendResponse(message.message_id, 'success', result);
        } catch (error) {
            console.error('❌ Command execution error:', error);
            this.sendResponse(message.message_id, 'error', {
                code: 'COMMAND_FAILED',
                message: error.message,
                details: error.stack
            });
        }
    }

    /**
     * Check if we're running in Snap! environment
     */
    isSnapEnvironment() {
        // Check for core Snap! objects
        const hasWorld = typeof world !== 'undefined';
        const hasSpriteMorph = typeof SpriteMorph !== 'undefined';
        const hasIDEMorph = typeof IDE_Morph !== 'undefined';
        const hasSnapURL = window.location.href.includes('snap.berkeley.edu');

        // More lenient check - at least one core object + correct URL
        return hasSnapURL && (hasWorld || hasSpriteMorph || hasIDEMorph);
    }

    /**
     * Wait for Snap! environment to be available
     */
    waitForSnapEnvironment() {
        return new Promise((resolve, reject) => {
            // Check if already available
            if (this.isSnapEnvironment()) {
                resolve();
                return;
            }

            console.log('⏳ Waiting for Snap! environment to load...');

            const timeout = setTimeout(() => {
                reject(new Error('Snap! environment detection timeout (30s)'));
            }, 30000);

            const checkEnvironment = () => {
                if (this.isSnapEnvironment()) {
                    clearTimeout(timeout);
                    resolve();
                } else {
                    setTimeout(checkEnvironment, 500);
                }
            };

            checkEnvironment();
        });
    }

    /**
     * Wait for Snap! to be fully loaded
     */
    async waitForSnapReady() {
        return new Promise((resolve) => {
            const checkReady = () => {
                if (world && world.children && world.children[0] && world.children[0].stage) {
                    resolve();
                } else {
                    setTimeout(checkReady, 100);
                }
            };
            checkReady();
        });
    }

    /**
     * Show connection UI to user
     */
    showConnectionUI() {
        // Create a simple connection dialog
        const dialog = document.createElement('div');
        dialog.id = 'snap-bridge-connection';
        dialog.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4CAF50;
            color: white;
            padding: 15px;
            border-radius: 8px;
            font-family: Arial, sans-serif;
            font-size: 14px;
            z-index: 10000;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            max-width: 300px;
        `;
        
        dialog.innerHTML = `
            <div style="margin-bottom: 10px;">
                <strong>🎓 Snap! Educational Assistant</strong>
            </div>
            <div style="margin-bottom: 10px;">
                Enter your connection code:
            </div>
            <input type="text" id="connection-token" placeholder="Enter code..." 
                   style="width: 100%; padding: 5px; margin-bottom: 10px; border: none; border-radius: 4px;">
            <button id="connect-btn" style="background: #45a049; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                Connect
            </button>
            <button id="close-btn" style="background: #f44336; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin-left: 5px;">
                Close
            </button>
        `;
        
        document.body.appendChild(dialog);
        
        // Add event listeners
        document.getElementById('connect-btn').onclick = () => {
            const token = document.getElementById('connection-token').value.trim();
            if (token) {
                this.connect(token);
            }
        };
        
        document.getElementById('close-btn').onclick = () => {
            dialog.remove();
        };
        
        // Focus on input
        document.getElementById('connection-token').focus();
    }

    /**
     * Connect to MCP server with token
     */
    async connect(token) {
        try {
            if (this.websocketClient && this.websocketClient.isConnected) {
                console.log('⚠️ Already connected to MCP server, skipping connection attempt');
                return;
            }

            console.log('🔌 Connecting to MCP server...');

            if (!this.websocketClient) {
                this.websocketClient = new WebSocketClient('ws://localhost:8765');

                // Set up the high-level event listeners
                this.websocketClient.on('connected', () => {
                    console.log('✅ WebSocket connected via client');
                    this.isConnected = true;
                });

                this.websocketClient.on('disconnected', (event) => {
                    console.log('🔌 WebSocket disconnected via client:', event);
                    this.isConnected = false;
                    // this.showReconnectUI(); // You can enable this later
                });

                this.websocketClient.on('error', (error) => {
                    console.error('❌ WebSocket error via client:', error);
                    // this.showErrorUI('Connection failed.'); // You can enable this later
                });

                // --- THIS IS THE CRITICAL FIX ---
                // We are now listening for the specific 'command' event.
                this.websocketClient.on('command', (commandMessage) => {
                    console.log(`BRIDGE: Received command event: '${commandMessage.command}'`);
                    this.handleCommand(commandMessage);
                });
            }

            // Now, initiate the connection
            await this.websocketClient.connect(token);

        } catch (error) {
            console.error('❌ Connection error:', error);
            // this.showErrorUI('Failed to connect to server.');
        }
    }

    /**
     * Send connection request with token
     */
    sendConnectionRequest(token) {
        const message = {
            type: 'connect',
            version: '1.0.0',
            token: token,
            client_info: {
                extension_version: '0.1.0',
                browser: navigator.userAgent,
                snap_version: this.apiWrapper.getSnapVersion(),
                timestamp: new Date().toISOString()
            }
        };

        if (this.websocketClient) {
            this.websocketClient.send(message);
        }
    }

    /**
     * Handle incoming WebSocket messages
     */
    handleMessage(message) {
        console.log('📨 Received message:', message.type);
        
        switch (message.type) {
            case 'connect_ack':
                this.handleConnectionAck(message);
                break;
            case 'connect_error':
                this.handleConnectionError(message);
                break;
            case 'command':
                this.handleCommand(message);
                break;
            case 'ping':
                this.handlePing(message);
                break;
            default:
                console.warn('⚠️ Unknown message type:', message.type);
        }
    }

    /**
     * Handle connection acknowledgment
     */
    handleConnectionAck(message) {
        if (message.status === 'accepted') {
            this.isConnected = true;
            this.sessionId = message.session_id;
            console.log('✅ Connected to MCP server');
            
            // Update UI
            this.showSuccessUI('Connected! Ready to create Snap! programs.');
            
            // Remove connection dialog
            const dialog = document.getElementById('snap-bridge-connection');
            if (dialog) {
                setTimeout(() => dialog.remove(), 2000);
            }
        }
    }

    /**
     * Handle connection error
     */
    handleConnectionError(message) {
        console.error('❌ Connection rejected:', message.error);
        this.showErrorUI(message.error.message || 'Connection failed');
    }

    /**
     * Handle incoming commands
     */
    async handleCommand(message) {
        console.log(`BRIDGE: Received command '${message.command}'. Ready state: ${this.isSnapFullyReady}`);
        if (this.isSnapFullyReady) {
            this.executeCommand(message);
        } else {
            console.log(' M queuing command until Snap! is ready.');
            this.commandQueue.push(message);
        }
    }

    /**
     * Handle ping messages
     */
    handlePing(message) {
        const pong = {
            type: 'pong',
            timestamp: new Date().toISOString(),
            latency_ms: Date.now() - new Date(message.timestamp).getTime()
        };
        if (this.websocketClient) {
            this.websocketClient.send(pong);
        }
    }

    /**
     * Send response to MCP server
     */
    sendResponse(messageId, status, payload) {
        const response = {
            message_id: messageId,
            type: 'response',
            status: status,
            timestamp: new Date().toISOString(),
            payload: payload
        };

        if (this.websocketClient && this.websocketClient.isConnected) {
            this.websocketClient.send(response);
        }
    }

    /**
     * Setup message handlers
     */
    setupMessageHandlers() {
        // Add any additional message handlers here
    }

    /**
     * Show success UI
     */
    showSuccessUI(message) {
        this.showNotification(message, '#4CAF50');
    }

    /**
     * Show error UI
     */
    showErrorUI(message) {
        this.showNotification(message, '#f44336');
    }

    /**
     * Show reconnect UI
     */
    showReconnectUI() {
        this.showNotification('Connection lost. Please reconnect.', '#ff9800');
    }

    /**
     * Show notification
     */
    showNotification(message, color) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${color};
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

    /**
     * Pause heartbeat (when page is hidden)
     */
    pauseHeartbeat() {
        if (this.websocketClient) {
            this.websocketClient.pauseHeartbeat();
        }
    }

    /**
     * Resume heartbeat (when page is visible)
     */
    resumeHeartbeat() {
        if (this.websocketClient) {
            this.websocketClient.resumeHeartbeat();
        }
    }

    /**
     * Get connection status
     */
    getConnectionStatus() {
        return {
            connected: this.websocketClient?.isConnected || false,
            session_id: this.sessionId,
            server_url: this.serverUrl
        };
    }
}

// --- LEAVE THE ENTIRE SnapBridge CLASS DEFINITION AS IS ---
// The class logic is fine. We are only changing HOW and WHEN it gets created.

// --- DELETE OR COMMENT OUT THE OLD INITIALIZATION LOGIC AT THE BOTTOM ---
// (see above)

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

// Store reference to prevent duplicate loading
window.SnapBridge = SnapBridge;

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SnapBridge;
}

} // Close the initial if-statement that checks for SnapBridge