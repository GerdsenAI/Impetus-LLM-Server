import React, { useEffect, useState } from 'react'
import { Cpu, Zap, Thermometer, HardDrive } from 'lucide-react'
import { Socket } from 'socket.io-client'

interface HardwareMonitorProps {
  hardwareInfo: any
  socket: Socket | null
}

export const HardwareMonitor: React.FC<HardwareMonitorProps> = ({ hardwareInfo, socket }) => {
  const [hardwareStatus, setHardwareStatus] = useState<any>(null)

  useEffect(() => {
    if (!socket) return

    socket.on('hardware_status', (data) => {
      setHardwareStatus(data)
    })

    // Request initial status
    socket.emit('get_hardware_status')

    return () => {
      socket.off('hardware_status')
    }
  }, [socket])

  if (!hardwareInfo) {
    return (
      <div className="hardware-monitor">
        <h2 className="section-title">Hardware Monitor</h2>
        <div className="loading">
          <div className="loading-spinner"></div>
          <span>Detecting hardware...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="hardware-monitor">
      <h2 className="section-title">Hardware Monitor</h2>
      
      <div className="hardware-info">
        <div className="info-row">
          <Cpu className="info-icon" />
          <div className="info-content">
            <div className="info-label">Chip</div>
            <div className="info-value">{hardwareInfo.chip_type}</div>
          </div>
        </div>

        <div className="info-row">
          <Zap className="info-icon" />
          <div className="info-content">
            <div className="info-label">Cores</div>
            <div className="info-value">
              {hardwareInfo.performance_cores}P + {hardwareInfo.efficiency_cores}E
            </div>
          </div>
        </div>

        <div className="info-row">
          <HardDrive className="info-icon" />
          <div className="info-content">
            <div className="info-label">Memory</div>
            <div className="info-value">
              {hardwareInfo.available_memory_gb?.toFixed(1)} / {hardwareInfo.total_memory_gb?.toFixed(1)} GB
            </div>
          </div>
        </div>

        {hardwareStatus && (
          <div className="info-row">
            <Thermometer className="info-icon" />
            <div className="info-content">
              <div className="info-label">Thermal</div>
              <div className={`info-value thermal-${hardwareStatus.thermal?.thermal_state}`}>
                {hardwareStatus.thermal?.thermal_state || 'nominal'}
              </div>
            </div>
          </div>
        )}
      </div>

      {hardwareStatus?.cpu && (
        <div className="cpu-cores">
          <h3 className="subsection-title">CPU Usage</h3>
          <div className="cores-grid">
            {hardwareStatus.cpu.usage_per_core.map((usage: number, index: number) => (
              <div key={index} className="core-usage">
                <div className="core-label">Core {index}</div>
                <div className="core-bar">
                  <div 
                    className="core-bar-fill"
                    style={{ width: `${usage}%`, backgroundColor: getCoreColor(usage) }}
                  />
                </div>
                <div className="core-percent">{usage.toFixed(0)}%</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function getCoreColor(usage: number): string {
  if (usage > 80) return 'var(--danger-color)'
  if (usage > 60) return 'var(--warning-color)'
  return 'var(--success-color)'
}

// Add styles
const styles = `
.hardware-monitor {
  min-height: 400px;
}

.hardware-info {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: var(--background-tertiary);
  border-radius: 8px;
}

.info-icon {
  width: 24px;
  height: 24px;
  color: var(--primary-color);
}

.info-content {
  flex: 1;
}

.info-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.info-value {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--text-primary);
}

.thermal-nominal {
  color: var(--success-color);
}

.thermal-fair {
  color: var(--warning-color);
}

.thermal-serious,
.thermal-critical {
  color: var(--danger-color);
}

.cpu-cores {
  margin-top: 2rem;
}

.subsection-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: var(--text-primary);
}

.cores-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 0.75rem;
}

.core-usage {
  background: var(--background-tertiary);
  border-radius: 6px;
  padding: 0.75rem;
}

.core-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-bottom: 0.25rem;
}

.core-bar {
  height: 4px;
  background: var(--border-color);
  border-radius: 2px;
  overflow: hidden;
  margin: 0.5rem 0;
}

.core-bar-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.core-percent {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 3rem;
  color: var(--text-secondary);
}
`

if (typeof document !== 'undefined') {
  const styleSheet = document.createElement('style')
  styleSheet.textContent = styles
  document.head.appendChild(styleSheet)
}