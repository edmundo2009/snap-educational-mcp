// browser_extension/snap_bridge/websocket_client.js - WebSocket Client for MCP Communication

// Prevent duplicate loading
if (typeof window.WebSocketClient !== 'undefined') {
  console.log('⚠️ WebSocketClient already loaded, skipping...');
} else {

/**
 * WebSocketClient
 *
 * Handles WebSocket communication with the MCP server,
 * including connection management, message queuing, and reconnection logic.
 */

class WebSocketClient {
  constructor(url = 'ws://localhost:8765') {
    this.url = url;
    this.websocket = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // Start with 1 second
    this.messageQueue = [];
    this.messageHandlers = new Map();
    this.pendingMessages = new Map();
    this.messageId = 0;
    this.heartbeatInterval = null;
    this.heartbeatTimeout = 30000; // 30 seconds
    
    this.setupEventHandlers();
  }

  /**
   * Setup event handlers
   */
  setupEventHandlers() {
    // Handle page visibility changes
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.pauseHeartbeat();
      } else {
        this.resumeHeartbeat();
      }
    });

    // Handle page unload
    window.addEventListener('beforeunload', () => {
      this.disconnect();
    });
  }

  /**
   * Connect to WebSocket server
   */
  async connect(token) {
    try {
      // Prevent duplicate connections
      if (this.isConnected || this.websocket) {
        console.log('⚠️ Already connected or connecting, skipping connection attempt');
        return;
      }

      console.log(`🔌 Connecting to ${this.url}...`);

      this.websocket = new WebSocket(this.url);
      
      this.websocket.onopen = () => {
        console.log('✅ WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;

        // Wait a moment for the connection to be fully established
        setTimeout(() => {
          console.log('🔄 WebSocket fully ready, sending connection request...');
          // Send connection request
          this.sendConnectionRequest(token);

          // Start heartbeat
          this.startHeartbeat();

          // Process queued messages
          this.processMessageQueue();

          // Notify handlers
          this.emit('connected');
        }, 100); // Small delay to ensure connection is fully ready
      };
      
      this.websocket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('❌ Error parsing message:', error);
        }
      };
      
      this.websocket.onclose = (event) => {
        console.log('🔌 WebSocket disconnected:', event.code, event.reason);
        this.isConnected = false;
        this.stopHeartbeat();
        
        // Attempt reconnection if not intentional
        if (event.code !== 1000) {
          this.attemptReconnection();
        }
        
        this.emit('disconnected', { code: event.code, reason: event.reason });
      };
      
      this.websocket.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        this.emit('error', error);
      };
      
    } catch (error) {
      console.error('❌ Connection error:', error);
      throw error;
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    if (this.websocket) {
      this.websocket.close(1000, 'Client disconnect');
    }
    this.stopHeartbeat();
  }

  /**
   * Send connection request
   */
  sendConnectionRequest(token) {
    const message = {
      type: 'connect',
      version: '1.0.0',
      token: token,
      client_info: {
        extension_version: '0.1.0',
        browser: navigator.userAgent,
        snap_version: this.getSnapVersion(),
        timestamp: new Date().toISOString()
      }
    };

    console.log('📤 Sending connection request:', message);
    this.send(message);
  }

  /**
   * Get Snap! version
   */
  getSnapVersion() {
    try {
      return world.children[0].version || 'unknown';
    } catch (error) {
      return 'unknown';
    }
  }

  /**
   * Send message
   */
  send(message) {
    console.log('📡 Attempting to send message:', message);
    console.log('📊 Connection state:', {
      isConnected: this.isConnected,
      readyState: this.websocket?.readyState,
      OPEN: WebSocket.OPEN
    });

    if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
      console.log('✅ Sending message immediately');
      this.websocket.send(JSON.stringify(message));
    } else {
      console.log('⏳ Queueing message for later (readyState:', this.websocket?.readyState, ')');
      // Queue message for later
      this.messageQueue.push(message);
    }
  }

  /**
   * Send message with response tracking
   */
  async sendWithResponse(message, timeout = 10000) {
    return new Promise((resolve, reject) => {
      const messageId = this.generateMessageId();
      message.message_id = messageId;
      
      // Set up response handler
      const timeoutId = setTimeout(() => {
        this.pendingMessages.delete(messageId);
        reject(new Error('Message timeout'));
      }, timeout);
      
      this.pendingMessages.set(messageId, {
        resolve,
        reject,
        timeoutId
      });
      
      this.send(message);
    });
  }

  /**
   * Generate unique message ID
   */
  generateMessageId() {
    return `msg_${++this.messageId}_${Date.now()}`;
  }

  /**
   * Handle incoming message
   */
  handleMessage(message) {
    console.log('📨 Received message:', message.type);
    
    // Handle response to pending message
    if (message.message_id && this.pendingMessages.has(message.message_id)) {
      const pending = this.pendingMessages.get(message.message_id);
      clearTimeout(pending.timeoutId);
      this.pendingMessages.delete(message.message_id);
      
      if (message.status === 'success') {
        pending.resolve(message.payload);
      } else {
        pending.reject(new Error(message.error?.message || 'Request failed'));
      }
      return;
    }
    
    // Handle specific message types
    switch (message.type) {
      case 'connect_ack':
        this.handleConnectionAck(message);
        break;
      case 'connect_error':
        this.handleConnectionError(message);
        break;
      case 'ping':
        this.handlePing(message);
        break;
      case 'pong':
        this.handlePong(message);
        break;
      case 'command':
        this.handleCommand(message);
        break;
      default:
        console.warn('⚠️ Unknown message type:', message.type);
    }
    
    // Emit to registered handlers
    this.emit(message.type, message);
  }

  /**
   * Handle connection acknowledgment
   */
  handleConnectionAck(message) {
    if (message.status === 'accepted') {
      console.log('✅ Connection accepted');
      this.emit('authenticated', message);
    }
  }

  /**
   * Handle connection error
   */
  handleConnectionError(message) {
    console.error('❌ Connection rejected:', message.error);
    this.emit('authentication_failed', message.error);
  }

  /**
   * Handle ping message
   */
  handlePing(message) {
    const pong = {
      type: 'pong',
      timestamp: new Date().toISOString(),
      latency_ms: Date.now() - new Date(message.timestamp).getTime()
    };
    this.send(pong);
  }

  /**
   * Handle pong message
   */
  handlePong(message) {
    // Pong received - connection is healthy
    console.log('🏓 Pong received, connection healthy');
  }

  /**
   * Handle command message
   */
  handleCommand(message) {
    this.emit('command', message);
  }

  /**
   * Process queued messages
   */
  processMessageQueue() {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      this.send(message);
    }
  }

  /**
   * Attempt reconnection
   */
  attemptReconnection() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('❌ Max reconnection attempts reached');
      this.emit('reconnection_failed');
      return;
    }
    
    this.reconnectAttempts++;
    console.log(`🔄 Reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
    
    setTimeout(() => {
      this.connect().catch(error => {
        console.error('❌ Reconnection failed:', error);
        // Exponential backoff
        this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
        this.attemptReconnection();
      });
    }, this.reconnectDelay);
  }

  /**
   * Start heartbeat
   */
  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected) {
        this.send({
          type: 'ping',
          timestamp: new Date().toISOString()
        });
      }
    }, this.heartbeatTimeout);
  }

  /**
   * Stop heartbeat
   */
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * Pause heartbeat (when page is hidden)
   */
  pauseHeartbeat() {
    this.stopHeartbeat();
  }

  /**
   * Pause heartbeat (when page is hidden)
   */
  pauseHeartbeat() {
    this.stopHeartbeat();
  }

  /**
   * Resume heartbeat (when page is visible)
   */
  resumeHeartbeat() {
    if (this.isConnected) {
      this.startHeartbeat();
    }
  }

  /**
   * Register event handler
   */
  on(event, handler) {
    if (!this.messageHandlers.has(event)) {
      this.messageHandlers.set(event, []);
    }
    this.messageHandlers.get(event).push(handler);
  }

  /**
   * Unregister event handler
   */
  off(event, handler) {
    if (this.messageHandlers.has(event)) {
      const handlers = this.messageHandlers.get(event);
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * Emit event to handlers
   */
  emit(event, data) {
    if (this.messageHandlers.has(event)) {
      this.messageHandlers.get(event).forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error(`❌ Error in event handler for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Get connection status
   */
  getStatus() {
    return {
      connected: this.isConnected,
      reconnect_attempts: this.reconnectAttempts,
      queued_messages: this.messageQueue.length,
      pending_messages: this.pendingMessages.size
    };
  }
}

// Store reference to prevent duplicate loading
window.WebSocketClient = WebSocketClient;

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = WebSocketClient;
}

} // End of duplicate loading protection
