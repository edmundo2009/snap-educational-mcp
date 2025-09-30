// snap_bridge/bridge.js - Main Snap! Bridge for MCP Communication

/**
 * Snap! Educational Bridge
 * 
 * This is the main bridge that connects the MCP server to the Snap! IDE.
 * It handles WebSocket communication, block creation, and visual feedback.
 */

class SnapBridge {
    constructor() {
        this.websocket = null;
        this.isConnected = false;
        this.sessionId = null;
        this.messageHandlers = new Map();
        this.pendingMessages = new Map();
        this.messageId = 0;
        
        // Initialize components
        this.blockCreator = new SnapBlockCreator();
        this.apiWrapper = new SnapAPIWrapper();
        this.visualFeedback = new VisualFeedback();
        
        this.init();
    }

    /**
     * Initialize the bridge
     */
    init() {
        console.log('🚀 Initializing Snap! Educational Bridge...');
        
        // Check if we're in Snap! environment
        if (!this.isSnapEnvironment()) {
            console.error('❌ Not running in Snap! environment');
            return;
        }

        // Set up message handlers
        this.setupMessageHandlers();
        
        // Wait for Snap! to be fully loaded
        this.waitForSnapReady().then(() => {
            console.log('✅ Snap! is ready');
            this.showConnectionUI();
        });
    }

    /**
     * Check if we're running in Snap! environment
     */
    isSnapEnvironment() {
        return typeof world !== 'undefined' && 
               typeof SpriteMorph !== 'undefined' && 
               typeof IDE_Morph !== 'undefined';
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
            console.log('🔌 Connecting to MCP server...');
            
            this.websocket = new WebSocket('ws://localhost:8765');
            
            this.websocket.onopen = () => {
                console.log('✅ WebSocket connected');
                this.sendConnectionRequest(token);
            };
            
            this.websocket.onmessage = (event) => {
                this.handleMessage(JSON.parse(event.data));
            };
            
            this.websocket.onclose = () => {
                console.log('🔌 WebSocket disconnected');
                this.isConnected = false;
                this.showReconnectUI();
            };
            
            this.websocket.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
                this.showErrorUI('Connection failed. Make sure MCP server is running.');
            };
            
        } catch (error) {
            console.error('❌ Connection error:', error);
            this.showErrorUI('Failed to connect to server.');
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
        
        this.websocket.send(JSON.stringify(message));
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
            
            // Send success response
            this.sendResponse(message.message_id, 'success', result);
            
        } catch (error) {
            console.error('❌ Command error:', error);
            this.sendResponse(message.message_id, 'error', {
                code: 'COMMAND_FAILED',
                message: error.message,
                details: error.stack
            });
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
        this.websocket.send(JSON.stringify(pong));
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
        
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(response));
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
}

// Initialize bridge when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.snapBridge = new SnapBridge();
    });
} else {
    window.snapBridge = new SnapBridge();
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SnapBridge;
}
