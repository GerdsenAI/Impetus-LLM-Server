import { useEffect, useRef, useState, useCallback } from 'react';

export const useWebSocket = (url, options = {}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const messageHandlersRef = useRef(new Map());
  
  const {
    onOpen,
    onClose,
    onError,
    onMessage,
    reconnectInterval = 5000,
    maxReconnectAttempts = 5,
    shouldReconnect = true
  } = options;

  const reconnectAttemptsRef = useRef(0);

  // Subscribe to specific message types
  const subscribe = useCallback((messageType, handler) => {
    if (!messageHandlersRef.current.has(messageType)) {
      messageHandlersRef.current.set(messageType, new Set());
    }
    messageHandlersRef.current.get(messageType).add(handler);

    // Return unsubscribe function
    return () => {
      const handlers = messageHandlersRef.current.get(messageType);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          messageHandlersRef.current.delete(messageType);
        }
      }
    };
  }, []);

  // Send message through WebSocket
  const sendMessage = useCallback((data) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
      return true;
    }
    console.warn('WebSocket is not connected. Message not sent:', data);
    return false;
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = (event) => {
        console.log('WebSocket connected:', url);
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
        onOpen?.(event);
      };

      wsRef.current.onclose = (event) => {
        console.log('WebSocket disconnected:', url);
        setIsConnected(false);
        onClose?.(event);

        // Attempt to reconnect
        if (shouldReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current += 1;
            console.log(`Reconnecting... Attempt ${reconnectAttemptsRef.current}`);
            connect();
          }, reconnectInterval);
        }
      };

      wsRef.current.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError(event);
        onError?.(event);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          setLastMessage(message);

          // Call general message handler
          onMessage?.(message);

          // Call specific message type handlers
          if (message.type && messageHandlersRef.current.has(message.type)) {
            const handlers = messageHandlersRef.current.get(message.type);
            handlers.forEach(handler => handler(message));
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setError(err);
    }
  }, [url, onOpen, onClose, onError, onMessage, shouldReconnect, maxReconnectAttempts, reconnectInterval]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  // Setup connection on mount
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    error,
    sendMessage,
    subscribe,
    connect,
    disconnect
  };
};

// Specific hook for model management WebSocket
export const useModelWebSocket = (serverUrl = 'http://localhost:8080') => {
  const wsUrl = serverUrl.replace('http://', 'ws://').replace('https://', 'wss://') + '/ws';
  
  const [modelStatus, setModelStatus] = useState({});
  const [serverStatus, setServerStatus] = useState('unknown');

  const handleMessage = useCallback((message) => {
    switch (message.type) {
      case 'model_status':
        setModelStatus(prev => ({
          ...prev,
          [message.model_id]: message.status
        }));
        break;
      
      case 'model_loading_progress':
        setModelStatus(prev => ({
          ...prev,
          [message.model_id]: {
            status: 'loading',
            progress: message.progress
          }
        }));
        break;
      
      case 'server_status':
        setServerStatus(message.status);
        break;
      
      default:
        // Handle other message types
        break;
    }
  }, []);

  const ws = useWebSocket(wsUrl, {
    onMessage: handleMessage,
    onOpen: () => setServerStatus('connected'),
    onClose: () => setServerStatus('disconnected'),
    onError: () => setServerStatus('error')
  });

  return {
    ...ws,
    modelStatus,
    serverStatus
  };
};