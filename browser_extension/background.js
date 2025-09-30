// browser_extension/background.js - Service Worker for Snap! Educational Assistant

/**
 * Background Service Worker
 * 
 * Handles extension lifecycle, tab management, and communication
 * between content scripts and the MCP server.
 */

class SnapExtensionBackground {
    constructor() {
        this.activeConnections = new Map();
        this.mcpServerUrl = 'ws://localhost:8765';
        this.setupEventListeners();
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Extension installation/startup
        chrome.runtime.onInstalled.addListener((details) => {
            this.handleInstallation(details);
        });

        chrome.runtime.onStartup.addListener(() => {
            console.log('🚀 Snap! Educational Assistant started');
        });

        // Tab events
        chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
            this.handleTabUpdate(tabId, changeInfo, tab);
        });

        chrome.tabs.onRemoved.addListener((tabId) => {
            this.handleTabRemoved(tabId);
        });

        // Message handling
        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            this.handleMessage(message, sender, sendResponse);
            return true; // Keep message channel open for async response
        });

        // External connections (from content scripts)
        chrome.runtime.onConnect.addListener((port) => {
            this.handleConnection(port);
        });

        // Action (popup) clicks
        chrome.action.onClicked.addListener((tab) => {
            this.handleActionClick(tab);
        });
    }

    /**
     * Handle extension installation
     */
    handleInstallation(details) {
        console.log('📦 Extension installed:', details.reason);
        
        if (details.reason === 'install') {
            // First time installation
            this.showWelcomeNotification();
            this.openOptionsPage();
        } else if (details.reason === 'update') {
            // Extension updated
            console.log('🔄 Extension updated to version', chrome.runtime.getManifest().version);
        }
    }

    /**
     * Handle tab updates
     */
    handleTabUpdate(tabId, changeInfo, tab) {
        // Check if this is a Snap! page
        if (changeInfo.status === 'complete' && this.isSnapPage(tab.url)) {
            console.log('🎯 Snap! page detected:', tab.url);
            this.injectSnapBridge(tabId);
        }
    }

    /**
     * Handle tab removal
     */
    handleTabRemoved(tabId) {
        // Clean up any connections for this tab
        if (this.activeConnections.has(tabId)) {
            const connection = this.activeConnections.get(tabId);
            if (connection.websocket) {
                connection.websocket.close();
            }
            this.activeConnections.delete(tabId);
            console.log('🧹 Cleaned up connection for tab', tabId);
        }
    }

    /**
     * Handle messages from content scripts
     */
    async handleMessage(message, sender, sendResponse) {
        try {
            console.log('📨 Background received message:', message.type);

            switch (message.type) {
                case 'inject_bridge_request':
                    if (sender.tab && sender.tab.id) {
                        await this.injectSnapBridge(sender.tab.id);
                        sendResponse({ success: true });
                    } else {
                        sendResponse({ success: false, error: 'No tab information' });
                    }
                    break;

                case 'get_connection_token':
                    const token = await this.generateConnectionToken();
                    sendResponse({ success: true, token: token });
                    break;

                case 'connect_to_mcp':
                    const result = await this.connectToMCP(message.token, sender.tab.id);
                    sendResponse({ success: result.success, error: result.error });
                    break;

                case 'send_to_mcp':
                    await this.sendToMCP(message.data, sender.tab.id);
                    sendResponse({ success: true });
                    break;

                case 'get_extension_info':
                    sendResponse({
                        success: true,
                        info: {
                            version: chrome.runtime.getManifest().version,
                            id: chrome.runtime.id
                        }
                    });
                    break;

                case 'open_options':
                    this.openOptionsPage();
                    sendResponse({ success: true });
                    break;

                default:
                    console.warn('⚠️ Unknown message type:', message.type);
                    sendResponse({ success: false, error: 'Unknown message type' });
            }

        } catch (error) {
            console.error('❌ Error handling message:', error);
            sendResponse({ success: false, error: error.message });
        }
    }

    /**
     * Handle port connections
     */
    handleConnection(port) {
        console.log('🔌 Port connected:', port.name);
        
        port.onMessage.addListener((message) => {
            console.log('📨 Port message:', message);
        });

        port.onDisconnect.addListener(() => {
            console.log('🔌 Port disconnected:', port.name);
        });
    }

    /**
     * Handle action button clicks
     */
    handleActionClick(tab) {
        if (this.isSnapPage(tab.url)) {
            // Inject bridge if not already present
            this.injectSnapBridge(tab.id);
        } else {
            // Show notification to navigate to Snap!
            this.showSnapNavigationNotification();
        }
    }

    /**
     * Check if URL is a Snap! page
     */
    isSnapPage(url) {
        if (!url) return false;
        return url.includes('snap.berkeley.edu') || 
               url.includes('extensions.snap.berkeley.edu');
    }

    /**
     * Inject Snap! bridge into page
     */
    async injectSnapBridge(tabId) {
        try {
            console.log('💉 Injecting Snap! bridge into tab', tabId);

            // Inject bridge scripts in order
            const scripts = [
                'snap_bridge/visual_feedback.js',
                'snap_bridge/websocket_client.js',
                'snap_bridge/snap_api_wrapper.js',
                'snap_bridge/block_creator.js',
                'snap_bridge/bridge.js'
            ];

            for (const script of scripts) {
                await chrome.scripting.executeScript({
                    target: { tabId: tabId },
                    files: [script]
                });
            }

            console.log('✅ Snap! bridge injected successfully');

        } catch (error) {
            console.error('❌ Error injecting bridge:', error);
        }
    }

    /**
     * Generate connection token for MCP server
     */
    async generateConnectionToken() {
        // Generate a secure random token
        const array = new Uint8Array(32);
        crypto.getRandomValues(array);
        const token = Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
        
        // Store token with timestamp
        await chrome.storage.local.set({
            connectionToken: token,
            tokenTimestamp: Date.now()
        });

        return token;
    }

    /**
     * Connect to MCP server
     */
    async connectToMCP(token, tabId) {
        try {
            console.log('🔌 Connecting to MCP server for tab', tabId);

            // Create WebSocket connection
            const websocket = new WebSocket(this.mcpServerUrl);
            
            return new Promise((resolve) => {
                websocket.onopen = () => {
                    console.log('✅ Connected to MCP server');
                    
                    // Store connection
                    this.activeConnections.set(tabId, {
                        websocket: websocket,
                        token: token,
                        connected: true
                    });

                    resolve({ success: true });
                };

                websocket.onerror = (error) => {
                    console.error('❌ MCP connection error:', error);
                    resolve({ success: false, error: 'Connection failed' });
                };

                websocket.onclose = () => {
                    console.log('🔌 MCP connection closed');
                    if (this.activeConnections.has(tabId)) {
                        this.activeConnections.get(tabId).connected = false;
                    }
                };
            });

        } catch (error) {
            console.error('❌ MCP connection error:', error);
            return { success: false, error: error.message };
        }
    }

    /**
     * Send message to MCP server
     */
    async sendToMCP(data, tabId) {
        const connection = this.activeConnections.get(tabId);
        
        if (!connection || !connection.connected) {
            throw new Error('No active MCP connection');
        }

        connection.websocket.send(JSON.stringify(data));
    }

    /**
     * Show welcome notification
     */
    showWelcomeNotification() {
        chrome.notifications.create({
            type: 'basic',
            iconUrl: 'icons/icon48.png',
            title: 'Snap! Educational Assistant',
            message: 'Welcome! Navigate to Snap! to start creating programs with natural language.'
        });
    }

    /**
     * Show Snap! navigation notification
     */
    showSnapNavigationNotification() {
        chrome.notifications.create({
            type: 'basic',
            iconUrl: 'icons/icon48.png',
            title: 'Navigate to Snap!',
            message: 'Please visit snap.berkeley.edu to use the educational assistant.'
        });
    }

    /**
     * Open options page
     */
    openOptionsPage() {
        chrome.runtime.openOptionsPage();
    }

    /**
     * Get stored settings
     */
    async getSettings() {
        const result = await chrome.storage.sync.get({
            mcpServerUrl: 'ws://localhost:8765',
            autoConnect: true,
            showTutorials: true,
            animationSpeed: 'normal'
        });
        return result;
    }

    /**
     * Save settings
     */
    async saveSettings(settings) {
        await chrome.storage.sync.set(settings);
    }
}

// Initialize background service
const snapExtension = new SnapExtensionBackground();

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SnapExtensionBackground;
}
