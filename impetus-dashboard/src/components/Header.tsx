import { Activity } from 'lucide-react'
import ConnectionStatus from './ConnectionStatus'

interface HeaderProps {
  connected: boolean
  wsEndpoint?: string
}

export const Header: React.FC<HeaderProps> = ({ wsEndpoint = 'ws://localhost:8080' }) => {
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-left">
          <h1 className="header-title">
            <Activity className="header-icon" />
            Impetus LLM Server
          </h1>
          <span className="header-subtitle">Premium Apple Silicon ML Platform</span>
        </div>
        
        <div className="header-right">
          <ConnectionStatus 
            wsEndpoint={wsEndpoint}
            onReconnect={() => window.location.reload()}
          />
        </div>
      </div>
    </header>
  )
}

// Add styles
const styles = `
.header {
  background: var(--background-secondary);
  border-bottom: 1px solid var(--border-color);
  padding: 1rem 2rem;
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(10px);
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.header-title {
  font-size: 1.5rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
}

.header-icon {
  width: 24px;
  height: 24px;
  color: var(--primary-color);
}

.header-subtitle {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}
`

// Inject styles
if (typeof document !== 'undefined') {
  const styleSheet = document.createElement('style')
  styleSheet.textContent = styles
  document.head.appendChild(styleSheet)
}