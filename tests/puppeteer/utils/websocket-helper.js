/**
 * WebSocket testing utilities for IMPETUS
 */

class WebSocketHelper {
  constructor(baseUrl = 'http://localhost:8080') {
    this.baseUrl = baseUrl;
    this.wsUrl = baseUrl.replace('http://', 'ws://').replace('https://', 'wss://') + '/ws';
    this.ws = null;
    this.messages = [];
    this.isConnected = false;
    this.messageHandlers = new Map();
  }

  /**
   * Connect to WebSocket server
   */
  connect() {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.wsUrl);
        
        this.ws.onopen = () => {
          console.log('✅ WebSocket connected:', this.wsUrl);
          this.isConnected = true;
          resolve();
        };
        
        this.ws.onclose = (event) => {
          console.log('🔌 WebSocket disconnected:', event.code, event.reason);
          this.isConnected = false;
        };
        
        this.ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
          reject(error);
        };
        
        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.messages.push({
              timestamp: Date.now(),
              data: message
            });
            
            // Call registered handlers
            if (message.type && this.messageHandlers.has(message.type)) {
              const handlers = this.messageHandlers.get(message.type);
              handlers.forEach(handler => handler(message));
            }
            
            // Call general handler
            if (this.messageHandlers.has('*')) {
              const handlers = this.messageHandlers.get('*');
              handlers.forEach(handler => handler(message));
            }
          } catch (err) {
            console.error('Failed to parse WebSocket message:', err);
          }
        };
        
        // Set a timeout for connection
        setTimeout(() => {
          if (!this.isConnected) {
            reject(new Error('WebSocket connection timeout'));
          }
        }, 5000);
      } catch (err) {
        reject(err);
      }
    });
  }

  /**
   * Send a message through WebSocket
   */
  send(data) {
    if (!this.isConnected || !this.ws) {
      throw new Error('WebSocket is not connected');
    }
    
    const message = typeof data === 'string' ? data : JSON.stringify(data);
    this.ws.send(message);
  }

  /**
   * Subscribe to specific message types
   */
  subscribe(messageType, handler) {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, new Set());
    }
    this.messageHandlers.get(messageType).add(handler);
    
    // Return unsubscribe function
    return () => {
      const handlers = this.messageHandlers.get(messageType);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          this.messageHandlers.delete(messageType);
        }
      }
    };
  }

  /**
   * Wait for a specific message type
   */
  waitForMessage(messageType, timeout = 5000) {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        unsubscribe();
        reject(new Error(`Timeout waiting for message type: ${messageType}`));
      }, timeout);
      
      const unsubscribe = this.subscribe(messageType, (message) => {
        clearTimeout(timer);
        unsubscribe();
        resolve(message);
      });
    });
  }

  /**
   * Get all messages of a specific type
   */
  getMessagesByType(messageType) {
    return this.messages
      .filter(msg => msg.data.type === messageType)
      .map(msg => msg.data);
  }

  /**
   * Clear message history
   */
  clearMessages() {
    this.messages = [];
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.isConnected = false;
    }
  }

  /**
   * Test WebSocket reconnection
   */
  async testReconnection(disconnectDuration = 5000) {
    console.log('🔄 Testing WebSocket reconnection...');
    
    // Disconnect
    this.disconnect();
    console.log('📴 Disconnected WebSocket');
    
    // Wait
    await new Promise(resolve => setTimeout(resolve, disconnectDuration));
    
    // Reconnect
    try {
      await this.connect();
      console.log('✅ WebSocket reconnected successfully');
      return true;
    } catch (err) {
      console.error('❌ WebSocket reconnection failed:', err);
      return false;
    }
  }

  /**
   * Simulate model status updates
   */
  async simulateModelStatusUpdate(modelId, status, progress = null) {
    const message = {
      type: 'model_status_update',
      model_id: modelId,
      status: status,
      timestamp: Date.now()
    };
    
    if (progress !== null) {
      message.progress = progress;
    }
    
    this.send(message);
  }

  /**
   * Monitor WebSocket performance
   */
  async measureLatency(messageCount = 10) {
    const latencies = [];
    
    for (let i = 0; i < messageCount; i++) {
      const startTime = Date.now();
      const pingMessage = {
        type: 'ping',
        timestamp: startTime,
        id: i
      };
      
      // Send ping and wait for pong
      const pongPromise = this.waitForMessage('pong', 1000);
      this.send(pingMessage);
      
      try {
        await pongPromise;
        const latency = Date.now() - startTime;
        latencies.push(latency);
      } catch (err) {
        console.warn(`Ping ${i} failed:`, err.message);
      }
    }
    
    if (latencies.length > 0) {
      const avgLatency = latencies.reduce((a, b) => a + b, 0) / latencies.length;
      const minLatency = Math.min(...latencies);
      const maxLatency = Math.max(...latencies);
      
      return {
        average: Math.round(avgLatency),
        min: minLatency,
        max: maxLatency,
        samples: latencies.length
      };
    }
    
    return null;
  }

  /**
   * Test WebSocket under load
   */
  async testLoad(messagesPerSecond = 10, duration = 5000) {
    console.log(`📊 Testing WebSocket with ${messagesPerSecond} msgs/sec for ${duration}ms...`);
    
    let messagesSent = 0;
    let messagesReceived = 0;
    const errors = [];
    
    // Subscribe to all messages
    const unsubscribe = this.subscribe('*', () => {
      messagesReceived++;
    });
    
    const interval = 1000 / messagesPerSecond;
    const startTime = Date.now();
    
    const sendInterval = setInterval(() => {
      try {
        this.send({
          type: 'load_test',
          id: messagesSent,
          timestamp: Date.now()
        });
        messagesSent++;
      } catch (err) {
        errors.push(err);
      }
    }, interval);
    
    // Wait for test duration
    await new Promise(resolve => setTimeout(resolve, duration));
    
    clearInterval(sendInterval);
    unsubscribe();
    
    const actualDuration = Date.now() - startTime;
    
    return {
      sent: messagesSent,
      received: messagesReceived,
      errors: errors.length,
      duration: actualDuration,
      messagesPerSecond: (messagesSent / actualDuration) * 1000
    };
  }
}

module.exports = { WebSocketHelper };