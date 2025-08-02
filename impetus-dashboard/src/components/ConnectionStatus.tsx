import React, { useState, useEffect } from 'react';
import { Badge, Button, Space, Tooltip } from 'antd';
import { WifiOutlined, DisconnectOutlined, ReloadOutlined } from '@ant-design/icons';

interface ConnectionStatusProps {
  wsEndpoint: string;
  onReconnect?: () => void;
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ wsEndpoint, onReconnect }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [lastError, setLastError] = useState<string>('');

  useEffect(() => {
    // Check WebSocket connection status
    const checkConnection = async () => {
      try {
        const response = await fetch('/api/health/status');
        if (response.ok) {
          setIsConnected(true);
          setLastError('');
          setRetryCount(0);
        } else {
          setIsConnected(false);
          setLastError(`Server returned ${response.status}`);
        }
      } catch (error) {
        setIsConnected(false);
        setLastError(error instanceof Error ? error.message : 'Connection failed');
      }
    };

    // Initial check
    checkConnection();

    // Set up periodic checks
    const interval = setInterval(checkConnection, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleReconnect = async () => {
    setIsConnecting(true);
    setRetryCount(prev => prev + 1);
    
    try {
      if (onReconnect) {
        await onReconnect();
      }
      
      // Force a connection check
      const response = await fetch('/api/health/status');
      if (response.ok) {
        setIsConnected(true);
        setLastError('');
        setRetryCount(0);
      }
    } catch (error) {
      setLastError(error instanceof Error ? error.message : 'Reconnection failed');
    } finally {
      setIsConnecting(false);
    }
  };

  if (isConnected) {
    return (
      <Tooltip title="Connected to server">
        <Badge status="success" text="Connected" />
      </Tooltip>
    );
  }

  return (
    <Space>
      <Tooltip title={lastError || 'Not connected to server'}>
        <Badge status="error" text="Disconnected" />
      </Tooltip>
      
      <Button
        size="small"
        icon={<ReloadOutlined spin={isConnecting} />}
        onClick={handleReconnect}
        loading={isConnecting}
      >
        Reconnect
      </Button>
      
      {retryCount > 0 && (
        <span style={{ fontSize: '12px', color: '#999' }}>
          Retry #{retryCount}
        </span>
      )}
    </Space>
  );
};

export default ConnectionStatus;