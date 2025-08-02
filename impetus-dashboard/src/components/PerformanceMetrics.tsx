import React, { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { TrendingUp, Clock, Cpu, Activity } from 'lucide-react'

interface PerformanceMetricsProps {
  metrics: any
}

export const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({ metrics }) => {
  const [chartData, setChartData] = useState<any[]>([])

  useEffect(() => {
    if (!metrics) return

    // Add new data point to chart
    setChartData(prev => {
      const newData = [...prev, {
        time: new Date().toLocaleTimeString(),
        cpu: metrics.system?.cpu_percent || 0,
        memory: metrics.system?.memory_percent || 0,
        latency: metrics.application?.average_latency_ms || 0
      }]
      
      // Keep only last 20 points
      return newData.slice(-20)
    })
  }, [metrics])

  if (!metrics) {
    return (
      <div className="performance-metrics">
        <h2 className="section-title">Performance Metrics</h2>
        <div className="loading">
          <div className="loading-spinner"></div>
          <span>Waiting for metrics...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="performance-metrics">
      <h2 className="section-title">Performance Metrics</h2>
      
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-header">
            <TrendingUp className="metric-icon" />
            <span className="metric-label">Requests</span>
          </div>
          <div className="metric-value">
            {metrics.application?.requests_total || 0}
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <Activity className="metric-icon" />
            <span className="metric-label">Tokens Generated</span>
          </div>
          <div className="metric-value">
            {metrics.application?.tokens_generated || 0}
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <Clock className="metric-icon" />
            <span className="metric-label">Avg Latency</span>
          </div>
          <div className="metric-value">
            {(metrics.application?.average_latency_ms || 0).toFixed(1)}
            <span className="metric-unit">ms</span>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <Cpu className="metric-icon" />
            <span className="metric-label">CPU Usage</span>
          </div>
          <div className="metric-value">
            {(metrics.system?.cpu_percent || 0).toFixed(1)}
            <span className="metric-unit">%</span>
          </div>
        </div>
      </div>

      {chartData.length > 0 && (
        <div className="performance-chart">
          <h3 className="subsection-title">Real-time Performance</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
              <XAxis 
                dataKey="time" 
                stroke="var(--text-secondary)"
                fontSize={12}
              />
              <YAxis 
                stroke="var(--text-secondary)"
                fontSize={12}
              />
              <Tooltip 
                contentStyle={{ 
                  background: 'var(--background-secondary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px'
                }}
              />
              <Line 
                type="monotone" 
                dataKey="cpu" 
                stroke="var(--primary-color)" 
                strokeWidth={2}
                dot={false}
                name="CPU %"
              />
              <Line 
                type="monotone" 
                dataKey="memory" 
                stroke="var(--success-color)" 
                strokeWidth={2}
                dot={false}
                name="Memory %"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

// Add styles
const styles = `
.performance-metrics {
  min-height: 400px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-top: 1rem;
}

.metric-card {
  background: var(--background-tertiary);
  border-radius: 8px;
  padding: 1rem;
}

.metric-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.metric-icon {
  width: 16px;
  height: 16px;
  color: var(--primary-color);
}

.metric-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.metric-value {
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--text-primary);
}

.metric-unit {
  font-size: 1rem;
  color: var(--text-secondary);
  font-weight: 400;
  margin-left: 0.25rem;
}

.performance-chart {
  margin-top: 2rem;
}

.subsection-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: var(--text-primary);
}
`

if (typeof document !== 'undefined') {
  const styleSheet = document.createElement('style')
  styleSheet.textContent = styles
  document.head.appendChild(styleSheet)
}