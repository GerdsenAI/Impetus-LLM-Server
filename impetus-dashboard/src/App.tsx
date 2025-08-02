import React, { useEffect, useState } from 'react'
import { io, Socket } from 'socket.io-client'
import { HardwareMonitor } from './components/HardwareMonitor'
import { ModelManager } from './components/ModelManager'
import { PerformanceMetrics } from './components/PerformanceMetrics'
import { Header } from './components/Header'
import './App.css'

interface AppState {
  connected: boolean
  hardwareInfo: any
  metrics: any
  loadedModels: string[]
}

function App() {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [state, setState] = useState<AppState>({
    connected: false,
    hardwareInfo: null,
    metrics: null,
    loadedModels: []
  })

  useEffect(() => {
    // Connect to WebSocket
    const newSocket = io('/', {
      transports: ['websocket', 'polling']
    })

    newSocket.on('connect', () => {
      console.log('Connected to server')
      setState(prev => ({ ...prev, connected: true }))
      
      // Subscribe to updates
      newSocket.emit('subscribe', { room: 'metrics' })
      newSocket.emit('subscribe', { room: 'hardware' })
      newSocket.emit('subscribe', { room: 'models' })
    })

    newSocket.on('disconnect', () => {
      console.log('Disconnected from server')
      setState(prev => ({ ...prev, connected: false }))
    })

    newSocket.on('hardware_info', (data) => {
      setState(prev => ({ ...prev, hardwareInfo: data }))
    })

    newSocket.on('metrics_update', (data) => {
      setState(prev => ({ ...prev, metrics: data }))
    })

    newSocket.on('models_update', (data) => {
      setState(prev => ({ ...prev, loadedModels: data.loaded_models }))
    })

    newSocket.on('thermal_warning', (data) => {
      console.warn('Thermal warning:', data)
      // TODO: Show notification to user
    })

    setSocket(newSocket)

    return () => {
      newSocket.close()
    }
  }, [])

  return (
    <div className="app">
      <Header connected={state.connected} />
      
      <div className="dashboard">
        <div className="dashboard-grid">
          <div className="card">
            <HardwareMonitor 
              hardwareInfo={state.hardwareInfo}
              socket={socket}
            />
          </div>
          
          <div className="card">
            <PerformanceMetrics 
              metrics={state.metrics}
            />
          </div>
          
          <div className="card full-width">
            <ModelManager 
              loadedModels={state.loadedModels}
              socket={socket}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default App