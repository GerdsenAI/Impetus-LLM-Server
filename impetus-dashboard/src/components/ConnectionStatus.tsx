import { useState, useEffect } from 'react';
import { Wifi, WifiOff, RefreshCw } from 'lucide-react';

interface ConnectionStatusProps {
  wsEndpoint?: string;
  onReconnect?: () => void;
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ onReconnect }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [lastError, setLastError] = useState<string>('');

  useEffect(() => {
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

    checkConnection();
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
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: '#52c41a' }}>
        <Wifi size={14} /> Connected
      </span>
    );
  }

  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
      <span
        title={lastError || 'Not connected to server'}
        style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: '#ff4d4f' }}
      >
        <WifiOff size={14} /> Disconnected
      </span>

      <button
        onClick={handleReconnect}
        disabled={isConnecting}
        style={{
          display: 'inline-flex', alignItems: 'center', gap: '4px',
          padding: '2px 8px', fontSize: '12px', borderRadius: '4px',
          border: '1px solid #d9d9d9', background: '#fff', cursor: 'pointer',
        }}
      >
        <RefreshCw size={12} className={isConnecting ? 'spin' : ''} />
        Reconnect
      </button>

      {retryCount > 0 && (
        <span style={{ fontSize: '12px', color: '#999' }}>
          Retry #{retryCount}
        </span>
      )}
    </span>
  );
};

export default ConnectionStatus;
